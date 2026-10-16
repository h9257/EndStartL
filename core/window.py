"""
Window helper utilities for desktop discovery and management (Pure ctypes Win32).
"""

import ctypes
from ctypes import wintypes
from typing import List, Dict, Optional, Any

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def ensure_default_desktop():
    """Ensure the current thread has access to the interactive 'Default' desktop."""
    try:
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
            return True
    except Exception:
        pass
    return False


def get_window_title(hwnd: int) -> str:
    """Get the window title for a given HWND."""
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    return ""


def get_window_class_name(hwnd: int) -> str:
    """Get the window class name for a given HWND."""
    buff = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buff, 256)
    return buff.value


def get_window_rect(hwnd: int) -> Dict[str, int]:
    """Get window bounding rectangle."""
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return {
        "x": rect.left,
        "y": rect.top,
        "w": rect.right - rect.left,
        "h": rect.bottom - rect.top,
        "left": rect.left,
        "top": rect.top,
        "right": rect.right,
        "bottom": rect.bottom
    }


def list_windows(include_empty_titles: bool = False) -> List[Dict[str, Any]]:
    """List all visible top-level windows on the desktop."""
    ensure_default_desktop()
    results = []

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        rect = get_window_rect(hwnd)
        if rect["w"] <= 5 or rect["h"] <= 5:
            return True

        title = get_window_title(hwnd)
        if not include_empty_titles and not title.strip():
            return True

        class_name = get_window_class_name(hwnd)

        # Ignore system background workers without titles
        if class_name in ("Progman", "WorkerW", "Shell_TrayWnd", "Windows.UI.Core.CoreWindow"):
            if not title.strip():
                return True

        results.append({
            "hwnd": int(hwnd),
            "hwnd_hex": hex(hwnd),
            "title": title.strip(),
            "class_name": class_name,
            "rect": rect
        })
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    results.sort(key=lambda item: (not bool(item["title"]), item["title"].lower()))
    return results


def find_window_by_title(keyword: str) -> Optional[Dict[str, Any]]:
    """Find the first visible window matching a keyword in title (case-insensitive)."""
    windows = list_windows()
    keyword_lower = keyword.strip().lower()
    for w in windows:
        if keyword_lower in w["title"].lower():
            return w
    return None


def activate_window(hwnd: int) -> bool:
    """Bring the window to the foreground."""
    try:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        return bool(user32.SetForegroundWindow(hwnd))
    except Exception:
        return False
