import io
import importlib.util
import threading
import time
import unittest
from unittest.mock import patch

from openscreen.capture import encode_jpeg, select_monitor
from openscreen.config import Config, parse_args
from openscreen.streaming import FrameHub


class ConfigTests(unittest.TestCase):
    def test_defaults_and_options(self):
        config, list_monitors = parse_args([])
        self.assertEqual((config.host, config.port, config.monitor, config.fps), ("0.0.0.0", 8000, 1, 12))
        self.assertFalse(list_monitors)
        config, list_monitors = parse_args(["--monitor", "0", "--list-monitors", "--quality", "85"])
        self.assertEqual((config.monitor, config.quality, list_monitors), (0, 85, True))

    def test_invalid_options(self):
        for args in (["--port", "0"], ["--fps", "61"], ["--monitor", "-1"], ["--quality", "0"]):
            with self.subTest(args=args), patch("sys.stderr", new=io.StringIO()):
                with self.assertRaises(SystemExit):
                    parse_args(args)


class CaptureTests(unittest.TestCase):
    def test_invalid_monitor_gives_actionable_error(self):
        sct = type("Sct", (), {"monitors": [{}, {}]})()
        with self.assertRaisesRegex(ValueError, "--list-monitors"):
            select_monitor(sct, 2)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "需要安装 Pillow")
    def test_bgra_encoding_and_resize(self):
        from PIL import Image

        shot = type("Shot", (), {"size": (4, 2), "bgra": bytes([0, 0, 255, 255] * 8)})()
        jpeg = encode_jpeg(shot, max_width=2, quality=75)
        image = Image.open(io.BytesIO(jpeg))
        self.assertEqual(image.size, (2, 1))
        self.assertGreater(image.getpixel((0, 0))[0], 200)


class FrameHubTests(unittest.TestCase):
    def test_slow_viewer_gets_newest_frame(self):
        hub = FrameHub(Config())
        with hub._condition:
            hub._frame, hub._sequence = b"first", 1
            hub._frame, hub._sequence = b"newest", 2
            hub._condition.notify_all()
        self.assertEqual(hub.next_frame(0), (2, b"newest"))
        self.assertIsNone(hub.next_frame(2, timeout=0.01))

    def test_waiter_wakes_on_new_frame(self):
        hub = FrameHub(Config())
        result = []
        waiter = threading.Thread(target=lambda: result.append(hub.next_frame(0, timeout=1)))
        waiter.start()
        time.sleep(0.02)
        with hub._condition:
            hub._frame, hub._sequence = b"frame", 1
            hub._condition.notify_all()
        waiter.join(timeout=1)
        self.assertFalse(waiter.is_alive())
        self.assertEqual(result, [(1, b"frame")])


if __name__ == "__main__":
    unittest.main()
