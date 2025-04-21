import os, json, tkinter as tk
from tkinter import ttk, messagebox

# Paths
BASE_DIR      = os.path.dirname(__file__)
BADGE_FILE    = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "badge_data.json"))
PROGRESS_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "badge_progress.json"))

def load_badges():
    with open(BADGE_FILE, encoding="utf‑8") as f:
        return json.load(f)

def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return {}
    with open(PROGRESS_FILE, encoding="utf‑8") as f:
        return json.load(f)

def save_progress(progress):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf‑8") as f:
        json.dump(progress, f, indent=2)

def launch_badge_tracker():
    win = tk.Toplevel()
    win.title("Badge Tracker")
    win.geometry("600x500")

    # Filter dropdown
    filter_var = tk.StringVar(value="All")
    filter_menu = ttk.Combobox(
        win, textvariable=filter_var,
        values=["All", "Completed", "In-progress"],
        state="readonly", width=15
    )
    filter_menu.pack(pady=5)

    # Treeview setup
    cols = ("Badge", "Status")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=20)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=350 if col=="Badge" else 100, anchor="center")
    tree.pack(fill="both", expand=True, padx=10, pady=5)

    badges   = load_badges()
    progress = load_progress()

    def refresh():
        tree.delete(*tree.get_children())
        for name in sorted(badges):
            status = progress.get(name, "")
            if filter_var.get() == "Completed" and status != "Completed":
                continue
            if filter_var.get() == "In-progress" and status != "In-progress":
                continue
            tree.insert("", tk.END, values=(name, status))

    def toggle_status():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a badge first.")
            return
        item = sel[0]
        badge, current = tree.item(item, "values")
        new_status = "Completed" if current != "Completed" else ""
        progress[badge] = new_status
        save_progress(progress)
        refresh()

    # Bind filter change
    filter_menu.bind("<<ComboboxSelected>>", lambda e: refresh())
    refresh()

    # Toggle button
    btn = tk.Button(win, text="Toggle Completed", command=toggle_status)
    btn.pack(pady=5)
