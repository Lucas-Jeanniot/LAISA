import tkinter as tk
import subprocess
import sys

def install_packages():
    try:
        import requests
    except ImportError:
        print("requests package not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])

def create_tooltip(widget, text):
    tooltip = tk.Toplevel(widget)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry("+0+0")
    label = tk.Label(tooltip, text=text, bg='#2e2e2e', fg='white', font=("Arial", 10), bd=1, relief="solid")
    label.pack()

    def enter(event):
        x = event.x_root + 10
        y = event.y_root + 10
        tooltip.wm_geometry(f"+{x}+{y}")
        tooltip.deiconify()

    def leave(event):
        tooltip.withdraw()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)
    tooltip.withdraw()
