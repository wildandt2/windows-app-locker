import psutil
import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess
import time
import threading

# =============================
# CONFIG
# =============================
LOCKED_APP = "chrome.exe"   # Ganti sesuai kebutuhan
PIN = "1234"                # Ganti PIN kamu
# =============================

allow_open = False

def ask_password():
    global allow_open
    root = tk.Tk()
    root.withdraw()

    user_input = simpledialog.askstring("App Locked", "Masukkan PIN:", show='*')

    if user_input == PIN:
        allow_open = True
        messagebox.showinfo("Success", "PIN Benar. Aplikasi dibuka.")
        subprocess.Popen(LOCKED_APP)
    else:
        messagebox.showerror("Error", "PIN Salah!")

def monitor():
    global allow_open
    while True:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == LOCKED_APP:
                if not allow_open:
                    proc.kill()
                    ask_password()
                else:
                    allow_open = False
        time.sleep(1)

if __name__ == "__main__":
    print("App Locker berjalan...")
    threading.Thread(target=monitor, daemon=True).start()

    while True:
        time.sleep(10)
