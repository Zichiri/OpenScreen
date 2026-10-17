"""One capture worker and a latest-frame buffer shared by all viewers."""

from __future__ import annotations

import logging
import threading
import time

from .capture import check_macos_permission, encode_jpeg, select_monitor
from .config import Config

logger = logging.getLogger(__name__)


class FrameHub:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._condition = threading.Condition()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._frame: bytes | None = None
        self._sequence = 0
        self._error: str | None = None

    @property
    def error(self) -> str | None:
        with self._condition:
            return self._error

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def start(self, timeout: float = 15.0) -> None:
        check_macos_permission()
        self._thread = threading.Thread(target=self._capture_loop, name="screen-capture", daemon=True)
        self._thread.start()
        deadline = time.monotonic() + timeout
        with self._condition:
            while self._frame is None and self._error is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("等待第一帧超时；请检查屏幕录制权限和显示器状态")
                self._condition.wait(remaining)
            if self._error:
                raise RuntimeError(self._error)

    def stop(self) -> None:
        self._stop.set()
        with self._condition:
            self._condition.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=3)

    def next_frame(self, last_sequence: int, timeout: float = 1.0) -> tuple[int, bytes] | None:
        with self._condition:
            self._condition.wait_for(
                lambda: self._sequence > last_sequence or self._error is not None or self._stop.is_set(),
                timeout=timeout,
            )
            if self._error or self._stop.is_set():
                return None
            if self._frame is None or self._sequence <= last_sequence:
                return None
            return self._sequence, self._frame

    def _capture_loop(self) -> None:
        try:
            from mss import MSS

            interval = 1 / self.config.fps
            with MSS() as sct:
                monitor = select_monitor(sct, self.config.monitor)
                while not self._stop.is_set():
                    started = time.monotonic()
                    screenshot = sct.grab(monitor)
                    frame = encode_jpeg(screenshot, self.config.max_width, self.config.quality)
                    with self._condition:
                        self._frame = frame
                        self._sequence += 1
                        self._condition.notify_all()
                    self._stop.wait(max(0, interval - (time.monotonic() - started)))
        except Exception as exc:
            logger.exception("屏幕采集停止")
            with self._condition:
                self._error = f"屏幕采集失败：{exc}"
                self._condition.notify_all()
