#!/bin/zsh
set -eu
MV_DIR=${0:A:h}
exec /bin/zsh "$MV_DIR/run.sh" "$@"
