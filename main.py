import psutil
import subprocess
import time
import threading
import hashlib
import json
import sys
import os
import customtkinter as ctk
from tkinter import messagebox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =============================
# SAFE CONFIG PATH
# =============================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# =============================
# DEFAULT CONFIG
# =============================
default_config = {
    "apps": ["chrome.exe"],
    "folders": [],
    "password_hash": ""
}

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        json.dump(default_config, f, indent=4)

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

LOCKED_APPS = config["apps"]
LOCKED_FOLDERS = config["folders"]
PASSWORD_HASH = config["password_hash"]

allow_open = False


# =============================
# HASH
# =============================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


# =============================
# PASSWORD WINDOW (MODERN UI)
# =============================
def password_window():
    global allow_open

    def check():
        if hash_password(entry.get()) == PASSWORD_HASH:
            allow_open = True
            app.destroy()
        else:
            messagebox.showerror("Error", "Wrong Password")

    app = ctk.CTk()
    app.title("App Locked")
    app.geometry("300x200")

    label = ctk.CTkLabel(app, text="Enter Password", font=("Arial", 18))
    label.pack(pady=20)

    entry = ctk.CTkEntry(app, show="*")
    entry.pack(pady=10)

    btn = ctk.CTkButton(app, text="Unlock", command=check)
    btn.pack(pady=10)

    app.mainloop()


# =============================
# MONITOR APPS
# =============================
def monitor_apps():
    global allow_open
    while True:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in LOCKED_APPS:
                if not allow_open:
                    proc.kill()
                    password_window()
                else:
                    allow_open = False
        time.sleep(1)


# =============================
# FOLDER LOCK (BLOCK EXPLORER)
# =============================
class FolderHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        global allow_open
        if not allow_open:
            password_window()


def monitor_folders():
    observer = Observer()
    handler = FolderHandler()

    for folder in LOCKED_FOLDERS:
        if os.path.exists(folder):
            observer.schedule(handler, folder, recursive=True)

    observer.start()


# =============================
# WATCHDOG SELF RESTART
# =============================
def watchdog():
    while True:
        time.sleep(5)
        if not any(p.info['name'] == os.path.basename(sys.executable) for p in psutil.process_iter(['name'])):
            subprocess.Popen(sys.executable)


# =============================
# FIRST TIME PASSWORD SET
# =============================
if PASSWORD_HASH == "":
    temp = ctk.CTk()
    temp.withdraw()
    new_pass = ctk.CTkInputDialog(text="Create Password", title="Setup").get_input()
    if new_pass:
        config["password_hash"] = hash_password(new_pass)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        PASSWORD_HASH = config["password_hash"]
    temp.destroy()


# =============================
# MAIN
# =============================
if __name__ == "__main__":
    threading.Thread(target=monitor_apps, daemon=True).start()
    threading.Thread(target=monitor_folders, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()

    while True:
        time.sleep(10)
