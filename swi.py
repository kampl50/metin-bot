import time
import ctypes
import win32gui
import win32process
import win32api
import tkinter as tk
from tkinter import messagebox
import threading

# Windows API constants and structures
PUL = ctypes.POINTER(ctypes.c_ulong)
SendInput = ctypes.windll.user32.SendInput

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

KEY_CODES = {
    '1': 0x02,  # Scancode for the "1" key
    '2': 0x03,  # Scancode for the "2" key
    '3': 0x04,  # Scancode for the "3" key
    'Space': 0x39  # Scancode for the "Space" key
}

def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, KEYEVENTF_SCANCODE, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

# Main classes
class WindowManager:
    def __init__(self):
        self.pids = []
        self.hwnds = []
        self.running = False
        self.current_index = 0

    def get_hwnds_for_pid(self, pid):
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
        return win32gui.IsIconic(hwnd)

    def bring_window_to_foreground(self, hwnd):
        if self.is_minimized(hwnd):
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            time.sleep(0.1)

        current_thread_id = win32api.GetCurrentThreadId()
        window_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        ctypes.windll.user32.AttachThreadInput(current_thread_id, window_thread_id, True)

        ctypes.windll.user32.SetForegroundWindow(hwnd)
        time.sleep(0.1)
        ctypes.windll.user32.BringWindowToTop(hwnd)
        time.sleep(0.1)
        ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
        time.sleep(0.1)

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

class KeyPresser:
    def __init__(self):
        self.running = False
        self.thread = None
        self.keys = set()  # Default to empty set

    def add_key(self, key):
        if key in KEY_CODES:
            self.keys.add(KEY_CODES[key])

    def remove_key(self, key):
        if key in KEY_CODES:
            self.keys.discard(KEY_CODES[key])

    def start_pressing(self):
        self.running = True
        self.thread = threading.Thread(target=self.press_keys)
        self.thread.start()

    def stop_pressing(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def press_keys(self):
        while self.running:
            for key in self.keys:
                PressKey(key)
                time.sleep(0.1)
                ReleaseKey(key)
                time.sleep(1)

# Create the GUI
root = tk.Tk()
root.title("Window Switcher")

wm = WindowManager()
kp = KeyPresser()

def start():
    try:
        pids = list(map(int, pid_entry.get().split()))
        wm.pids = pids
        wm.start_switching()
        kp.start_pressing()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid list of PIDs separated by spaces.")

def stop():
    wm.stop_switching()
    kp.stop_pressing()

frame = tk.Frame(root)
frame.pack(pady=10)

pid_label = tk.Label(frame, text="Enter PIDs (separated by spaces):")
pid_label.grid(row=0, column=0, padx=5)

pid_entry = tk.Entry(frame)
pid_entry.grid(row=0, column=1, padx=5)

key_label = tk.Label(frame, text="Select Keys to Press:")
key_label.grid(row=1, column=0, padx=5)

keys_frame = tk.Frame(frame)
keys_frame.grid(row=1, column=1, padx=5)

key_vars = {
    '1': tk.BooleanVar(),
    '2': tk.BooleanVar(),
    '3': tk.BooleanVar(),
    'Space': tk.BooleanVar()
}

def on_key_change():
    kp.keys.clear()
    for key, var in key_vars.items():
        if var.get():
            kp.add_key(key)
        else:
            kp.remove_key(key)

for key in key_vars:
    checkbox = tk.Checkbutton(keys_frame, text=key, variable=key_vars[key], command=on_key_change)
    checkbox.pack(anchor='w')

start_button = tk.Button(frame, text="Start", command=start)
start_button.grid(row=2, column=0, padx=5, pady=5)

stop_button = tk.Button(frame, text="Stop", command=stop)
stop_button.grid(row=2, column=1, padx=5, pady=5)

root.mainloop()
