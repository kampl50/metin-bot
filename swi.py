import time
import ctypes
import win32gui
import win32process
import win32api

# Ustal PIDy okien
pids = [22060,8928]

def get_hwnds_for_pid(pid):
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

def is_minimized(hwnd):
    """Check if a window is minimized."""
    return win32gui.IsIconic(hwnd)

def bring_window_to_foreground(hwnd):
    """Bring a window to the foreground."""
    if is_minimized(hwnd):
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

def main():
    hwnds = []
    for pid in pids:
        hwnd_list = get_hwnds_for_pid(pid)
        if hwnd_list:
            hwnds.append(hwnd_list[0])
        else:
            print(f"Error: No window found for PID {pid}")
            return

    current_index = 0

    while True:
        bring_window_to_foreground(hwnds[current_index])
        current_index = (current_index + 1) % len(hwnds)
        time.sleep(3)

if __name__ == "__main__":
    main()
