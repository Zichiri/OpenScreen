# OpenScreen

一个局域网推流的软件，只支持观看，无法传输声音和远程控制

在 Windows 或 macOS 电脑上启动服务，同一局域网内的其它设备用浏览器打开 `http://电脑IP:8000`，即可实时查看这台电脑的屏幕。服务使用一个采集线程生成 MJPEG 画面，多名观看者共享最新帧；网络变慢时会跳过旧帧。

## 安装

需要 Python 3.10 或更新版本。请在**准备共享屏幕的电脑**上执行。

Windows PowerShell：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m openscreen
```

macOS 终端：

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .
./.venv/bin/python -m openscreen
```

启动后终端会打印本机和局域网访问地址。观看者与共享电脑需要在可互访的局域网中，并在浏览器打开打印出的局域网地址。按 `Ctrl+C` 结束共享。

macOS 首次运行可能弹出屏幕录制权限请求。请允许当前使用的终端或 Python；如果已经在系统设置中手动授权，请**退出并重新打开终端**，然后重新运行服务。设置位置通常是“系统设置 → 隐私与安全性 → 屏幕与系统音频录制”。Windows 首次运行若弹出防火墙提示，请允许在专用网络访问；也可以自行放行所用端口。

## 常用选项

命令中的 `python -m openscreen` 可以换成已安装的 `openscreen` 命令。以下以 macOS 虚拟环境路径为例；Windows 使用 `.\.venv\Scripts\python.exe` 替换 `./.venv/bin/python`。

```bash
./.venv/bin/python -m openscreen --list-monitors
./.venv/bin/python -m openscreen --monitor 2 --port 9000
./.venv/bin/python -m openscreen --fps 15 --max-width 1600 --quality 75
./.venv/bin/python -m openscreen --password 'your-password'
```

`--monitor` 默认是 `1`，`0` 表示所有显示器拼接后的虚拟桌面。默认设置是 12 FPS、最大宽度 1280 像素、JPEG 质量 70、监听 `0.0.0.0:8000`。使用 `--host 127.0.0.1` 可仅允许本机访问。运行 `python -m openscreen --help` 可查看全部参数。

设置密码后，浏览器登录用户名为 `viewer`。服务使用 HTTP Basic 验证；局域网内的 HTTP 通信**没有加密**，包括画面和密码。请仅在可信网络中使用。更高的安全需求应在服务前配置 HTTPS 反向代理或 VPN。命令行密码也可能显示在本机进程列表中。

## 常见问题

- **其它电脑打不开**：确认访问的是共享电脑的局域网 IPv4 地址，且两台设备可互访；检查 Windows/macOS 防火墙，以及路由器是否启用了客户端隔离。终端打印的地址只是尽力检测；有多个网卡或 VPN 时，可能需要手动使用正确的局域网 IP。
- **macOS 画面黑屏或提示权限不足**：给启动服务的终端或 Python 授予屏幕录制权限，并退出终端后重新启动。某些受保护内容仍可能被系统隐藏。
- **显示器编号错误**：先运行 `--list-monitors`，再通过 `--monitor` 选择。插拔显示器后请重启服务。
- **画面卡顿**：先降低 `--fps` 或 `--max-width`；MJPEG 每帧都是 JPEG，多名观看者的网络带宽会随人数增加。

## 开发检查

先激活虚拟环境，或把以下 `python` 换成上文 `.venv` 中的 Python 路径，然后运行：

```bash
python -m pip install -e '.[dev]'
python -m unittest discover -s tests -v
```
