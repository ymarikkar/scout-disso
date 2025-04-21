import json, os, tkinter as tk
from tkinter import ttk

BADGE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "badge_data.json")

def launch_badge_tracker():
    win = tk.Toplevel()
    win.title("Badge Tracker")
    win.geometry("500x500")

    cols = ("Badge", "Completed?")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=20)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=220 if c == "Badge" else 100, anchor="center")
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    with open(BADGE_FILE) as f:
        badges = json.load(f)
    for name in sorted(badges):
        tree.insert("", tk.END, values=(name, ""))   # completion tracking next iteration
