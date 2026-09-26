"""
Linguo macOS Platform Utilities
Clipboard integration (pbcopy), synthetic paste (AppleScript Cmd+V),
system notifications, sound effects, and Cocoa runtime discovery.
"""

import os
import sys
import subprocess
from ..core.config import load_config


def copy_to_clipboard(text: str):
    """Copies text to macOS clipboard using pbcopy."""
    try:
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, close_fds=True)
        p.communicate(input=text.encode("utf-8"))
    except Exception as e:
        sys.stderr.write(f"Failed to copy to clipboard: {e}\n")


def paste_to_active_window():
    """Simulates Cmd+V via AppleScript to instantly paste text into any focused app."""
    script = 'tell application "System Events" to keystroke "v" using command down'
    subprocess.run(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def play_sound(sound_name: str = "Tink"):
    """Plays subtle macOS feedback sound."""
    cfg = load_config()
    if not cfg.get("sound_feedback", True):
        return
    sound_path = f"/System/Library/Sounds/{sound_name}.aiff"
    if os.path.exists(sound_path):
        subprocess.Popen(["afplay", sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def show_mac_notification(title: str, subtitle: str, message: str):
    """Displays native macOS Notification Banner."""
    cfg = load_config()
    if not cfg.get("notifications", True):
        return
    safe_title = title.replace('"', '\\"')
    safe_subtitle = subtitle.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    apple_script = f'display notification "{safe_msg}" with title "{safe_title}" subtitle "{safe_subtitle}"'
    subprocess.Popen(["osascript", "-e", apple_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_python_cocoa_path() -> str:
    """Finds a Python interpreter with PyObjC Cocoa installed."""
    candidates = [sys.executable, "/usr/local/bin/python3", "/opt/homebrew/bin/python3", "/usr/bin/python3"]
    for c in candidates:
        if c and os.path.exists(c):
            try:
                res = subprocess.run([c, "-c", "import Cocoa"], capture_output=True)
                if res.returncode == 0:
                    return c
            except Exception:
                pass
    return sys.executable
