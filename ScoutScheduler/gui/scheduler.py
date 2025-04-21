import tkinter as tk
from tkinter import messagebox

# we import backend scheduling logic here
from ScoutScheduler.backend.scheduler_logic import generate_schedule
from ScoutScheduler.backend.data_management import load_sessions, save_sessions

def launch_scheduler():
    # Main scheduler window
    root = tk.Tk()
    root.title("Scout Scheduler")
    root.geometry("800x600")

    # Heading
    heading = tk.Label(root, text="Welcome to Scout Scheduler", font=("Helvetica", 18, "bold"))
    heading.pack(pady=20)

    # Button frame (so button_frame exists before we add buttons to it)
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    # Open sessions scheduler
    open_sched_btn = tk.Button(
        button_frame, text="Open Scheduler", width=20,
        command=lambda: show_scheduler_window(root)
    )
    open_sched_btn.grid(row=0, column=0, padx=5)

    # Badge tracker (import inside handler to avoid circular)
    def open_badge_tracker():
        from ScoutScheduler.gui.badge_tracker import launch_badge_tracker
        launch_badge_tracker(root)
    badge_tracker_btn = tk.Button(
        button_frame, text="Badge Tracker", width=20,
        command=open_badge_tracker
    )
    badge_tracker_btn.grid(row=0, column=1, padx=5)

    # Chatbot
    def open_chatbot():
        from ScoutScheduler.gui.chatbot import launch_chatbot
        launch_chatbot(root)
    chatbot_btn = tk.Button(
        button_frame, text="Ask the AI", width=20,
        command=open_chatbot
    )
    chatbot_btn.grid(row=0, column=2, padx=5)

    # Suggest sessions
    suggest_btn = tk.Button(
        button_frame, text="Suggest Sessions", width=20,
        command=lambda: suggest_sessions(session_list)
    )
    suggest_btn.grid(row=0, column=3, padx=5)

    # Exit
    exit_btn = tk.Button(
        button_frame, text="Exit", width=20,
        command=root.quit
    )
    exit_btn.grid(row=0, column=4, padx=5)

    # Finally, start the main loop
    root.mainloop()


def show_scheduler_window(parent_root):
    window = tk.Toplevel(parent_root)
    window.title("Session Scheduler")
    window.geometry("600x500")

    # Title
    heading = tk.Label(window, text="Session Scheduler", font=("Helvetica", 16, "bold"))
    heading.pack(pady=10)

    # Input frame
    frame = tk.Frame(window)
    frame.pack(pady=10)

    # Date entry
    tk.Label(frame, text="Date (DD-MM-YYYY):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    date_entry = tk.Entry(frame)
    date_entry.grid(row=0, column=1, padx=5)

    # Time entry
    tk.Label(frame, text="Time (HH:MM):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    time_entry = tk.Entry(frame)
    time_entry.grid(row=1, column=1, padx=5)

    # Title entry
    tk.Label(frame, text="Session Title:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    title_entry = tk.Entry(frame)
    title_entry.grid(row=2, column=1, padx=5)

    # Session list
    session_list = tk.Listbox(window, width=70, height=10)
    session_list.pack(pady=20)

    # Load existing sessions
    for sess in load_sessions():
        session_list.insert(tk.END, sess)

    # Add session
    def add_session():
        date = date_entry.get().strip()
        time = time_entry.get().strip()
        title = title_entry.get().strip()
        if not (date and time and title):
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return
        entry = f"{date} {time} - {title}"
        session_list.insert(tk.END, entry)
        save_sessions(session_list.get(0, tk.END))
        date_entry.delete(0, tk.END)
        time_entry.delete(0, tk.END)
        title_entry.delete(0, tk.END)

    # Edit session
    def edit_session():
        try:
            idx = session_list.curselection()[0]
            text = session_list.get(idx)
            date_part, rest = text.split(" ", 1)
            time_part, title_part = rest.split(" - ", 1)
            date_entry.delete(0, tk.END); date_entry.insert(0, date_part)
            time_entry.delete(0, tk.END); time_entry.insert(0, time_part)
            title_entry.delete(0, tk.END); title_entry.insert(0, title_part)
            session_list.delete(idx)
        except IndexError:
            messagebox.showwarning("No Selection", "Please select a session to edit.")

    # Delete session
    def delete_session():
        try:
            idx = session_list.curselection()[0]
            session_list.delete(idx)
            save_sessions(session_list.get(0, tk.END))
        except IndexError:
            messagebox.showwarning("No Selection", "Please select a session to delete.")

    # Buttons under scheduler window
    btn_frame = tk.Frame(window)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Add Session", command=add_session).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Edit Selected", command=edit_session).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Delete Selected", command=delete_session).grid(row=0, column=2, padx=5)


def suggest_sessions(session_list_widget):
    """
    Calls your backend.generate_schedule(...) and displays suggestions
    based on the currently loaded badges and sessions.
    """
    # Load current sessions and badges, then generate suggestions
    sessions = list(session_list_widget.get(0, tk.END))
    suggestions = generate_schedule(sessions)

    # Show suggestions in a popup
    msg = "\n".join(f"- {s}" for s in suggestions)
    messagebox.showinfo("Session Suggestions", msg or "No suggestions available.")

