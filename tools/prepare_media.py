"""从指定的原版发布包安全提取音乐；绝不执行其中的代码或二进制。"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://github.com/yym8224961/world.execute-me-ascii/releases/download/v1.0.0/world-execute-mv.pyz'
BUNDLE_SHA256 = '55043652a24c38301d7042b9508d91af52b0c184d23a9f45f570892cdf03e6db'
AUDIO_SHA256 = '2da5fb306fc83b178617da9283b94e65933ae0c9c99d40b0b91be5266ed21a40'
MAX_BYTES = 20 * 1024 * 1024


def extract(data, destination):
    # 固定整个归档和音频的摘要，不信任归档自行提供的清单。
    if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != BUNDLE_SHA256:
        raise ValueError('原版发布包校验失败，未提取任何文件。')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.getinfo('media/song.mp3')
        if info.file_size > MAX_BYTES:
            raise ValueError('音频资源尺寸异常。')
        audio = archive.read(info)
    if hashlib.sha256(audio).hexdigest() != AUDIO_SHA256:
        raise ValueError('音乐校验失败。')
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != AUDIO_SHA256:
            raise ValueError('目标已存在其他音乐，不会覆盖。')
    else:
        with destination.open('xb') as output:
            output.write(audio)
    return {'source': URL, 'release': 'v1.0.0', 'bundle_sha256': BUNDLE_SHA256,
            'audio_sha256': AUDIO_SHA256, 'audio_bytes': len(audio)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=ROOT/'world-execute-mv.pyz')
    parser.add_argument('--download', action='store_true', help='显式下载固定版本，只在准备资源时联网')
    args = parser.parse_args()
    if args.download:
        with urllib.request.urlopen(URL, timeout=60) as response:
            data = response.read(MAX_BYTES + 1)
    else:
        with args.bundle.open('rb') as source:
            data = source.read(MAX_BYTES + 1)
    result = extract(data, ROOT/'media/song.mp3')
    (ROOT/'media/provenance.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('音乐已准备完成；仅提取 media/song.mp3，未执行发布包。')


if __name__ == '__main__':
    main()
