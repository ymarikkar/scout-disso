import tkinter as tk
from tkinter import messagebox, ttk
import datetime

from ScoutScheduler.backend.data_management import (
    load_sessions,
    save_sessions,
    load_badges,
    save_badges,
    load_holidays
)
from ScoutScheduler.backend.data_models import Preferences, Badge
from ScoutScheduler.backend.badge_logic import get_completed_badges  # NEW: to filter completed badges
from ScoutScheduler.gui.chatbot import launch_chatbot
from ScoutScheduler.gui.badge_tracker import launch_badge_tracker  # NEW: enable Badge Tracker window

def launch_scheduler():
    root = tk.Tk()
    root.title("Scout Scheduler")
    root.geometry("800x600")

    # Heading
    tk.Label(root, text="Welcome to Scout Scheduler", font=("Helvetica", 18, "bold")).pack(pady=20)

    # Buttons
    btn_scheduler = tk.Button(root, text="Open Scheduler", width=20, command=lambda: show_scheduler_window(root))
    btn_badge_tracker = tk.Button(root, text="Badge Tracker", width=20, command=lambda: launch_badge_tracker(root))
    btn_suggest = tk.Button(root, text="Suggest Sessions", width=20, command=lambda: suggest_sessions_dialog(root))
    btn_chatbot = tk.Button(root, text="Ask the AI", width=20, command=launch_chatbot)
    btn_exit = tk.Button(root, text="Exit", width=20, command=root.quit)

    for btn in (btn_scheduler, btn_badge_tracker, btn_suggest, btn_chatbot, btn_exit):
        btn.pack(pady=10)

    root.mainloop()

def show_scheduler_window(parent_root):
    window = tk.Toplevel(parent_root)
    window.title("Session Scheduler")
    window.geometry("700x550")

    # --- Entry Frame ---
    frame = tk.Frame(window)
    frame.pack(pady=10, fill="x")

    # Date dropdowns
    tk.Label(frame, text="Date (DD‑MM‑YYYY):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    day_var, month_var, year_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
    days = [f"{d:02d}" for d in range(1, 32)]
    months = [f"{m:02d}" for m in range(1, 13)]
    years = [str(y) for y in range(datetime.datetime.now().year, 2031)]
    ttk.Combobox(frame, values=days, textvariable=day_var, width=4, state="readonly").grid(row=0, column=1)
    ttk.Combobox(frame, values=months, textvariable=month_var, width=4, state="readonly").grid(row=0, column=2)
    ttk.Combobox(frame, values=years, textvariable=year_var, width=6, state="readonly").grid(row=0, column=3)
    day_var.set(days[0]); month_var.set(months[0]); year_var.set(years[0])

    # Time & Title entries
    tk.Label(frame, text="Time (HH:MM):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    time_entry = tk.Entry(frame, width=10); time_entry.grid(row=1, column=1, columnspan=3, sticky="w")
    tk.Label(frame, text="Session Title:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    title_entry = tk.Entry(frame, width=40); title_entry.grid(row=2, column=1, columnspan=3, sticky="w")

    # --- Session Listbox ---
    session_list = tk.Listbox(window, width=80, height=15)
    session_list.pack(pady=10, padx=10)

    # Load existing sessions into the listbox
    sessions = load_sessions()
    for entry in sessions:
        session_list.insert(tk.END, entry)

    # --- Buttons for session actions ---
    btn_frame = tk.Frame(window)
    btn_frame.pack(pady=5)
    def add_session():
        date = f"{day_var.get()}-{month_var.get()}-{year_var.get()}"
        time = time_entry.get().strip() or "18:00"
        title = title_entry.get().strip() or "New Session"
        entry = f"{date} {time} - {title}"
        sessions.append(entry)
        save_sessions(sessions)
        session_list.insert(tk.END, entry)
        messagebox.showinfo("Session Added", f"Added session on {date}.")

    def delete_session():
        sel = session_list.curselection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a session to delete.")
            return
        index = sel[0]
        session = session_list.get(index)
        sessions.remove(session)
        save_sessions(sessions)
        session_list.delete(index)
        messagebox.showinfo("Session Deleted", f"Removed session: {session}")

    tk.Button(btn_frame, text="Add Session", command=add_session).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Delete", command=delete_session).grid(row=0, column=2, padx=5)
    # (You could also hook suggest_sessions here if needed)

    return window  # Return window in case caller needs it

def suggest_sessions_dialog(parent):
    """
    Pop up a dialog to generate session suggestions and append them to the sessions list.
    """
    # Load all necessary data
    badges_data = load_badges()  # returns dict of badge_name -> URL
    existing = load_sessions()   # list of session strings
    raw_holidays = load_holidays()  # dict of term -> list of date strings

    # Prepare a set of holiday dates for quick lookup
    holidays_set = {d for dates in raw_holidays.values() for d in dates}

    # Create Badge objects list, marking completed badges
    completed_set = set(get_completed_badges())
    badges = []
    for name, url in badges_data.items():
        # Use Badge model; mark completed=True if badge name is in user's completed list
        badges.append(Badge(title=name, url=url, completed=(name in completed_set)))

    prefs = Preferences()  # default preferences (can extend if needed)

    # Call scheduling algorithm
    suggested = generate_schedule(
        badges=badges,
        existing_sessions=existing,
        holidays=holidays_set,
        preferences=prefs
    )

    # Format suggestions and save to sessions file
    formatted = []
    for s in suggested:
        try:
            # If suggestion is a Session object
            entry = f"{s.date} {s.time} - {s.title}"
        except AttributeError:
            # Fallback if it's a tuple (date, title)
            entry = f"{s[0]} - {s[1]}"
        formatted.append(entry)
    save_sessions(formatted)  # overwrite sessions with suggested plan

    # Notify user
    messagebox.showinfo("Suggestions Applied", f"{len(formatted)} sessions generated and saved.")
    # Optionally, open a fresh scheduler window to show new sessions
    win = show_scheduler_window(parent)
    for entry in formatted:
        try:
            win.children['!listbox'].insert(tk.END, entry)
        except Exception:
            pass

if __name__ == "__main__":
    launch_scheduler()
