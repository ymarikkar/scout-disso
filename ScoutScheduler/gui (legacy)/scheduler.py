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
from ScoutScheduler.backend.scheduler_logic import generate_schedule
from ScoutScheduler.backend.data_models import Preferences
from ScoutScheduler.gui.chatbot import launch_chatbot


def launch_scheduler():
    root = tk.Tk()
    root.title("Scout Scheduler")
    root.geometry("800x600")

    # Heading
    tk.Label(root, text="Welcome to Scout Scheduler",
             font=("Helvetica", 18, "bold")).pack(pady=20)

    # Buttons
    btn_scheduler    = tk.Button(root, text="Open Scheduler",
                                 width=20, command=lambda: show_scheduler_window(root))
    btn_badge_tracker= tk.Button(root, text="Badge Tracker",
                                 width=20, command=lambda: messagebox.showinfo("Info", "Badge Tracker coming soon"))
    btn_suggest      = tk.Button(root, text="Suggest Sessions",
                                 width=20, command=lambda: suggest_sessions_dialog(root))
    btn_chatbot      = tk.Button(root, text="Ask the AI",
                                 width=20, command=launch_chatbot)
    btn_exit         = tk.Button(root, text="Exit",
                                 width=20, command=root.quit)

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
    days   = [f"{d:02d}" for d in range(1, 32)]
    months = [f"{m:02d}" for m in range(1, 13)]
    years  = [str(y) for y in range(datetime.datetime.now().year, 2031)]
    ttk.Combobox(frame, values=days,   textvariable=day_var,   width=4, state="readonly").grid(row=0, column=1)
    ttk.Combobox(frame, values=months, textvariable=month_var, width=4, state="readonly").grid(row=0, column=2)
    ttk.Combobox(frame, values=years,  textvariable=year_var,  width=6, state="readonly").grid(row=0, column=3)
    day_var.set(days[0]); month_var.set(months[0]); year_var.set(years[0])

    # Time & Title entries
    tk.Label(frame, text="Time (HH:MM):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    time_entry  = tk.Entry(frame, width=10); time_entry.grid(row=1, column=1, columnspan=3, sticky="w")

    tk.Label(frame, text="Session Title:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    title_entry = tk.Entry(frame, width=40); title_entry.grid(row=2, column=1, columnspan=3, sticky="w")

    # --- Session Listbox ---
    session_list = tk.Listbox(window, width=80, height=15)
    session_list.pack(pady=10, padx=10)
    # Populate existing
    for s in load_sessions():
        session_list.insert(tk.END, s)

    # --- Add/Edit/Delete ---
    def add_session():
        date = f"{day_var.get()}-{month_var.get()}-{year_var.get()}"
        time = time_entry.get().strip()
        title = title_entry.get().strip()
        if not (date and time and title):
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return
        entry = f"{date} {time} - {title}"
        session_list.insert(tk.END, entry)
        save_sessions(session_list.get(0, tk.END))
        # clear
        time_entry.delete(0, tk.END)
        title_entry.delete(0, tk.END)

    def edit_session():
        try:
            idx = session_list.curselection()[0]
            sel = session_list.get(idx)
            d, rest = sel.split(" ", 1)
            t, ttl = rest.split(" - ", 1)
            day_var.set(d.split("-")[0]); month_var.set(d.split("-")[1]); year_var.set(d.split("-")[2])
            time_entry.delete(0, tk.END);  time_entry.insert(0, t)
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

    # Buttons row
    btn_frame = tk.Frame(window)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Add",   command=add_session).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="Edit",  command=edit_session).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="Delete",command=delete_session).grid(row=0, column=2, padx=5)
    # DONE: you could also hook suggest_sessions here if you like

    return window  # in case caller needs it


def suggest_sessions_dialog(parent):
    """
    Pop up a small dialog to show generated schedule suggestions,
    then write them into the main sessions file.
    """
    # Load all data
    badges  = load_badges()
    existing = load_sessions()
    raw_holidays = load_holidays()  # assumed dict of term→list of dates
    # flatten to a set of date strings if needed:
    holidays_set = {
        d for dates in raw_holidays.values() for d in dates
    }

    # Default preferences placeholder
    prefs = Preferences()

    # Call your scheduling algorithm
    suggested: list = generate_schedule(
        badges=badges,
        existing_sessions=existing,
        term_dates=raw_holidays,
        holidays=holidays_set,
        availability=None,
        preferences=prefs
    )

    # Format & save
    # assume each suggestion is an object or tuple with date, time, badge/title
    formatted = []
    for s in suggested:
        # if s has attributes .date, .time, .badge_name:
        try:
            entry = f"{s.date} {s.time} - {s.badge_name}"
        except AttributeError:
            # fallback if it's a (date, name) tuple
            entry = f"{s[0]} - {s[1]}"
        formatted.append(entry)

    # Overwrite sessions file
    save_sessions(formatted)

    # Inform the user
    messagebox.showinfo("Suggestions Applied",
                        f"{len(formatted)} sessions generated and saved.")

    # Optionally, reopen scheduler window so they can see them
    win = show_scheduler_window(parent)
    for e in formatted:
        # new window's list is populated from file, but just in case:
        win.children['!listbox'].insert(tk.END, e)


if __name__ == "__main__":
    launch_scheduler()
