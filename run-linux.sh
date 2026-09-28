#!/bin/sh
# Linux 入口：只使用已有虚拟环境，不在启动时安装依赖或下载资源。
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$ROOT/.venv/bin/python" ]; then
    printf '%s\n' '请先按 README-Windows.md 创建虚拟环境并安装依赖。' >&2
    exit 1
fi
export PYTHONUTF8=1
exec "$ROOT/.venv/bin/python" "$ROOT/player.py" "$@"
