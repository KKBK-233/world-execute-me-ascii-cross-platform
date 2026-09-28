"""统一 Windows 与 POSIX 的终端输入、尺寸和退出恢复。"""
import os
import sys
import time


class Terminal:
    def __enter__(self):
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise RuntimeError('请在交互式终端中运行，或使用 --snapshot 导出画面。')
        self._restore = None
        if os.name == 'nt':
            self._windows_setup()
        else:
            import termios
            import tty
            self._restore = termios.tcgetattr(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
        try:
            sys.stdout.write('\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[2J')
            sys.stdout.flush()
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def _windows_setup(self):
        # 只修改本次控制台句柄，退出时还原；不修改注册表或系统配置。
        import ctypes
        from ctypes import wintypes
        self._kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self._kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        self._kernel.GetStdHandle.restype = wintypes.HANDLE
        self._kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self._kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._handle = self._kernel.GetStdHandle(-11 & 0xffffffff)
        mode = wintypes.DWORD()
        if not self._kernel.GetConsoleMode(self._handle, ctypes.byref(mode)):
            raise RuntimeError('无法访问控制台，请使用 Windows Terminal 或 PowerShell。')
        self._restore = mode.value
        if not self._kernel.SetConsoleMode(self._handle, mode.value | 0x0004):
            raise RuntimeError('当前终端不支持 ANSI 显示，请使用 Windows Terminal。')

    def size(self):
        try:
            return os.get_terminal_size(sys.stdout.fileno())
        except OSError:
            return (100, 36)

    def read(self, timeout):
        if os.name != 'nt':
            import select
            if select.select([sys.stdin], [], [], max(0, timeout))[0]:
                return os.read(sys.stdin.fileno(), 128).decode('utf-8', errors='ignore')
            return ''
        import msvcrt
        deadline = time.monotonic() + max(0, timeout)
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getwch()
                if key in ('\x00', '\xe0'):
                    return {'K': '\x1b[D', 'M': '\x1b[C'}.get(msvcrt.getwch(), '')
                return key
            if time.monotonic() >= deadline:
                return ''
            time.sleep(min(.005, max(0, deadline - time.monotonic())))

    def __exit__(self, *_):
        try:
            sys.stdout.write('\x1b[0m\x1b[?7h\x1b[?25h\x1b[?1049l')
            sys.stdout.flush()
        finally:
            if self._restore is not None:
                if os.name == 'nt':
                    self._kernel.SetConsoleMode(self._handle, self._restore)
                else:
                    import termios
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._restore)
