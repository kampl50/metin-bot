import time
import ctypes
import win32gui
import win32process
import win32api
import tkinter as tk
from tkinter import messagebox

class WindowManager:
    def __init__(self):
        self.pids = []
        self.hwnds = []
        self.running = False
        self.current_index = 0

    def get_hwnds_for_pid(self, pid):
        """Get window handles for a given process id."""
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    hwnds.append(hwnd)
            return True

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds

    def is_minimized(self, hwnd):
        """Check if a window is minimized."""
        return win32gui.IsIconic(hwnd)

    def bring_window_to_foreground(self, hwnd):
        """Bring a window to the foreground."""
        if self.is_minimized(hwnd):
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            time.sleep(0.1)

        # Attach the thread of the target window to the current thread
        current_thread_id = win32api.GetCurrentThreadId()
        window_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        ctypes.windll.user32.AttachThreadInput(current_thread_id, window_thread_id, True)

        ctypes.windll.user32.SetForegroundWindow(hwnd)
        time.sleep(0.1)
        ctypes.windll.user32.BringWindowToTop(hwnd)
        time.sleep(0.1)
        ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
        time.sleep(0.1)

        # Detach the thread
        ctypes.windll.user32.AttachThreadInput(current_thread_id, window_thread_id, False)

    def update_hwnds(self):
        self.hwnds = []
        for pid in self.pids:
            hwnd_list = self.get_hwnds_for_pid(pid)
            if hwnd_list:
                self.hwnds.append(hwnd_list[0])
            else:
                print(f"Error: No window found for PID {pid}")

    def start_switching(self):
        self.running = True
        self.update_hwnds()
        self.switch_windows()

    def stop_switching(self):
        self.running = False

    def switch_windows(self):
        if not self.running or not self.hwnds:
            return
        self.bring_window_to_foreground(self.hwnds[self.current_index])
        self.current_index = (self.current_index + 1) % len(self.hwnds)
        root.after(3000, self.switch_windows)

def start():
    try:
        pids = list(map(int, pid_entry.get().split()))
        wm.pids = pids
        wm.start_switching()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid list of PIDs separated by spaces.")

def stop():
    wm.stop_switching()

# Create the GUI
root = tk.Tk()
root.title("Window Switcher")

wm = WindowManager()

frame = tk.Frame(root)
frame.pack(pady=10)

pid_label = tk.Label(frame, text="Enter PIDs (separated by spaces):")
pid_label.grid(row=0, column=0, padx=5)

pid_entry = tk.Entry(frame)
pid_entry.grid(row=0, column=1, padx=5)

start_button = tk.Button(frame, text="Start", command=start)
start_button.grid(row=1, column=0, padx=5, pady=5)

stop_button = tk.Button(frame, text="Stop", command=stop)
stop_button.grid(row=1, column=1, padx=5, pady=5)

root.mainloop()
