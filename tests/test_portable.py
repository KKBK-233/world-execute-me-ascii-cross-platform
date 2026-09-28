"""无需音频硬件的回归测试：按样本同步、资源安全和完整画面采样。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from audio_pcm import Audio
from player import Film
from tools.prepare_media import extract, BUNDLE_SHA256, AUDIO_SHA256


class FakeStream:
    def __init__(self, **kwargs):
        self.callback = kwargs['callback']
        self.time = 0.0
        self.active = False
        self.closed = False

    def start(self):
        self.active = True

    def abort(self):
        self.active = False

    def close(self):
        self.closed = True


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch('soundfile.read', return_value=(np.ones((1000, 2), dtype='float32'), 100)),
            patch('sounddevice.OutputStream', FakeStream),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.audio = Audio('unused.mp3')
        self.addCleanup(self.audio.close)

    def tick(self, dac=0, frames=100):
        out = np.zeros((frames, 2), dtype='float32')
        self.audio._callback(out, frames, types.SimpleNamespace(outputBufferDacTime=dac),
                             types.SimpleNamespace(output_underflow=False))
        return out

    def test_initial_silence_and_duration(self):
        self.assertEqual(self.audio.state, {'time': 0, 'duration': 10, 'playing': False})
        self.assertFalse(self.tick().any())

    def test_clock_uses_dac_time_not_queued_samples(self):
        self.audio.command('play')
        self.tick(dac=.1)
        self.audio._stream.time = .6
        self.assertAlmostEqual(self.audio.state['time'], .5)

    def test_pause_freezes_and_resume_keeps_position(self):
        self.audio.command('play')
        self.tick(dac=.1)
        self.audio._stream.time = .6
        self.audio.command('pause')
        self.audio._stream.time = 5
        self.assertEqual(self.audio.state['time'], .5)
        self.assertFalse(self.tick().any())
        self.audio.command('play')
        self.tick(dac=5)
        self.audio._stream.time = 5.25
        self.assertAlmostEqual(self.audio.state['time'], .75)

    def test_seek_while_paused(self):
        self.audio.command('seek 4.25')
        self.assertEqual(self.audio.state['time'], 4.25)
        self.assertFalse(self.audio.state['playing'])
        self.assertEqual(self.audio._cursor, 425)

    def test_seek_while_playing_resets_clock(self):
        self.audio.command('play')
        self.tick()
        self.audio.command('seek 7')
        self.tick(dac=1)
        self.audio._stream.time = 1.2
        self.assertAlmostEqual(self.audio.state['time'], 7.2)
        self.audio.command('seek 1')
        self.assertEqual(self.audio.state['time'], 1)

    def test_eof_and_restart(self):
        self.audio.command('seek 9.5')
        self.audio.command('play')
        out = self.tick(dac=0)
        self.assertTrue(out[:50].any())
        self.assertFalse(out[50:].any())
        self.audio._stream.time = .5
        self.assertEqual(self.audio.state, {'time': 10, 'duration': 10, 'playing': False})
        self.audio.command('seek 0')
        self.audio.command('play')
        self.assertTrue(self.audio.state['playing'])

    def test_volume_and_clamping(self):
        self.audio.command('play')
        self.audio.command('volume 0')
        self.assertFalse(self.tick().any())
        self.audio.command('volume 5')
        self.assertEqual(self.tick()[0, 0], 1)
        self.audio.command('seek -10')
        self.assertEqual(self.audio.state['time'], 0)
        self.audio.command('seek 999')
        self.assertEqual(self.audio.state['time'], 10)

    def test_non_finite_rejected(self):
        for command in ('seek nan', 'seek inf', 'volume nan'):
            with self.assertRaises(ValueError):
                self.audio.command(command)

    def test_device_failure_detected(self):
        self.audio._stream.active = False
        with self.assertRaises(RuntimeError):
            self.audio.check()

    def test_close_idempotent(self):
        stream = self.audio._stream
        self.audio.close()
        self.audio.close()
        self.assertTrue(stream.closed)

    def test_start_failure_closes_stream(self):
        with patch.object(FakeStream, 'start', side_effect=RuntimeError('device unavailable')):
            with patch.object(FakeStream, 'close') as close:
                with self.assertRaises(RuntimeError):
                    Audio('unused.mp3')
                close.assert_called_once()


class ResourceTests(unittest.TestCase):
    def test_corrupt_bundle_never_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'media/song.mp3'
            with self.assertRaises(ValueError):
                extract(b'not an archive', target)
            self.assertFalse(target.parent.exists())

    @unittest.skipUnless((ROOT/'world-execute-mv.pyz').exists(), '未提供原版发布包')
    def test_verified_extraction_and_no_overwrite(self):
        data = (ROOT/'world-execute-mv.pyz').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), BUNDLE_SHA256)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'song.mp3'
            extract(data, target)
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), AUDIO_SHA256)
            extract(data, target)
            target.write_bytes(b'keep my music')
            with self.assertRaises(ValueError):
                extract(data, target)
            self.assertEqual(target.read_bytes(), b'keep my music')

    def test_snapshot_from_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT/'player.py'), '--snapshot',
                                     '67.3', '--plain'], cwd=folder, capture_output=True,
                                    text=True, encoding='utf-8', timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('If I can make you happy', result.stdout)
            self.assertIn('如果我能让你快乐', result.stdout)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_cli_rejects_invalid_arguments(self):
        for args in (['--snapshot', 'nan'], ['--fps', '0'], ['--width', '-1'], ['--volume', '2']):
            result = subprocess.run([sys.executable, str(ROOT/'player.py'), *args],
                                    capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 2)

    def test_film_samples_all_sections(self):
        film = Film()
        for t in range(213):
            with self.subTest(time=t):
                canvas = film.render(float(t), 127, 44)
                self.assertEqual(len(canvas.cells), 44)
                self.assertTrue(canvas.ansi().endswith('\x1b[0m'))

    def test_small_window_help_and_title(self):
        film = Film()
        for size in ((1, 1), (63, 23), (64, 24), (239, 85)):
            for t in (0, 15.9, 17.9, 29.7, 159.85, 211.9):
                film.render(t, *size, help_on=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
