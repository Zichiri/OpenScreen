import base64
import importlib.util
import unittest


@unittest.skipUnless(
    importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
    "需要安装开发依赖：pip install -e '.[dev]'",
)
class ServerTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from openscreen.config import Config
        from openscreen.server import create_app

        class FakeHub:
            error = None
            stopped = False

            def start(self):
                pass

            def stop(self):
                self.stopped = True

            def next_frame(self, last_sequence):
                if last_sequence == 0:
                    return 1, b"jpeg-frame"
                self.stopped = True
                return None

        self.client = TestClient(create_app(Config(password="secret"), FakeHub()))
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def _auth(self, password="secret"):
        token = base64.b64encode(f"viewer:{password}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    def test_every_route_requires_password(self):
        for path in ("/", "/style.css", "/app.js", "/status", "/stream"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get("/", headers=self._auth("wrong")).status_code, 401)

    def test_authenticated_view_and_stream(self):
        response = self.client.get("/", headers=self._auth())
        self.assertEqual(response.status_code, 200)
        self.assertIn("OpenScreen", response.text)
        self.assertTrue(self.client.get("/status", headers=self._auth()).json()["ok"])
        response = self.client.get("/stream", headers=self._auth())
        self.assertEqual(response.status_code, 200)
        self.assertIn("multipart/x-mixed-replace", response.headers["content-type"])
        self.assertIn(b"Content-Type: image/jpeg\r\n", response.content)
        self.assertIn(b"jpeg-frame", response.content)

    def test_utf8_password(self):
        from fastapi.testclient import TestClient
        from openscreen.config import Config
        from openscreen.server import create_app

        class IdleHub:
            error = None
            stopped = False

            def start(self):
                pass

            def stop(self):
                pass

        with TestClient(create_app(Config(password="屏幕密码"), IdleHub())) as client:
            token = base64.b64encode("viewer:屏幕密码".encode("utf-8")).decode("ascii")
            response = client.get("/status", headers={"Authorization": f"Basic {token}"})
            self.assertEqual(response.status_code, 200)
