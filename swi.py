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
    'Space': 0x39,  # Scancode for the "Space" key
    'z': 0x2C   # Scancode for the "z" key
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

class WindowManager:
    def __init__(self):
        self.pids = []
        self.hwnds = []
        self.running = False
        self.current_index = 0
        self.switch_interval = 1500  # Default interval is 1.5 seconds

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
        root.after(int(self.switch_interval), self.switch_windows)

class KeyPresser:
    def __init__(self):
        self.running = False
        self.threads = []
        self.keys = {}

    def add_key(self, key, frequency):
        if key in KEY_CODES:
            self.keys[KEY_CODES[key]] = frequency

    def remove_key(self, key):
        if key in KEY_CODES:
            self.keys.pop(KEY_CODES[key], None)

    def start_pressing(self):
        self.running = True
        self.threads = []
        for key, frequency in self.keys.items():
            thread = threading.Thread(target=self.press_key, args=(key, frequency))
            thread.start()
            self.threads.append(thread)

    def stop_pressing(self):
        self.running = False
        for thread in self.threads:
            if thread.is_alive():
                thread.join()

    def press_key(self, key, frequency):
        while self.running:
            PressKey(key)
            time.sleep(0.1)
            ReleaseKey(key)
            time.sleep(frequency)

# Tworzenie GUI
root = tk.Tk()
root.title("Window Switcher")

wm = WindowManager()
kp = KeyPresser()

def start():
    try:
        pids = [int(pid_entry.get()) for pid_entry in pid_entries if pid_entry.get().isdigit()]
        wm.pids = pids
        wm.switch_interval = float(switch_interval_entry.get()) * 1000  # Update switch interval
        wm.start_switching()
        kp.start_pressing()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid PIDs.")

def stop():
    wm.stop_switching()
    kp.stop_pressing()

frame = tk.Frame(root)
frame.pack(pady=10)

pid_label = tk.Label(frame, text="Enter up to 6 PIDs:")
pid_label.grid(row=0, column=0, padx=5, columnspan=2)

pid_entries = []
for i in range(6):
    pid_entry = tk.Entry(frame, width=10)
    pid_entry.grid(row=i+1, column=0, padx=5, pady=2)
    pid_entries.append(pid_entry)

key_label = tk.Label(frame, text="Select Keys to Press and Frequency (s):")
key_label.grid(row=7, column=0, padx=5, columnspan=2)

keys_frame = tk.Frame(frame)
keys_frame.grid(row=8, column=0, columnspan=2, padx=5)

key_vars = {
    '1': (tk.BooleanVar(), tk.DoubleVar(value=0.3)),
    '2': (tk.BooleanVar(), tk.DoubleVar(value=1.0)),
    '3': (tk.BooleanVar(), tk.DoubleVar(value=1.0)),
    'Space': (tk.BooleanVar(), tk.DoubleVar(value=1.0)),
    'z': (tk.BooleanVar(), tk.DoubleVar(value=0.3))
}

def on_key_change():
    kp.keys.clear()
    for key, (var, freq_var) in key_vars.items():
        if var.get():
            kp.add_key(key, freq_var.get())
        else:
            kp.remove_key(key)

for idx, key in enumerate(key_vars):
    var, freq_var = key_vars[key]
    checkbox = tk.Checkbutton(keys_frame, text=key, variable=var, command=on_key_change)
    checkbox.grid(row=idx, column=0, sticky='w')
    freq_entry = tk.Entry(keys_frame, textvariable=freq_var, width=5)
    freq_entry.grid(row=idx, column=1, padx=5)

switch_interval_label = tk.Label(frame, text="Switch Interval (s):")
switch_interval_label.grid(row=9, column=0, padx=5)

switch_interval_entry = tk.Entry(frame)
switch_interval_entry.grid(row=9, column=1, padx=5)
switch_interval_entry.insert(0, "1.5")  # Default value

start_button = tk.Button(frame, text="Start", command=start)
start_button.grid(row=10, column=0, padx=5, pady=5)

stop_button = tk.Button(frame, text="Stop", command=stop)
stop_button.grid(row=10, column=1, padx=5, pady=5)

root.mainloop()
