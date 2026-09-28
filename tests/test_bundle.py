"""Check actual built resources and execution outside the project directory."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT/'dist/world-execute-mv.pyz'


class BundleTests(unittest.TestCase):
    def test_embedded_resources_match_source(self):
        with zipfile.ZipFile(BUNDLE) as archive:
            manifest = json.loads(archive.read('bundle-manifest.json'))
            self.assertIn('media/song.mp3', manifest['files'])
            for name, digest in manifest['files'].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                self.assertEqual(archive.read(name), (ROOT/name).read_bytes())
            config = json.loads(archive.read('config.json'))
            self.assertEqual(config['audio'], 'media/song.mp3')
            self.assertFalse(any(name.lower().endswith(('.mp4', '.png', '.jpg')) for name in archive.namelist()))

    def test_runs_from_an_empty_directory_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            work = base/'unrelated working directory'; work.mkdir()
            scratch = base/'scratch'; scratch.mkdir()
            env = dict(os.environ, TMPDIR=str(scratch))
            for t, expected in [(67.3, 'If I can make you happy'), (124.2, 'Then maybe'),
                                (159.85, 'TROIS'), (183.2, 'Question me')]:
                result = subprocess.run([sys.executable, str(BUNDLE), '--snapshot', str(t),
                                         '--plain', '--width', '125', '--height', '45'],
                                        cwd=work, env=env, capture_output=True, text=True, check=True)
                self.assertIn(expected, result.stdout)
                self.assertEqual(list(work.iterdir()), [])
                self.assertEqual(list(scratch.iterdir()), [])

    def test_corrupt_resource_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder)/'corrupt.pyz'
            with zipfile.ZipFile(BUNDLE) as original, zipfile.ZipFile(bad, 'w') as changed:
                for name in original.namelist():
                    data = original.read(name)
                    changed.writestr(name, b'{}' if name == 'config.json' else data)
            result = subprocess.run([sys.executable, str(bad), '--snapshot', '67.3', '--plain'],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('资源校验失败', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
