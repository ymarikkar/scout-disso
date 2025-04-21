# ScoutScheduler/gui/scheduler.py

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from backend.data_management import (
    load_badges,
    load_term_dates,      # ← your alias for holidays
    load_sessions,
    save_sessions
)
from backend.scheduler_logic import generate_schedule
from backend.data_models import Preferences
from gui.chatbot import launch_chatbot

def launch_scheduler():
    root = tk.Tk()
    root.title("Scout Scheduler")
    root.geometry("800x600")

    tk.Label(root, text="Welcome to Scout Scheduler", font=("Helvetica", 18, "bold"))\
      .pack(pady=20)

    tk.Button(root, text="Open Scheduler", width=20,
              command=lambda: show_scheduler_window(root))\
      .pack(pady=10)

    tk.Button(root, text="Badge Tracker", width=20,
              command=lambda: messagebox.showinfo("Info", "Badge Tracker coming soon"))\
      .pack(pady=10)

    tk.Button(root, text="Ask the AI", width=20,
              command=launch_chatbot)\
      .pack(pady=10)

    tk.Button(root, text="Exit", width=20,
              command=root.quit)\
      .pack(pady=10)

    root.mainloop()


def show_scheduler_window(parent_root):
    window = tk.Toplevel(parent_root)
    window.title("Session Scheduler")
    window.geometry("700x600")

    tk.Label(window, text="Session Scheduler", font=("Helvetica", 16, "bold"))\
      .pack(pady=10)

    frame = tk.Frame(window)
    frame.pack(pady=10)

    # Date dropdowns
    tk.Label(frame, text="Date (DD-MM-YYYY):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    day_var = tk.StringVar();   days = [f"{d:02d}" for d in range(1,32)]
    month_var = tk.StringVar(); months = [f"{m:02d}" for m in range(1,13)]
    year_var = tk.StringVar();  years = [str(y) for y in range(2025,2031)]
    ttk.Combobox(frame, textvariable=day_var, values=days, width=4, state="readonly") \
        .grid(row=0, column=1, sticky="w")
    ttk.Combobox(frame, textvariable=month_var, values=months, width=4, state="readonly") \
        .grid(row=0, column=2)
    ttk.Combobox(frame, textvariable=year_var, values=years, width=6, state="readonly") \
        .grid(row=0, column=3)
    day_var.set(days[0]); month_var.set(months[0]); year_var.set(years[0])

    # Time and title
    tk.Label(frame, text="Time (HH:MM):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    time_entry = tk.Entry(frame); time_entry.grid(row=1, column=1, columnspan=3, sticky="we", padx=5)
    tk.Label(frame, text="Session Title:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    title_entry = tk.Entry(frame); title_entry.grid(row=2, column=1, columnspan=3, sticky="we", padx=5)

    # Session list
    session_list = tk.Listbox(window, width=80, height=12)
    session_list.pack(pady=20)
    for sess in load_sessions():
        session_list.insert(tk.END, sess)

    # Button bar
    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)

    def add_session():
        date = f"{day_var.get()}-{month_var.get()}-{year_var.get()}"
        time = time_entry.get().strip()
        title = title_entry.get().strip()
        if not (date and time and title):
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return
        entry = f"{date} {time} – {title}"
        session_list.insert(tk.END, entry)
        save_sessions(session_list.get(0, tk.END))
        time_entry.delete(0, tk.END); title_entry.delete(0, tk.END)

    def delete_session():
        sel = session_list.curselection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a session to delete.")
            return
        session_list.delete(sel[0])
        save_sessions(session_list.get(0, tk.END))

    def suggest_sessions():
        # load everything
        badges        = load_badges()
        holidays      = load_term_dates()      # term dates
        existing      = list(load_sessions())
        prefs         = Preferences()          # you’ll want to fill this from UI later
        # generate
        suggestions   = generate_schedule(
            badges=badges,
            existing_sessions=existing,
            term_dates=holidays,
            holidays=set(),
            availability=None,
            preferences=prefs
        )
        # show them
        session_list.delete(0, tk.END)
        for s in suggestions:
            session_list.insert(tk.END, str(s))
        save_sessions(session_list.get(0, tk.END))

    # place your buttons
    tk.Button(button_frame, text="Add Session",      command=add_session).grid(row=0, column=0, padx=5)
    tk.Button(button_frame, text="Delete Selected",  command=delete_session).grid(row=0, column=1, padx=5)
    tk.Button(button_frame, text="Suggest Sessions", command=suggest_sessions).grid(row=0, column=2, padx=5)

    window.mainloop()
