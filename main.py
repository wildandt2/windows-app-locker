import psutil
import subprocess
import time
import threading
import hashlib
import json
import os
import customtkinter as ctk
from tkinter import messagebox

# =============================
# UI SETTINGS
# =============================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =============================
# CONFIG
# =============================
APPDATA_DIR = os.path.join(os.getenv("LOCALAPPDATA"), "AppLocker")
os.makedirs(APPDATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(APPDATA_DIR, "config.json")

default_config = {
    "apps": ["notion.exe", "chrome.exe"],
    "password_hash": "",
    "max_attempts": 3,
    "lockout_seconds": 30
}

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        json.dump(default_config, f, indent=4)

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

for key in default_config:
    if key not in config:
        config[key] = default_config[key]

with open(CONFIG_PATH, "w") as f:
    json.dump(config, f, indent=4)

LOCKED_APPS = [a.lower() for a in config["apps"]]
PASSWORD_HASH = config["password_hash"]
MAX_ATTEMPTS = config["max_attempts"]
LOCKOUT_SECONDS = config["lockout_seconds"]

# =============================
# GLOBAL STATE
# =============================
app_unlocked = False
password_window_open = False
failed_attempts = 0
lockout_until = 0

# =============================
# HASH
# =============================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# =============================
# FIRST TIME SETUP
# =============================
def first_time_setup():
    global PASSWORD_HASH

    app = ctk.CTk()
    app.withdraw()

    dialog = ctk.CTkInputDialog(
        text="Create New Password",
        title="First Setup"
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
# PASSWORD WINDOW
# =============================
def show_password_window(app_name, exe_path):
    global app_unlocked
    global password_window_open
    global failed_attempts
    global lockout_until

    if time.time() < lockout_until:
        return

    password_window_open = True

    def check():
        global app_unlocked
        global failed_attempts
        global lockout_until

        if hash_password(entry.get()) == PASSWORD_HASH:
            failed_attempts = 0
            app_unlocked = True
            window.destroy()

            subprocess.Popen(exe_path)

        else:
            failed_attempts += 1

            if failed_attempts >= MAX_ATTEMPTS:
                lockout_until = time.time() + LOCKOUT_SECONDS
                failed_attempts = 0
                messagebox.showerror(
                    "Locked",
                    f"Too many wrong attempts.\nLocked {LOCKOUT_SECONDS}s."
                )
                window.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    f"Wrong password ({failed_attempts}/{MAX_ATTEMPTS})"
                )

    window = ctk.CTk()
    window.title("Application Locked")
    window.geometry("320x200")
    window.resizable(False, False)

    label = ctk.CTkLabel(window, text=f"{app_name} Locked", font=("Arial", 16))
    label.pack(pady=20)

    entry = ctk.CTkEntry(window, show="*", width=200)
    entry.pack(pady=10)
    entry.focus()

    button = ctk.CTkButton(window, text="Unlock", command=check)
    button.pack(pady=10)

    window.mainloop()
    password_window_open = False

# =============================
# CHECK IF APP STILL RUNNING
# =============================
def is_app_running():
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in LOCKED_APPS:
                return True
        except:
            pass
    return False

# =============================
# MONITOR
# =============================
def monitor_apps():
    global app_unlocked

    while True:
        running = is_app_running()

        # Kalau app tidak berjalan → reset lock
        if not running:
            app_unlocked = False

        for proc in psutil.process_iter(['name', 'exe']):
            try:
                name = proc.info['name']
                if not name:
                    continue

                if name.lower() in LOCKED_APPS:

                    if app_unlocked:
                        continue

                    exe_path = proc.info['exe']
                    proc.terminate()

                    if not password_window_open and exe_path:
                        threading.Thread(
                            target=show_password_window,
                            args=(name, exe_path),
                            daemon=True
                        ).start()

            except:
                pass

        time.sleep(1)

# =============================
# MAIN
# =============================
if __name__ == "__main__":
    threading.Thread(target=monitor_apps, daemon=True).start()

    while True:
        time.sleep(1)
