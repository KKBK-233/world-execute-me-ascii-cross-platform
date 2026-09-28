# Windows 本地有声播放

从 [Release](https://github.com/KKBK-233/world-execute-me-ascii-cross-platform/releases) 下载 `world-execute-mv-windows-x64.zip`，解压后运行 `WorldExecuteMV/Play-MV.bat`。包内已有音乐和 Python 运行环境；保持整个 `WorldExecuteMV` 文件夹完整。源码目录也可运行 `播放MV.bat`。

播放器启动后按空格开始。建议终端至少 128 列 × 44 行，使用支持中文的等宽字体。

| 按键 | 功能 |
| --- | --- |
| 空格 / Enter | 播放或暂停 |
| ← / → | 后退或前进 5 秒 |
| 1–5 | 跳转章节 |
| R | 从头播放 |
| + / - | 调整程序音量 |
| H | 显示帮助 |
| Q / Esc / Ctrl+C | 退出 |

示例：`WorldExecuteMV.exe --start 158.7 --autoplay`。音频使用系统默认输出设备；切换设备后重新启动。运行时不联网。

## 从源码运行和构建

使用 Python 3.12，在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe tools/prepare_media.py --download
.\.venv\Scripts\python.exe player.py
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe tools/build_portable.py
```

`prepare_media.py` 只读取、校验上游固定版本资源中的音乐，不执行上游程序；已有不同的 `media/song.mp3` 不会被覆盖。播放器使用 PortAudio 输出 PCM，并以音频设备时钟驱动画面。

Windows 11 x64 已验证终端播放、暂停、跳转、重播、退出和整曲静音设备运行；实际听感与音画同步仍需主观试听。历史记录见 `docs/windows-validation.json`。
