"""HTTP routes for the viewer and MJPEG stream."""

from __future__ import annotations

import base64
import binascii
from contextlib import asynccontextmanager
from pathlib import Path
import secrets
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from .config import Config
from .streaming import FrameHub

STATIC = Path(__file__).parent / "static"


def create_app(config: Config, hub: FrameHub | None = None) -> FastAPI:
    hub = hub or FrameHub(config)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            hub.start()
            yield
        finally:
            hub.stop()

    app = FastAPI(title="OpenScreen", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

    def authorize(request: Request) -> None:
        if config.password is None:
            return
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        try:
            decoded = base64.b64decode(token, validate=True).decode("utf-8") if scheme.lower() == "basic" else ""
            username, password = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError, binascii.Error):
            username, password = "", ""
        if not (
            secrets.compare_digest(username.encode("utf-8"), b"viewer")
            and secrets.compare_digest(password.encode("utf-8"), config.password.encode("utf-8"))
        ):
            raise HTTPException(
                status_code=401,
                detail="需要访问密码",
                headers={"WWW-Authenticate": 'Basic realm="OpenScreen", charset="UTF-8"'},
            )

    @app.get("/", dependencies=[Depends(authorize)])
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-store"})

    @app.get("/style.css", dependencies=[Depends(authorize)])
    def style() -> FileResponse:
        return FileResponse(STATIC / "style.css", media_type="text/css")

    @app.get("/app.js", dependencies=[Depends(authorize)])
    def script() -> FileResponse:
        return FileResponse(STATIC / "app.js", media_type="text/javascript")

    @app.get("/status", dependencies=[Depends(authorize)])
    def status() -> dict[str, object]:
        return {
            "ok": hub.error is None,
            "error": hub.error,
            "monitor": config.monitor,
            "fps": config.fps,
        }

    def frames() -> Iterator[bytes]:
        last_sequence = 0
        while True:
            current = hub.next_frame(last_sequence)
            if current is None:
                if hub.error is not None or hub.stopped:
                    break
                continue
            last_sequence, jpeg = current
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                + f"Content-Length: {len(jpeg)}\r\n\r\n".encode("ascii")
                + jpeg
                + b"\r\n"
            )

    @app.get("/stream", dependencies=[Depends(authorize)])
    def stream() -> StreamingResponse:
        if hub.error is not None:
            raise HTTPException(status_code=503, detail=hub.error)
        return StreamingResponse(
            frames(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate", "X-Content-Type-Options": "nosniff"},
        )

    return app
