"""使用真实 ConPTY 与输出设备做静音冒烟；不需要 GUI，不改变系统音量。"""
import argparse
from collections import deque
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def run_case(command, args, actions, expected, timeout=30):
    from winpty import PtyProcess
    with tempfile.TemporaryDirectory(prefix='mv-smoke-') as work:
        report = Path(work)/'report.json'
        process = PtyProcess.spawn(command + ['--volume', '0', '--report', str(report), *args],
                                   cwd=work, dimensions=(44, 128))
        chunks = deque(maxlen=200)
        def read_output():
            try:
                while True:
                    chunks.append(process.read(8192))
            except EOFError:
                pass
        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        try:
            deadline = time.monotonic() + 15
            while '\x1b[0m' not in ''.join(chunks):
                if not process.isalive() or time.monotonic() > deadline:
                    raise RuntimeError('启动失败：' + ''.join(chunks)[-2000:])
                time.sleep(.05)
            for delay, keys in actions:
                time.sleep(delay)
                process.write(keys)
            deadline = time.monotonic() + timeout
            while process.isalive() and time.monotonic() < deadline:
                time.sleep(.1)
            if process.isalive():
                raise RuntimeError('播放器未在期限内退出。')
            reader.join(timeout=3)
            output = ''.join(chunks)
            if process.exitstatus != 0:
                raise RuntimeError(f'退出码 {process.exitstatus}：' + output[-2000:])
            result = json.loads(report.read_text(encoding='utf-8'))
            if not expected[0] <= result['last_time'] <= expected[1]:
                raise AssertionError(result)
            if '\x1b[?25h' not in output or '\x1b[?1049l' not in output:
                raise AssertionError('缺少终端恢复序列。')
            return result
        finally:
            if process.isalive():
                process.terminate(force=True)
            process.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--full', action='store_true', help='以真实速度静音播放完整音乐')
    parser.add_argument('--save', type=Path)
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise SystemExit('此冒烟脚本只在 Windows 上运行。')
    command = [str(args.exe.resolve())] if args.exe else [sys.executable, str(ROOT/'player.py')]
    cases = {}
    if args.full:
        cases['full_song'] = run_case(command, ['--autoplay', '--stop-after', '211.9'],
                                      [], (211.9, 212), timeout=240)
    else:
        cases['autoplay'] = run_case(command, ['--autoplay', '--stop-after', '2'], [], (2, 2.3))
        cases['pause_resume'] = run_case(command, [], [(0, ' '), (1.6, ' '), (1.6, 'q')], (1.2, 2.0))
        cases['seek_right'] = run_case(command, ['--start', '20', '--paused'],
                                      [(.2, '\x1b[C'), (.3, 'q')], (24.9, 25.1))
        cases['seek_left'] = run_case(command, ['--start', '20', '--paused'],
                                     [(.2, '\x1b[D'), (.3, 'q')], (14.9, 15.1))
        cases['chapter'] = run_case(command, [], [(.2, '5'), (.8, 'q')], (177.2, 178.5))
        cases['restart_help'] = run_case(command, ['--start', '100', '--paused'],
                                        [(.2, 'h'), (.2, 'r'), (.8, 'q')], (0, 1.5))
        cases['ctrl_c'] = run_case(command, [], [(.2, '\x03')], (0, .1))
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(json.dumps(cases, indent=2), encoding='utf-8')
    print(json.dumps({name: {k: v for k, v in result.items() if k != 'samples'}
                      for name, result in cases.items()}, indent=2))


if __name__ == '__main__':
    main()
