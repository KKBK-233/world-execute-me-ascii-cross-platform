# world.execute(me); 终端 MV

![world.execute(me); 画面预览](docs/images/mv-cover.png)

在终端播放 Mili《world.execute(me);》的字符动画和中英字幕。本仓库提供 Windows / Linux 本地有声版，以及无需登录的在线只读画面。

| 使用方式 | 入口 | 声音 |
| --- | --- | --- |
| 在线观看，Windows / Linux 终端 | `curl -N "https://www.kkbk.info/world.execute(me);"` | 无 |
| Windows x64 本地播放 | 从 [Release](https://github.com/KKBK-233/world-execute-me-ascii-cross-platform/releases) 下载 Windows ZIP，解压并运行 `WorldExecuteMV/Play-MV.bat` | 有 |
| Linux x86_64 本地播放 | 下载 Linux ZIP，解压并运行 `WorldExecuteMV/WorldExecuteMV` | 有，需本机音频输出 |

Windows PowerShell / CMD 请用 `curl.exe -N "https://www.kkbk.info/world.execute(me);"`。**URL 必须加引号**，否则括号和分号会被 Shell 当作语法。在线画面在连接后自动从开头播放；按 Ctrl+C 退出。建议终端至少 100 列 × 32 行。

源码与构建说明：[Windows](README-Windows.md) · [Linux 与在线服务](README-Linux.md)。在线服务使用 [stream_server.py](stream_server.py)，博客的 Nginx 路由配置保存在私有 `blog_glm` 仓库；服务不提供 Shell 或文件下载。

## 仓库导航

| 路径 | 用途 |
| --- | --- |
| `player.py`、`audio_pcm.py`、`terminal_io.py` | 本地有声播放 |
| `stream_server.py` | HTTP 终端画面，无音频 |
| `scenes.py`、`lyrics.json`、`spectrum.json`、`config.json` | 动画、字幕与时间数据 |
| `assets/` | 可单独使用的 SRT 与 LRC 字幕 |
| `tools/` | 校验提取音乐、构建便携包 |
| `tests/` | 播放、资源及 HTTP 服务测试 |
| `deploy/` | 两台服务器的 systemd 配置 |
| `docs/` | 历史验收记录 |

## 来源与权利

本仓库基于 [yym8224961/world.execute-me-ascii](https://github.com/yym8224961/world.execute-me-ascii) 的画面与资源，原版发布物见[上游 v1.0.0](https://github.com/yym8224961/world.execute-me-ascii/releases/tag/v1.0.0)。歌曲、歌词和原版代码的权利归各自权利人；本仓库没有额外授予再分发或改编许可。便携包内含音乐，使用前请自行确认授权范围。
