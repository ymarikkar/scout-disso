import tkinter as tk
from ScoutScheduler.backend.ai_integration import get_ai_suggestions
from ScoutScheduler.gui.chatbot       import launch_chatbot
from ScoutScheduler.gui.scheduler     import launch_scheduler
from ScoutScheduler.gui.badge_tracker import launch_badge_tracker


def launch_chatbot():
    window = tk.Toplevel()
    window.title("AI Session Assistant")
    window.geometry("600x500")

    # Chat display area
    chat_display = tk.Text(window, height=20, width=70, state="disabled", wrap="word")
    chat_display.pack(pady=10)

    # Input area
    input_frame = tk.Frame(window)
    input_frame.pack(pady=10)

    user_input = tk.Entry(input_frame, width=50)
    user_input.grid(row=0, column=0, padx=5)

    def send_message():
        user_msg = user_input.get().strip()
        if not user_msg:
            return

        # Display user's message
        chat_display.config(state="normal")
        chat_display.insert(tk.END, f"You: {user_msg}\n")
        chat_display.config(state="disabled")

        user_input.delete(0, tk.END)
        window.update()

        # Get AI reply
        ai_response = get_ai_suggestions(user_msg)

        # Display AI response
        chat_display.config(state="normal")
        chat_display.insert(tk.END, f"AI: {ai_response}\n\n")
        chat_display.config(state="disabled")
        chat_display.see(tk.END)

    send_btn = tk.Button(input_frame, text="Send", command=send_message)
    send_btn.grid(row=0, column=1)

    user_input.bind("<Return>", lambda event: send_message())
