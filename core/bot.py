"""
DesktopBot - Streamlined MaaFramework Procedural Automation Wrapper
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

from maa.controller import Win32Controller
from maa.define import MaaWin32ScreencapMethodEnum, MaaWin32InputMethodEnum
from maa.resource import Resource
from maa.tasker import Tasker
from maa.pipeline import JOCR

from core.window import activate_window, ensure_default_desktop, user32

logger = logging.getLogger("DesktopBot")


class DesktopBot:
    """Streamlined Bot wrapping MaaFramework vision and Win32 hardware control."""

    def __init__(self, resource_path: Optional[str] = None):
        ensure_default_desktop()
        self.project_root = Path(__file__).resolve().parent.parent
        self.resource_path = Path(resource_path) if resource_path else self.project_root / "resource"

        self.hwnd: Optional[int] = None
        self.controller: Optional[Win32Controller] = None
        self.resource = Resource()
        self.tasker = Tasker()

        # Initialize MaaFramework resource bundle
        load_res = self.resource.post_bundle(str(self.resource_path)).wait()
        if not load_res.succeeded:
            logger.warning(f"Resource bundle loading returned non-success: {self.resource_path}")

    def connect(self, hwnd: int, activate: bool = True) -> bool:
        """Connect to target window by HWND using FramePool screencap and Seize input."""
        ensure_default_desktop()
        self.hwnd = hwnd

        if activate:
            activate_window(hwnd)
            time.sleep(0.3)

        # 优先使用 Windows Graphics Capture (FramePool) 和硬件级 Seize 输入
        screencap_candidates = [
            MaaWin32ScreencapMethodEnum.FramePool,
            MaaWin32ScreencapMethodEnum.PrintWindow,
            MaaWin32ScreencapMethodEnum.GDI
        ]

        self.controller = None
        for cap_method in screencap_candidates:
            try:
                ctrl = Win32Controller(
                    hwnd,
                    screencap_method=cap_method.value,
                    mouse_method=MaaWin32InputMethodEnum.Seize
                )
                if ctrl.post_connection().wait().succeeded:
                    # 验证截屏是否可用
                    cached = ctrl.post_screencap().wait().get()
                    if cached is not None and cached.size > 0:
                        self.controller = ctrl
                        break
            except Exception:
                continue

        if not self.controller:
            logger.error(f"无法建立与窗口 (HWND: {hex(hwnd)}) 的有效截屏控制器连接！")
            return False

        self.tasker.bind(self.resource, self.controller)
        return True

    def is_window_alive(self) -> bool:
        """Check if target window HWND is still valid and visible."""
        if not self.hwnd:
            return False
        return bool(user32.IsWindow(self.hwnd) and user32.IsWindowVisible(self.hwnd))

    def activate(self) -> bool:
        """Bring target window to the foreground."""
        if not self.hwnd:
            return False
        return activate_window(self.hwnd)

    def ocr(self) -> List[Dict[str, Any]]:
        """
        Perform OCR scan on the target window screen.
        Returns a list of detected text dicts:
        [{ "text": str, "box": [x, y, w, h], "center": (cx, cy), "score": float }]
        """
        if not self.controller:
            raise RuntimeError("Bot is not connected to any window. Call connect(hwnd) first.")

        img = self.controller.post_screencap().wait().get()
        if img is None or img.size == 0:
            return []

        job = self.tasker.post_recognition("OCR", JOCR(), img)
        task_detail = job.wait().get()
        if not task_detail or not task_detail.node_id_list:
            return []

        node_detail = self.tasker.get_node_detail(task_detail.node_id_list[0])
        reco = node_detail.recognition
        if not reco or not reco.all_results:
            return []

        results = []
        for item in reco.all_results:
            box = item.box
            cx = box[0] + box[2] // 2
            cy = box[1] + box[3] // 2
            results.append({
                "text": item.text.strip(),
                "box": [box[0], box[1], box[2], box[3]],
                "center": (cx, cy),
                "score": float(item.score)
            })

        return results

    def click(self, x: int, y: int) -> bool:
        """Click on the target coordinate."""
        if not self.controller:
            raise RuntimeError("Bot is not connected to any window.")
        job = self.controller.post_click(x, y)
        return bool(job.wait().succeeded)
