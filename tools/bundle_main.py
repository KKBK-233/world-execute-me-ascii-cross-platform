"""Extract bundled media into a private temporary directory, then run the player."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import runpy
import sys
import tempfile
import zipfile


def main():
    if sys.platform != 'darwin':
        raise SystemExit('这个单文件播放器需要 macOS 12 或更新版本。')
    archive = Path(sys.argv[0]).resolve()
    sys.dont_write_bytecode = True
    with tempfile.TemporaryDirectory(prefix='world-execute-mv-') as directory:
        root = Path(directory)
        with zipfile.ZipFile(archive) as bundle:
            manifest = json.loads(bundle.read('bundle-manifest.json'))
            for name, digest in manifest['files'].items():
                relative = PurePosixPath(name)
                if relative.is_absolute() or '..' in relative.parts:
                    raise SystemExit('程序包资源路径无效。')
                data = bundle.read(name)
                if hashlib.sha256(data).hexdigest() != digest:
                    raise SystemExit('程序包资源校验失败：' + name)
                target = root.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        (root/'audio-clock').chmod(0o755)
        sys.path.insert(0, str(root))
        sys.argv[0] = str(root/'player.py')
        runpy.run_path(str(root/'player.py'), run_name='__main__')


if __name__ == '__main__':
    main()
