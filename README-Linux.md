# Linux 运行与终端观看

## 服务器上的只读画面

`stream_server.py` 使用 Python 标准库输出 ANSI 动画与字幕，不需要音频设备、账户登录或 Python 第三方依赖。每位观众从影片开头独立观看；画面无声音，也不能通过连接控制播放。

Windows PowerShell / CMD 与 Linux 终端都可以运行：

```text
curl -N http://186.241.105.219:41090/
```

Windows 若 `curl` 被 PowerShell 映射为别的命令，可使用 `curl.exe -N http://186.241.105.219:41090/`。建议终端至少 100 列、32 行；按 Ctrl+C 退出。服务只开放 `/` 画面和 `/healthz` 健康检查，不提供 Shell 或文件下载。默认最多 4 人同时观看，画面每秒 8 帧，单次播放约 212 秒。公开端口上的画面与歌词可以被任何能连到端口的人观看。

## Linux 本机有声播放

有声版本需要 Linux 主机有可用的音频输出设备及 PortAudio。进入项目目录后：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/prepare_media.py
./run-linux.sh
```

默认按空格开始；使用 `./run-linux.sh --autoplay` 可立即播放。无声服务器没有 PCM 播放设备，因此该服务器只能验证源码运行、资源、画面与构建，不能代表有声实播验收。

## 服务部署配置

`deploy/world-execute-stream.service` 将画面服务作为隔离的 systemd 动态用户运行，限制内存、CPU 和并发。它只读取 `/opt/world-execute-me-ascii` 下的源码与 JSON 资源。开放 41090/tcp 前应确认宿主机防火墙及云平台防火墙；无需修改现有 SSH 服务。
