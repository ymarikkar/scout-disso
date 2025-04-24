import tkinter as tk
from tkinter import ttk, messagebox

from ScoutScheduler.backend.badge_logic import get_all_badges, get_completed_badges, mark_badge_completed, mark_badge_incomplete

def launch_badge_tracker(parent_root):
    window = tk.Toplevel(parent_root)
    window.title("Badge Tracker")
    window.geometry("600x500")

    # Filter dropdown
    filter_var = tk.StringVar(value="All")
    filter_menu = ttk.Combobox(window, textvariable=filter_var,
                                values=["All", "Completed", "Incomplete"],
                                state="readonly", width=15)
    filter_menu.pack(pady=5)

    # Treeview setup
    cols = ("Badge", "Status")
    tree = ttk.Treeview(window, columns=cols, show="headings", height=20)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=350 if col == "Badge" else 100, anchor="center")
    tree.pack(fill="both", expand=True, padx=10, pady=5)

    # Load all badges (catalog) once
    all_badges = get_all_badges()  # list of all badge names (sorted)

    def refresh():
        """Refresh the badge list based on filter selection."""
        tree.delete(*tree.get_children())
        completed_set = set(get_completed_badges())
        for name in all_badges:
            status = "Completed" if name in completed_set else "Incomplete"
            if filter_var.get() == "Completed" and status != "Completed":
                continue
            if filter_var.get() == "Incomplete" and status != "Incomplete":
                continue
            tree.insert("", tk.END, values=(name, status))

    def toggle_status():
        """Toggle the selected badge's completion status."""
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a badge first.")
            return
        item = sel[0]
        badge, current_status = tree.item(item, "values")
        try:
            if current_status == "Completed":
                mark_badge_incomplete(badge)
            else:
                mark_badge_completed(badge)
        except Exception as e:
            messagebox.showerror("Error", f"Could not update badge status: {e}")
            return
        refresh()

    # Update list when filter changes
    filter_menu.bind("<<ComboboxSelected>>", lambda e: refresh())

    # Initial populate
    refresh()

    # Toggle status button
    btn_toggle = tk.Button(window, text="Toggle Completed", command=toggle_status)
    btn_toggle.pack(pady=5)
