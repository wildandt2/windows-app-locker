import psutil
import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess
import time
import threading
import hashlib
import json
import pystray
from PIL import Image, ImageDraw
import sys
import os

# =============================
# SAFE PATH (WORKS FOR EXE)
# =============================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else BASE_DIR, "config.json")

# =============================
# CREATE CONFIG IF NOT EXISTS
# =============================
if not os.path.exists(CONFIG_PATH):
    default_config = {
        "apps": ["chrome.exe", "notepad.exe"],
        "password_hash": ""
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(default_config, f, indent=4)

# =============================
# LOAD CONFIG
# =============================
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

LOCKED_APPS = config["apps"]
PASSWORD_HASH = config["password_hash"]

allow_open = False


# =============================
# HASH FUNCTION
# =============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =============================
# SET PASSWORD FIRST TIME
# =============================
def set_password():
    root = tk.Tk()
    root.withdraw()
    pwd = simpledialog.askstring("Set Password", "Buat Password:", show="*")

    if pwd:
        config["password_hash"] = hash_password(pwd)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        messagebox.showinfo("Success", "Password berhasil dibuat.")
        return hash_password(pwd)
    return None


if PASSWORD_HASH == "":
    PASSWORD_HASH = set_password()


# =============================
# PASSWORD CHECK
# =============================
def ask_password():
    global allow_open
    root = tk.Tk()
    root.withdraw()

    user_input = simpledialog.askstring("App Locked", "Masukkan Password:", show="*")

    if user_input and hash_password(user_input) == PASSWORD_HASH:
        allow_open = True
        messagebox.showinfo("Success", "Password Benar.")
    else:
        messagebox.showerror("Error", "Password Salah!")


# =============================
# MONITOR APPS
# =============================
def monitor():
    global allow_open
    while True:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in LOCKED_APPS:
                if not allow_open:
                    proc.kill()
                    ask_password()
                else:
                    allow_open = False
        time.sleep(1)


# =============================
# SYSTEM TRAY
# =============================
def create_tray():
    image = Image.new('RGB', (64, 64), color='black')
    draw = ImageDraw.Draw(image)
    draw.text((20, 20), "L", fill='white')

    def exit_app(icon, item):
        icon.stop()
        os._exit(0)

    icon = pystray.Icon("AppLocker", image, menu=pystray.Menu(
        pystray.MenuItem("Exit", exit_app)
    ))
    icon.run()


# =============================
# MAIN
# =============================
if __name__ == "__main__":
    print("App Locker V3 Ultimate Running...")

    threading.Thread(target=monitor, daemon=True).start()
    threading.Thread(target=create_tray, daemon=True).start()

    while True:
        time.sleep(10)
