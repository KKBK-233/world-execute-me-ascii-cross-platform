# Linux 本地播放与在线终端画面

## 直接在线观看

```sh
curl -N 'https://www.kkbk.info/world.execute(me);'
```

连接后自动从开头播放，按 Ctrl+C 退出。URL 必须加引号。Windows PowerShell / CMD 使用 `curl.exe -N "https://www.kkbk.info/world.execute(me);"`。该 HTTP 路由只输出 ANSI 画面和字幕，不传输声音，也不提供登录或远程命令。建议终端至少 100 列 × 32 行。

## Linux 本地有声播放

从 [Release](https://github.com/KKBK-233/world-execute-me-ascii-cross-platform/releases) 下载 Linux x86_64 ZIP，解压后运行 `WorldExecuteMV/WorldExecuteMV`。首次源码运行可按 Ubuntu 22.04 示例准备：

```sh
sudo apt install python3-venv libportaudio2 libsndfile1
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/prepare_media.py --download
./run-linux.sh
```

默认按空格开始，`./run-linux.sh --autoplay` 可直接播放。构建便携包需先安装 `requirements-build.txt`，再运行 `tools/build_portable.py`。Linux 包已在 Ubuntu 22.04 x86_64 上验证解压后输出画面；测试服务器没有 PCM 输出设备，有声实播仍待验证。其他发行版与架构也未验收。

## 部署终端画面服务

`stream_server.py` 仅依赖 Python 标准库，在连接后按时间轴输出画面。`deploy/blog-world-execute.service` 只监听 127.0.0.1:41090，并由博客仓库中的 Nginx 精确路由接入域名。公开入口同时只允许一个观看连接，额外请求返回 HTTP 429；公开画面约 212 秒一轮。音频文件不是该服务所需资源。

上游项目与资源权利说明见 [README](README.md)。
