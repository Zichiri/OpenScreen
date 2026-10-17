"""Command-line configuration."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    host: str = "0.0.0.0"
    port: int = 8000
    monitor: int = 1
    fps: int = 12
    max_width: int = 1920
    quality: int = 75
    password: str | None = None


def parse_args(argv: list[str] | None = None) -> tuple[Config, bool]:
    parser = argparse.ArgumentParser(
        prog="openscreen",
        description="在局域网内通过浏览器观看本机屏幕",
    )
    parser.add_argument("--host", default="0.0.0.0", help="监听地址，默认 0.0.0.0")
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    parser.add_argument("--monitor", type=int, default=1, help="显示器编号；0 表示全部显示器")
    parser.add_argument("--list-monitors", action="store_true", help="列出显示器并退出")
    parser.add_argument("--fps", type=int, default=12, help="每秒最多采集多少帧，默认 12")
    parser.add_argument("--max-width", type=int, default=1920, help="输出画面最大宽度，默认 1280")
    parser.add_argument("--quality", type=int, default=75, help="JPEG 质量，范围 1-95")
    parser.add_argument("--password", help="可选的访问密码；启用后浏览器使用 HTTP Basic 登录")
    args = parser.parse_args(argv)

    if not 1 <= args.port <= 65535:
        parser.error("--port 必须在 1-65535 之间")
    if args.monitor < 0:
        parser.error("--monitor 不能小于 0")
    if not 1 <= args.fps <= 60:
        parser.error("--fps 必须在 1-60 之间")
    if args.max_width < 160:
        parser.error("--max-width 不能小于 160")
    if not 1 <= args.quality <= 95:
        parser.error("--quality 必须在 1-95 之间")
    if args.password == "":
        parser.error("--password 不能为空")

    return Config(
        host=args.host,
        port=args.port,
        monitor=args.monitor,
        fps=args.fps,
        max_width=args.max_width,
        quality=args.quality,
        password=args.password,
    ), args.list_monitors
