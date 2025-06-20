import tkinter as tk
from tkinter import ttk, messagebox
import winsound
import json
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller sets this up
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class SessionTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Session Timer")
        self.root.geometry("400x400")
        self.root.configure(bg="#fdf6e3")

        self.sessions = []
        self.config_path = "session_settings.json"
        self.icon_path = "mintleaf.ico"

        self.current_index = 0
        self.remaining_time = 0
        self.original_time = 0
        self.timer_running = False
        self.timer_paused = False

        self.session_name_label = tk.Label(root, text="Session Timer", font=("Helvetica", 16, "bold"), bg="#fdf6e3", fg="#073642")
        self.session_name_label.pack(pady=(10, 5))

        self.timer_label = tk.Label(root, text="00:00", font=("Courier", 32, "bold"), bg="#fdf6e3", fg="#586e75")
        self.timer_label.pack(pady=(5, 10))

        self.button_frame = tk.Frame(root, bg="#fdf6e3")
        self.button_frame.pack()

        self.start_button = tk.Button(self.button_frame, text="Start", command=self.start_timer, width=8, bg="#2aa198", fg="white")
        self.start_button.grid(row=0, column=0, padx=2)

        self.pause_button = tk.Button(self.button_frame, text="Pause", command=self.pause_timer, width=8, bg="#b58900", fg="white")
        self.pause_button.grid(row=0, column=1, padx=2)

        self.resume_button = tk.Button(self.button_frame, text="Resume", command=self.resume_timer, width=8, bg="#6c71c4", fg="white")
        self.resume_button.grid(row=0, column=0, padx=2)
        self.resume_button.grid_remove()

        self.reset_button = tk.Button(root, text="Reset", command=self.reset_timer, bg="#dc322f", fg="white", width=25)
        self.reset_button.pack(pady=(5, 5))

        self.add_button = tk.Button(root, text="Add Session", command=self.add_session_tab, bg="#859900", fg="white", width=25)
        self.add_button.pack(pady=(0, 5))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TNotebook.Tab", padding=[6, 2], background="#eee8d5", font=('Helvetica', 9))
        self.style.map("TNotebook.Tab", background=[("selected", "#b58900")], foreground=[("selected", "#fff")])

        self.load_sessions_from_file()

        if not self.sessions:
            self.add_session_tab()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def save_sessions_to_file(self):
        data = []
        for session in self.sessions:
            name = session["name"].get().strip()
            time = session["time"].get().strip()
            if name and time.isdigit():
                data.append({"name": name, "time": time})
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_sessions_from_file(self):
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                for session_data in data:
                    self.add_session_tab(session_data["name"], session_data["time"])
        except (json.JSONDecodeError, IOError):
            print("⚠️ Failed to load session settings.")

    def add_session_tab(self, default_name="", default_time=""):
        frame = ttk.Frame(self.notebook)
        frame.configure(style='TFrame')

        name_var = tk.StringVar(value=default_name)
        time_var = tk.StringVar(value=default_time)

        label_name = tk.Label(frame, text="Session Name:", bg="#eee8d5")
        label_name.pack(pady=(8, 0))
        name_entry = tk.Entry(frame, textvariable=name_var, width=18)
        name_entry.pack(pady=(0, 4))

        label_time = tk.Label(frame, text="Duration (min):", bg="#eee8d5")
        label_time.pack()
        time_entry = tk.Entry(frame, textvariable=time_var, width=18)
        time_entry.pack(pady=(0, 5))

        remove_button = tk.Button(frame, text="Remove Session", command=lambda: self.remove_session_tab(frame), bg="#cb4b16", fg="white")
        remove_button.pack(pady=(8, 5))

        self.sessions.append({
            "frame": frame,
            "name": name_var,
            "time": time_var
        })
        self.notebook.add(frame, text=default_name or "New Session")

        # Real-time update tab name and save
        name_var.trace_add('write', lambda *args, nv=name_var, f=frame: [self.update_tab_title(nv, f), self.save_sessions_to_file()])
        time_var.trace_add('write', lambda *args: self.save_sessions_to_file())

    def update_tab_title(self, name_var, frame):
        index = self.notebook.index(frame)
        name = name_var.get().strip()
        if name:
            self.notebook.tab(index, text=name)

    def remove_session_tab(self, frame):
        idx = self.notebook.index(frame)
        self.notebook.forget(frame)
        del self.sessions[idx]
        self.save_sessions_to_file()
        if self.current_index >= len(self.sessions):
            self.reset_timer()

    def start_timer(self):
        if self.timer_running:
            return

        self.current_index = self.notebook.index(self.notebook.select())
        session = self.sessions[self.current_index]
        name = session["name"].get().strip() or f"Session {self.current_index + 1}"
        time_text = session["time"].get().strip()

        if not time_text.isdigit():
            messagebox.showerror("Invalid input", "Time must be a number.")
            return

        self.original_time = int(time_text) * 60
        self.remaining_time = self.original_time
        self.session_name_label.config(text=name)
        self.timer_running = True
        self.timer_paused = False
        self.start_button.grid_remove()
        self.resume_button.grid_remove()
        self.update_timer()

    def update_timer(self):
        if self.timer_running and not self.timer_paused:
            mins, secs = divmod(self.remaining_time, 60)
            self.timer_label.config(text=f"{mins:02}:{secs:02}")
            if self.remaining_time > 0:
                self.remaining_time -= 1
                self.root.after(1000, self.update_timer)
            else:
                winsound.Beep(1000, 500)
                self.move_to_next_session()

    def pause_timer(self):
        if self.timer_running:
            self.timer_paused = True
            self.resume_button.grid()
            self.start_button.grid_remove()

    def resume_timer(self):
        if self.timer_running and self.timer_paused:
            self.timer_paused = False
            self.resume_button.grid_remove()
            self.update_timer()

    def reset_timer(self):
        self.timer_running = False
        self.timer_paused = False
        self.resume_button.grid_remove()
        self.start_button.grid()
        self.timer_label.config(text="00:00")
        self.session_name_label.config(text="Session Timer")
        self.remaining_time = self.original_time

    def move_to_next_session(self):
        if self.current_index + 1 < len(self.sessions):
            self.current_index += 1
            self.notebook.select(self.current_index)
            self.timer_running = False
            self.start_timer()
        else:
            self.reset_timer()

    def on_close(self):
        if messagebox.askyesno("Exit", "Do you want to save your session settings before exiting?"):
            self.save_sessions_to_file()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SessionTimerApp(root)
    root.mainloop()
