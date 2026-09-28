#!/bin/zsh
set -eu
MV_DIR=${0:A:h}
mkdir -p "$MV_DIR/.build/swift-cache"
MV_BUILD_DIR=$(mktemp -d "$MV_DIR/.build/audio.XXXXXX")
trap 'rm -rf "$MV_BUILD_DIR"' EXIT
MV_ARCHS=("$(uname -m)")
if [[ "${1:-}" == "--universal" ]]; then
    MV_ARCHS=(arm64 x86_64)
fi
for MV_ARCH in "${MV_ARCHS[@]}"; do
    xcrun swiftc -O -module-cache-path "$MV_DIR/.build/swift-cache" \
        -target "$MV_ARCH-apple-macosx12.0" "$MV_DIR/AudioClock.swift" \
        -o "$MV_BUILD_DIR/audio-clock-$MV_ARCH"
done
if [[ ${#MV_ARCHS} -eq 2 ]]; then
    lipo -create "$MV_BUILD_DIR/audio-clock-arm64" "$MV_BUILD_DIR/audio-clock-x86_64" -output "$MV_BUILD_DIR/audio-clock"
else
    cp "$MV_BUILD_DIR/audio-clock-${MV_ARCHS[1]}" "$MV_BUILD_DIR/audio-clock"
fi
chmod 755 "$MV_BUILD_DIR/audio-clock"
mv "$MV_BUILD_DIR/audio-clock" "$MV_DIR/audio-clock"
print 'Audio helper ready.'
