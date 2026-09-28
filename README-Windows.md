# Windows 验收版 / Linux 适配入口

## Windows：不安装 Python、不找音乐

解压便携包后，双击 `Play-MV.bat` 或 `WorldExecuteMV.exe`。**整个目录必须保留**，不要单独移走 EXE；音乐和运行库在 `_internal` 中。源码目录也可双击 `播放MV.bat`，优先启动已构建的便携版。

播放器默认等待按空格开始，不会启动即响。建议最大化终端，至少 64 列 × 24 行，128 列 × 44 行效果更好。中文显示异常时使用支持中文的等宽字体或 Windows Terminal。运行不联网、不下载资源、不需要管理员权限。

| 按键 | 功能 |
| --- | --- |
| 空格 / Enter | 开始、暂停、继续 |
| ← / → | 前后跳转 5 秒 |
| 1–5 | 跳到章节并播放 |
| R | 从头播放 |
| + / - | 调整程序音量，不改变系统总音量 |
| H | 帮助 |
| Q / Esc / Ctrl+C | 退出并恢复终端 |

命令行示例：

```powershell
.\WorldExecuteMV.exe --start 158.7 --autoplay
.\WorldExecuteMV.exe --volume 0.3
.\WorldExecuteMV.exe --snapshot 67.3 --plain
```

音频使用系统默认输出设备；切换设备后重新启动。若启动失败，通过 `Play-MV.bat` 保留错误信息。此本地构建没有代码签名；不要为运行而关闭系统安全防护或全局放宽策略。

## 实现与验收边界

- 原版场景、字幕、频谱保持不变。音乐从上游 v1.0.0 包中按固定 SHA-256 校验后提取；没有执行其 macOS 二进制。
- MP3 启动时解码到内存中的 PCM，按样本定位，以 PortAudio 输出设备时钟推进画面。无需 FFmpeg。
- 三分半立体声 PCM 约占 71 MiB，另有 Python、依赖和动画开销。程序不将解码缓存写入硬盘。
- 暂停或跳转可能仍听到少量已进入设备缓冲区的声音，取决于音频设备延迟；音画是否符合预期仍需人工试听。
- Windows 是本轮验收目标。Linux 已有共用后端和启动入口，未完成 Linux 桌面/声卡实播验收；macOS 原生后端保留，未在本机回归。

## 从源码开发（Windows）

需要 Python 3.12（本次构建使用的版本）。以下命令仅首次准备环境时联网，正常播放不联网：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
# 已有原版 pyz 时直接提取；没有时显式添加 --download
.\.venv\Scripts\python.exe tools/prepare_media.py
.\.venv\Scripts\python.exe player.py
.\.venv\Scripts\python.exe tests/test_portable.py
.\.venv\Scripts\python.exe tools/build_portable.py
```

`tools/prepare_media.py --download` 仅下载指定上游发布包并校验，不执行包内程序。已有不同的 `media/song.mp3` 不会被覆盖。

## Linux（待实际声卡验收）

Ubuntu / Debian 示例，需要桌面音频会话；不要使用 sudo 运行播放器：

```sh
sudo apt install python3-venv libportaudio2 libsndfile1
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/prepare_media.py --download
sh ./run-linux.sh
```

在 Linux 上安装 `requirements-build.txt` 后运行 `tools/build_portable.py` 可构建该平台便携包；不能拿 Windows EXE 当 Linux 版本。其他发行版、ARM64 与不同 glibc 版本需要单独验证。

## 资源与许可

音乐和歌词：Mili《world.execute(me);》。上游项目：yym8224961/world.execute-me-ascii，Release v1.0.0。当前资源只用于本地验收；内嵌音乐不代表获得重新分发授权。源码包未提供独立 LICENSE，不在此新增任何第三方再授权。

便携包记录 `media-provenance.json`、`dependency-versions.json`，并保留依赖许可证。公开上传或分发前应确认代码、音乐和歌词的授权。上游摘要证明本次文件与选定发布物一致，不是发布者数字签名。

## 本轮已验证（2026-09-28）

- Windows 11 x64：17 项单元/资源测试通过；3 项原版 macOS 专用测试按平台跳过。
- 打包 EXE：真实 ConPTY 测试自动播放、暂停、左右跳转、章节切换、重播/帮助、Ctrl+C；全部通过并恢复终端。
- 完整 211.9067 秒真实速度静音播放：5,090 帧，音频欠载 0 次，最大单帧渲染约 31 ms。
- ZIP 解压到独立临时路径后，EXE 能在项目之外输出中英字幕画面。
- 原版 scenes.py、lyrics.json、spectrum.json 与上游包逐字节一致。
- 以上音频设备测试使用程序音量 0；实际可闻声音、音画同步和终端观感仍由用户验收。
