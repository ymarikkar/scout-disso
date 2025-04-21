import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import datetime

from ScoutScheduler.backend.data_management import (
    load_sessions,
    save_sessions,
    load_badges,
    load_term_dates as load_holidays
)
from ScoutScheduler.backend.data_models import Preferences, Session
from ScoutScheduler.backend.scheduler_logic import generate_schedule
from ScoutScheduler.gui.chatbot import launch_chatbot

def suggest_sessions(parent_window, session_listbox):
    """
    Gather data, run the scheduling algorithm, and offer to import the
    generated sessions into the scheduler.
    """
    # 1. Load all necessary data
    badges = load_badges()             # dict[str, Badge]
    existing = list(session_listbox.get(0, tk.END))  # list[str]
    holidays = load_holidays()         # dict[str, dict[str, list[str]]]

    # 2. Flatten holiday entries into a set of date‑strings
    holiday_dates = set()
    for year_block in holidays.values():
        for term_dates in year_block.values():
            holiday_dates.update(term_dates)

    # 3. Default preferences — you can expand this or load from user settings later
    prefs = Preferences(
        max_sessions_per_week=3,
        min_days_between=1,
        avoid_holidays=True
    )

    # 4. Generate suggestions
    suggestions: list[Session] = generate_schedule(
        badges=badges,
        existing_sessions=existing,
        holiday_dates=holiday_dates,
        prefs=prefs
    )

    if not suggestions:
        messagebox.showinfo("No Suggestions", "Couldn't find any sessions to suggest.")
        return

    # 5. Display and ask to import
    preview = "\n".join(f"{s.date} {s.time} – {s.title}" for s in suggestions)
    if not messagebox.askyesno(
        "Import Suggestions",
        f"I've generated {len(suggestions)} session(s):\n\n{preview}\n\n"
        "Import these into your schedule?"
    ):
        return

    # 6. Insert into UI and save
    for s in suggestions:
        session_listbox.insert(tk.END, f"{s.date} {s.time} - {s.title}")
    all_now = session_listbox.get(0, tk.END)
    save_sessions(list(all_now))
    messagebox.showinfo("Done", f"Added {len(suggestions)} session(s).")

def launch_scheduler():
    root = tk.Tk()
    root.title("Scout Scheduler")
    root.geometry("800x600")

    # Heading
    heading = tk.Label(root, text="Welcome to Scout Scheduler",
                       font=("Helvetica", 18, "bold"))
    heading.pack(pady=20)

    # Launcher buttons
    btn_scheduler = tk.Button(root, text="Open Scheduler", width=20,
                              command=lambda: show_scheduler_window(root))
    btn_scheduler.pack(pady=10)

    btn_badge_tracker = tk.Button(root, text="Badge Tracker", width=20,
                                  command=lambda: messagebox.showinfo(
                                      "Info", "Badge Tracker coming soon"))
    btn_badge_tracker.pack(pady=10)

    btn_chatbot = tk.Button(root, text="Ask the AI", width=20,
                            command=launch_chatbot)
    btn_chatbot.pack(pady=10)

    btn_exit = tk.Button(root, text="Exit", width=20, command=root.quit)
    btn_exit.pack(pady=10)

    root.mainloop()

def show_scheduler_window(parent_root):
    window = tk.Toplevel(parent_root)
    window.title("Session Scheduler")
    window.geometry("600x500")

    # Title
    heading = tk.Label(window, text="Session Scheduler",
                       font=("Helvetica", 16, "bold"))
    heading.pack(pady=10)

    # Input frame
    frame = tk.Frame(window)
    frame.pack(pady=10)

    # Date dropdowns
    tk.Label(frame, text="Date (DD-MM-YYYY):").grid(
        row=0, column=0, sticky="e", padx=5, pady=5)
    day_var = tk.StringVar(); month_var = tk.StringVar(); year_var = tk.StringVar()
    days = [f"{d:02d}" for d in range(1, 32)]
    months = [f"{m:02d}" for m in range(1, 13)]
    years = [str(y) for y in range(datetime.datetime.now().year, 2031)]
    ttk.Combobox(frame, textvariable=day_var, values=days,
                 width=5, state="readonly").grid(
        row=0, column=1, padx=2, sticky="w")
    ttk.Combobox(frame, textvariable=month_var, values=months,
                 width=5, state="readonly").grid(
        row=0, column=1, padx=2)
    ttk.Combobox(frame, textvariable=year_var, values=years,
                 width=7, state="readonly").grid(
        row=0, column=1, padx=2, sticky="e")
    day_var.set(days[0]); month_var.set(months[0]); year_var.set(years[0])

    # Time and title
    tk.Label(frame, text="Time (HH:MM):").grid(
        row=1, column=0, sticky="e", padx=5, pady=5)
    time_entry = tk.Entry(frame); time_entry.grid(row=1, column=1, padx=5)

    tk.Label(frame, text="Session Title:").grid(
        row=2, column=0, sticky="e", padx=5, pady=5)
    title_entry = tk.Entry(frame); title_entry.grid(row=2, column=1, padx=5)

    # Session list
    session_list = tk.Listbox(window, width=70, height=10)
    session_list.pack(pady=20)
    for session in load_sessions():
        session_list.insert(tk.END, session)

    # Actions: add, edit, delete, suggest
    def add_session():
        date = f"{day_var.get()}-{month_var.get()}-{year_var.get()}"
        time = time_entry.get().strip()
        title = title_entry.get().strip()
        if not (date and time and title):
            messagebox.showwarning("Missing Info", "Fill in all fields.")
            return
        entry = f"{date} {time} - {title}"
        session_list.insert(tk.END, entry)
        save_sessions(session_list.get(0, tk.END))
        # reset fields
        day_var.set(days[0]); month_var.set(months[0]); year_var.set(years[0])
        time_entry.delete(0, tk.END); title_entry.delete(0, tk.END)

    def edit_session():
        try:
            idx = session_list.curselection()[0]
            txt = session_list.get(idx)
            d, rest = txt.split(" ", 1)
            t, ttl = rest.split(" - ", 1)
            # refill inputs
            dd, mm, yy = d.split("-")
            day_var.set(dd); month_var.set(mm); year_var.set(yy)
            time_entry.delete(0, tk.END); time_entry.insert(0, t)
            title_entry.delete(0, tk.END); title_entry.insert(0, ttl)
            session_list.delete(idx)
        except IndexError:
            messagebox.showwarning("No Selection", "Select a session to edit.")

    def delete_session():
        try:
            idx = session_list.curselection()[0]
            session_list.delete(idx)
            save_sessions(session_list.get(0, tk.END))
        except IndexError:
            messagebox.showwarning("No Selection", "Select a session to delete.")

    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Add Session",
              command=add_session).grid(row=0, column=0, padx=5)
    tk.Button(button_frame, text="Edit Selected",
              command=edit_session).grid(row=0, column=1, padx=5)
    tk.Button(button_frame, text="Delete Selected",
              command=delete_session).grid(row=0, column=2, padx=5)
    tk.Button(button_frame, text="Suggest Sessions",
              command=lambda: suggest_sessions(window, session_list)
    ).grid(row=0, column=3, padx=5)

