"""
Linguo Platform Module
macOS integration and background services.
"""

from .macos import copy_to_clipboard, paste_to_active_window, play_sound, show_mac_notification, get_python_cocoa_path

__all__ = [
    "copy_to_clipboard", "paste_to_active_window", "play_sound",
    "show_mac_notification", "get_python_cocoa_path"
]
