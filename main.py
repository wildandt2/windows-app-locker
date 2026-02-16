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

# =============================
# UI SETTINGS
# =============================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =============================
# CONFIG LOCATION (AppData)
# =============================
APPDATA_DIR = os.path.join(os.getenv("LOCALAPPDATA"), "AppLocker")
os.makedirs(APPDATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(APPDATA_DIR, "config.json")

# =============================
# DEFAULT CONFIG
# =============================
default_config = {
    "apps": ["chrome.exe"],
    "password_hash": "",
    "max_attempts": 3,
    "lockout_seconds": 30
}

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        json.dump(default_config, f, indent=4)

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# Auto-fix missing keys
for key in default_config:
    if key not in config:
        config[key] = default_config[key]

with open(CONFIG_PATH, "w") as f:
    json.dump(config, f, indent=4)

LOCKED_APPS = config["apps"]
PASSWORD_HASH = config["password_hash"]
MAX_ATTEMPTS = config["max_attempts"]
LOCKOUT_SECONDS = config["lockout_seconds"]

allow_open = False
unlock_requested = False
failed_attempts = 0
lockout_until = 0


# =============================
# HASH
# =============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =============================
# PASSWORD WINDOW
# =============================
def show_password_window():
    global allow_open, unlock_requested
    global failed_attempts, lockout_until

    if time.time() < lockout_until:
        remaining = int(lockout_until - time.time())
        messagebox.showwarning(
            "Locked",
            f"Too many attempts.\nTry again in {remaining} seconds."
        )
        unlock_requested = False
        return

    def check():
        global allow_open, unlock_requested
        global failed_attempts, lockout_until

        if hash_password(entry.get()) == PASSWORD_HASH:
            allow_open = True
            failed_attempts = 0
            unlock_requested = False
            app.destroy()
        else:
            failed_attempts += 1
            if failed_attempts >= MAX_ATTEMPTS:
                lockout_until = time.time() + LOCKOUT_SECONDS
                failed_attempts = 0
                messagebox.showerror(
                    "Locked Out",
                    f"Too many wrong attempts.\nLocked for {LOCKOUT_SECONDS} seconds."
                )
                app.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    f"Wrong Password\nAttempt {failed_attempts}/{MAX_ATTEMPTS}"
                )

    app = ctk.CTk()
    app.title("Application Locked")
    app.geometry("320x220")
    app.resizable(False, False)

    label = ctk.CTkLabel(app, text="Enter Password", font=("Arial", 18))
    label.pack(pady=20)

    entry = ctk.CTkEntry(app, show="*")
    entry.pack(pady=10)

    button = ctk.CTkButton(app, text="Unlock", command=check)
    button.pack(pady=10)

    app.mainloop()


# =============================
# MONITOR APPS
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

    try:
        while True:
            if unlock_requested:
                show_password_window()
            time.sleep(1)

    except KeyboardInterrupt:
        print("App stopped safely.")
