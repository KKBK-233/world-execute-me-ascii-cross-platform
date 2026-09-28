"""跨平台 PCM 播放器：按样本跳转，并使用音频设备时钟同步画面。"""
import math
import threading
import time


class Audio:
    def __init__(self, path, *, device=None):
        try:
            import sounddevice as sd
            import soundfile as sf
        except (ImportError, OSError) as exc:
            raise RuntimeError('音频组件不可用，请安装 requirements.txt；Linux 还需要 PortAudio。') from exc
        # 一次解码本地音乐，避免 MP3 变码率跳转的累计偏差；不写解码缓存。
        self.samples, self.rate = sf.read(str(path), dtype='float32', always_2d=True)
        if not len(self.samples):
            raise RuntimeError('音频文件为空。')
        self.duration = len(self.samples) / self.rate
        self._lock = threading.RLock()
        self._cursor = 0
        self._position = 0.0
        self._playing = False
        self._anchor = None
        self._gain = .75
        self.error = ''
        self.underflows = 0
        self.last = time.monotonic()
        self._stream = None
        try:
            self._stream = sd.OutputStream(
                samplerate=self.rate, channels=self.samples.shape[1], dtype='float32',
                blocksize=0, latency='low', device=device, callback=self._callback)
            self._stream.start()
        except BaseException:
            if self._stream is not None:
                self._stream.close()
            raise

    def _callback(self, output, frames, clock, status):
        # 回调只拷贝已解码的样本；不执行文件读取、网络请求或日志输出。
        output.fill(0)
        self.last = time.monotonic()
        if status.output_underflow:
            self.underflows += 1
        try:
            with self._lock:
                if not self._playing:
                    return
                count = min(frames, len(self.samples) - self._cursor)
                if count:
                    # 每块重新锚定 DAC 时钟，设备短暂欠载后也不会永久漂移。
                    self._anchor = (self._cursor / self.rate, clock.outputBufferDacTime)
                    output[:count] = self.samples[self._cursor:self._cursor + count] * self._gain
                    self._cursor += count
        except Exception as exc:
            self.error = str(exc)
            output.fill(0)

    def _time_locked(self):
        if self._playing and self._anchor is not None:
            position, dac_time = self._anchor
            return min(self.duration, max(self._position,
                       position + self._stream.time - dac_time))
        return self._position

    @property
    def state(self):
        with self._lock:
            position = self._time_locked()
            if self._playing and position >= self.duration:
                self._playing = False
                self._position = self.duration
                self._anchor = None
            return {'time': position, 'duration': self.duration, 'playing': self._playing}

    def command(self, command):
        fields = command.split()
        if not fields:
            return
        with self._lock:
            name = fields[0]
            if name == 'play':
                if not self._playing and self._position < self.duration:
                    self._cursor = round(self._position * self.rate)
                    self._anchor = None
                    self._playing = True
            elif name == 'pause':
                self._position = self._time_locked()
                self._playing = False
                self._cursor = min(len(self.samples), round(self._position * self.rate))
                self._anchor = None
            elif name in ('seek', 'volume'):
                value = float(fields[1])
                if not math.isfinite(value):
                    raise ValueError('音频参数必须是有限数值。')
                if name == 'seek':
                    self._position = min(self.duration, max(0, value))
                    self._cursor = min(len(self.samples), round(self._position * self.rate))
                    self._anchor = None
                else:
                    self._gain = min(1, max(0, value))

    def check(self):
        if self.error:
            raise RuntimeError('音频回调失败：' + self.error)
        if not self._stream.active or time.monotonic() - self.last > 2:
            raise RuntimeError('音频输出已中断，请检查输出设备后重新启动。')

    def close(self):
        # 不持有回调锁关闭设备，避免退出时等待回调造成死锁。
        if self._stream is not None:
            self._stream.abort()
            self._stream.close()
            self._stream = None
