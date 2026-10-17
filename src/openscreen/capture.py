"""Capture and encode a selected display."""

from __future__ import annotations

import ctypes
import ctypes.util
import io
import sys
from typing import Any


def check_macos_permission() -> None:
    """Prompt for macOS screen recording permission when the native API is available."""
    if sys.platform != "darwin":
        return
    library = ctypes.util.find_library("CoreGraphics")
    if not library:
        return
    core_graphics = ctypes.CDLL(library)
    preflight = getattr(core_graphics, "CGPreflightScreenCaptureAccess", None)
    request = getattr(core_graphics, "CGRequestScreenCaptureAccess", None)
    if preflight is None:
        return
    preflight.restype = ctypes.c_bool
    if preflight():
        return
    if request is not None:
        request.restype = ctypes.c_bool
        if request():
            return
    raise RuntimeError(
        "macOS 尚未授予屏幕录制权限。请到 系统设置 → 隐私与安全性 → 屏幕与系统音频录制，"
        "允许当前终端或 Python，然后重新启动终端和服务。"
    )


def monitor_descriptions() -> list[str]:
    from mss import MSS

    with MSS() as sct:
        return [
            f"{index}: {item['width']}×{item['height']} "
            f"(x={item['left']}, y={item['top']})"
            + (" [全部显示器]" if index == 0 else "")
            for index, item in enumerate(sct.monitors)
        ]


def select_monitor(sct: Any, index: int) -> Any:
    monitors = sct.monitors
    if index >= len(monitors):
        raise ValueError(
            f"找不到显示器 {index}；当前可选范围为 0-{len(monitors) - 1}。"
            "可运行 openscreen --list-monitors 查看编号。"
        )
    return monitors[index]


def encode_jpeg(screenshot: Any, max_width: int, quality: int) -> bytes:
    from PIL import Image

    # MSS supplies BGRA bytes on both Windows and macOS. Converting directly
    # to RGB avoids depending on platform-specific Pillow screenshot APIs.
    image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    if image.width > max_width:
        height = max(1, round(image.height * max_width / image.width))
        image = image.resize((max_width, height), Image.Resampling.BILINEAR)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality)
    return output.getvalue()
