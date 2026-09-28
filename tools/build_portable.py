"""在目标平台构建离线便携包，包含音乐、解释器和音频依赖。"""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform not in ('win32', 'linux'):
        raise SystemExit('请在 Windows 或 Linux 目标平台上构建；macOS 使用原有构建脚本。')
    if not (ROOT/'media/song.mp3').is_file():
        raise SystemExit('请先运行 tools/prepare_media.py 准备内嵌音乐。')
    if not (ROOT/'README-Windows.md').is_file():
        raise SystemExit('缺少运行说明。')
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--console',
            '--noupx', '--name', 'WorldExecuteMV', '--distpath', str(ROOT/'dist'),
            '--workpath', str(ROOT/'.build/pyinstaller'), '--specpath', str(ROOT/'.build'),
            '--collect-all', '_sounddevice_data', '--collect-all', '_soundfile_data']
    for name in ('config.json', 'lyrics.json', 'spectrum.json'):
        args += ['--add-data', f'{ROOT/name}{os.pathsep}.']
    args += ['--add-data', f'{ROOT/"media/song.mp3"}{os.pathsep}media', str(ROOT/'player.py')]
    subprocess.run(args, cwd=ROOT, check=True)
    folder = ROOT/'dist/WorldExecuteMV'
    shutil.copy2(ROOT/'README-Windows.md', folder/'README-Windows.md')
    if (ROOT/'media/provenance.json').is_file():
        shutil.copy2(ROOT/'media/provenance.json', folder/'media-provenance.json')
    if sys.platform == 'win32':
        (folder/'Play-MV.bat').write_text(
            '@echo off\r\ncd /d "%~dp0"\r\n"WorldExecuteMV.exe" %*\r\nif errorlevel 1 pause\r\n',
            encoding='ascii', newline='')
    # 随包保留已安装依赖的许可证文件和版本，不把开发环境一同复制。
    versions = {}
    for package in ('numpy', 'sounddevice', 'soundfile', 'cffi', 'pycparser', 'typing-extensions'):
        dist = importlib.metadata.distribution(package)
        versions[package] = dist.version
        for item in dist.files or ():
            parts = Path(str(item)).parts
            if any('license' in part.lower() or 'copying' in part.lower() for part in parts):
                source = Path(dist.locate_file(item))
                if source.is_file():
                    target = folder/'licenses'/package/Path(*[p for p in parts if p not in ('.', '..')])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    (folder/'dependency-versions.json').write_text(json.dumps(versions, indent=2)+'\n', encoding='utf-8')
    target_platform = 'windows' if sys.platform == 'win32' else 'linux'
    machine = platform.machine().lower()
    arch = 'x64' if machine in ('amd64', 'x86_64') else machine
    output = ROOT/'dist'/f'world-execute-mv-{target_platform}-{arch}.zip'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(folder.parent))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256').write_text(f'{digest}  {output.name}\n', encoding='ascii')
    print(json.dumps({'artifact': str(output), 'sha256': digest, 'dependencies': versions}, indent=2))


if __name__ == '__main__':
    main()
