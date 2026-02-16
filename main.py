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

# =============================
# UI SETTINGS
# =============================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =============================
# SAFE PATH
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

# Create config if not exist
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        json.dump(default_config, f, indent=4)

# Load config
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# Auto-fix missing keys
for key in default_config:
    if key not in config:
        config[key] = default_config[key]

with open(CONFIG_PATH, "w") as f:
    json.dump(config, f, indent=4)

LOCKED_APPS = config["apps"]
LOCKED_FOLDERS = config["folders"]
PASSWORD_HASH = config["password_hash"]

allow_open = False
unlock_requested = False


# =============================
# HASH FUNCTION
# =============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =============================
# PASSWORD WINDOW
# =============================
def show_password_window():
    global allow_open, unlock_requested

    def check():
        global allow_open, unlock_requested
        if hash_password(entry.get()) == PASSWORD_HASH:
            allow_open = True
            unlock_requested = False
            app.destroy()
        else:
            messagebox.showerror("Error", "Wrong Password")

    app = ctk.CTk()
    app.title("Application Locked")
    app.geometry("300x200")
    app.resizable(False, False)

    label = ctk.CTkLabel(app, text="Enter Password", font=("Arial", 18))
    label.pack(pady=20)

    entry = ctk.CTkEntry(app, show="*")
    entry.pack(pady=10)

    button = ctk.CTkButton(app, text="Unlock", command=check)
    button.pack(pady=10)

    app.mainloop()


# =============================
# MONITOR APPS (THREAD SAFE)
# =============================
def monitor_apps():
    global unlock_requested
    while True:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in LOCKED_APPS:
                    if not allow_open:
                        proc.kill()
                        unlock_requested = True
            except:
                pass
        time.sleep(1)


# =============================
# FOLDER LOCK (BASIC MONITOR)
# =============================
class FolderHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        global unlock_requested
        if not allow_open:
            unlock_requested = True


def monitor_folders():
    observer = Observer()
    handler = FolderHandler()

    for folder in LOCKED_FOLDERS:
        if os.path.exists(folder):
            observer.schedule(handler, folder, recursive=True)

    observer.start()


# =============================
# FIRST TIME PASSWORD SET
# =============================
def first_time_setup():
    global PASSWORD_HASH

    app = ctk.CTk()
    app.withdraw()

    dialog = ctk.CTkInputDialog(
        text="Create New Password",
        title="First Time Setup"
    )
    new_password = dialog.get_input()

    if new_password:
        PASSWORD_HASH = hash_password(new_password)
        config["password_hash"] = PASSWORD_HASH
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)

    app.destroy()


if PASSWORD_HASH == "":
    first_time_setup()


# =============================
# MAIN LOOP
# =============================
if __name__ == "__main__":

    threading.Thread(target=monitor_apps, daemon=True).start()
    threading.Thread(target=monitor_folders, daemon=True).start()

    try:
        while True:
            if unlock_requested:
                show_password_window()
            time.sleep(1)

    except KeyboardInterrupt:
        print("App stopped safely.")
