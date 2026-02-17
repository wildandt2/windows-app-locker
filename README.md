# 🔒 App Locker (Windows)

A lightweight Windows background application that locks selected apps 
(e.g. Notion, Chrome) behind a password.

Built with:
- Python
- psutil
- CustomTkinter

---

## ✨ Features

- Lock specific applications by process name
- Secure password (SHA-256 hashed)
- Auto-lock when app is closed
- Brute-force protection (lockout timer)
- Lightweight background monitoring
- Electron-app safe (no crash issues)

---

## 📦 Requirements

- Windows OS
- Python 3.9+

Install dependencies:

```bash
pip install -r requirements.txt
🚀 How To Run
python main.py
The program will:

Ask you to create a password (first run only)

Run silently in background

Monitor selected apps

When a locked app is opened:

It will be closed

Password window will appear

If correct password:

App will open normally

Remains unlocked until fully closed