"""Run the OpenScreen service."""

from __future__ import annotations

import socket

from .capture import check_macos_permission, monitor_descriptions
from .config import parse_args


def local_ipv4() -> str | None:
    """Best-effort LAN address discovery without sending a packet."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 80))
            address = sock.getsockname()[0]
            if not address.startswith("127."):
                return address
    except OSError:
        pass
    try:
        addresses = socket.gethostbyname_ex(socket.gethostname())[2]
        return next((address for address in addresses if not address.startswith("127.")), None)
    except OSError:
        return None


def main() -> None:
    config, list_monitors = parse_args()
    if list_monitors:
        check_macos_permission()
        for description in monitor_descriptions():
            print(description)
        return

    from .server import create_app
    import uvicorn

    if config.host in ("0.0.0.0", "::"):
        address = local_ipv4()
        print(f"本机访问：http://127.0.0.1:{config.port}", flush=True)
        if address:
            print(f"局域网访问：http://{address}:{config.port}", flush=True)
        else:
            print("请查询本机局域网 IPv4 地址，并访问 http://该地址:端口", flush=True)
    else:
        print(f"访问地址：http://{config.host}:{config.port}", flush=True)
    if config.password is not None:
        print("访问用户名：viewer", flush=True)
    uvicorn.run(create_app(config), host=config.host, port=config.port, log_level="info")


if __name__ == "__main__":
    main()
