#!/bin/zsh
set -eu
MV_DIR=${0:A:h}
export LANG=en_US.UTF-8
export PYTHONUTF8=1
MV_BUNDLE="$MV_DIR/world-execute-mv.pyz"
if [[ ! -f "$MV_BUNDLE" ]]; then
    print -u2 '请将此启动文件与 world-execute-mv.pyz 放在同一目录。'
    exit 1
fi
exec python3 "$MV_BUNDLE" "$@"
