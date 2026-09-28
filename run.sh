#!/bin/zsh
set -eu
MV_DIR=${0:A:h}
export LANG=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
if [[ ! -x "$MV_DIR/audio-clock" ]]; then
    /bin/zsh "$MV_DIR/build-audio.sh"
fi
for MV_PYTHON in /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 /opt/homebrew/bin/python3 /usr/bin/python3; do
    if [[ -x "$MV_PYTHON" ]]; then
        exec "$MV_PYTHON" "$MV_DIR/player.py" "$@"
    fi
done
print -u2 '找不到 Python 3。请安装 Python 3 后重试。'
exit 1
