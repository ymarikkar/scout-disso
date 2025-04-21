import tkinter as tk
from tkinter import messagebox
from ScoutScheduler.gui.badge_tracker import launch_badge_tracker
from ScoutScheduler.gui.chatbot import launch_chatbot


# Import from the ScoutScheduler package
from ScoutScheduler.backend.data_management import load_sessions, save_sessions
from ScoutScheduler.gui.chatbot          import launch_chatbot

from ScoutScheduler.gui.badge_tracker       import launch_badge_tracker

# At top, replace old import:
from ScoutScheduler.gui.badge_tracker import launch_badge_tracker


# Then where you define the button:
btn_badge_tracker = tk.Button(
    root, text="Badge Tracker", width=20,
    command=launch_badge_tracker
)


def launch_scheduler():
    root = tk.Tk()
    root.title("Scout Scheduler")
    root.geometry("800x600")

    # Heading
    heading = tk.Label(root, text="Welcome to Scout Scheduler", font=("Helvetica", 18, "bold"))
    heading.pack(pady=20)

    # Buttons
    btn_scheduler = tk.Button(root, text="Open Scheduler", width=20, command=lambda: show_scheduler_window(root))
    btn_scheduler.pack(pady=10)

    btn_badge_tracker = tk.Button(root, text="Badge Tracker", width=20, command=lambda: messagebox.showinfo("Info", "Badge Tracker coming soon"))
    btn_badge_tracker.pack(pady=10)

    btn_chatbot = tk.Button(root, text="Ask the AI", width=20, command=launch_chatbot)
    btn_chatbot.pack(pady=10)

    btn_exit = tk.Button(root, text="Exit", width=20, command=root.quit)
    btn_exit.pack(pady=10)

    root.mainloop()
def show_scheduler_window(parent_root):
    window = tk.Toplevel(parent_root)
    window.title("Session Scheduler")
    window.geometry("600x500")

    # Title
    heading = tk.Label(window, text="Session Scheduler", font=("Helvetica", 16, "bold"))
    heading.pack(pady=10)

    # Entry Fields
    frame = tk.Frame(window)
    frame.pack(pady=10)

        # Calendar date‑picker (now inside the window, so `frame` is defined)
    from tkcalendar import Calendar
    cal = Calendar(frame, selectmode="day", date_pattern="dd-mm-yyyy")
    cal.grid(row=0, column=2, padx=5)


    # add a Date picker
    cal = Calendar(frame, selectmode="day", date_pattern="dd-mm-yyyy")
    cal.grid(row=0, column=2, padx=5)


    from tkinter import ttk
    import datetime

    # Date label
    tk.Label(frame, text="Date (DD-MM-YYYY):").grid(row=0, column=0, sticky="e", padx=5, pady=5)

    # Dropdowns for day, month, year
    day_var = tk.StringVar()
    month_var = tk.StringVar()
    year_var = tk.StringVar()

    days = [f"{d:02d}" for d in range(1, 32)]
    months = [f"{m:02d}" for m in range(1, 13)]
    years = [str(y) for y in range(datetime.datetime.now().year, 2031)]

    day_menu = ttk.Combobox(frame, textvariable=day_var, values=days, width=5, state="readonly")
    month_menu = ttk.Combobox(frame, textvariable=month_var, values=months, width=5, state="readonly")
    year_menu = ttk.Combobox(frame, textvariable=year_var, values=years, width=7, state="readonly")

    day_menu.grid(row=0, column=1, padx=2, sticky="w")
    month_menu.grid(row=0, column=1, padx=2)
    year_menu.grid(row=0, column=1, padx=2, sticky="e")

    # Default selections
    day_var.set(days[0])
    month_var.set(months[0])
    year_var.set(years[0])

    tk.Label(frame, text="Time (HH:MM):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    time_entry = tk.Entry(frame)
    time_entry.grid(row=1, column=1, padx=5)

    tk.Label(frame, text="Session Title:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    title_entry = tk.Entry(frame)
    title_entry.grid(row=2, column=1, padx=5)

    # Session List
    session_list = tk.Listbox(window, width=70, height=10)
    session_list.pack(pady=20)
    # Load existing sessions
    existing_sessions = load_sessions()
    for session in existing_sessions:
        session_list.insert(tk.END, session)


    # Add session
    def add_session():
        date = f"{day_var.get()}-{month_var.get()}-{year_var.get()}"
        time = time_entry.get().strip()
        title = title_entry.get().strip()

        if not date or not time or not title:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return

        session_str = f"{date} {time} - {title}"
        session_list.insert(tk.END, session_str)
        # Save to file
        all_sessions = session_list.get(0, tk.END)
        save_sessions(list(all_sessions))


     

    # Edit session
    def edit_session():
        try:
            selected_index = session_list.curselection()[0]
            selected_text = session_list.get(selected_index)

            # Parse the selected session string
            date_part, time_title = selected_text.split(" ", 1)
            time_part, title_part = time_title.split(" - ", 1)

            # Remove original entry
            session_list.delete(selected_index)
        except IndexError:
            messagebox.showwarning("No Selection", "Please select a session to edit.")

    # Delete session
    def delete_session():
        try:
            selected_index = session_list.curselection()[0]
            session_list.delete(selected_index)
            # Save updated list
            all_sessions = session_list.get(0, tk.END)
            save_sessions(list(all_sessions))

        except IndexError:
            messagebox.showwarning("No Selection", "Please select a session to delete.")

    # Button frame
    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)

    add_btn = tk.Button(button_frame, text="Add Session", command=add_session)
    add_btn.grid(row=0, column=0, padx=5)

    edit_btn = tk.Button(button_frame, text="Edit Selected", command=edit_session)
    edit_btn.grid(row=0, column=1, padx=5)

    delete_btn = tk.Button(button_frame, text="Delete Selected", command=delete_session)
    delete_btn.grid(row=0, column=2, padx=5)
