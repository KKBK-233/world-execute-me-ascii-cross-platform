"""验证公开画面服务的只读路由、连接上限和终端输出。"""
from http.client import HTTPConnection
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stream_server import StreamServer


class StreamServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = StreamServer(('127.0.0.1', 0), fps=8, duration=.2,
                                  max_clients=1)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path):
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            connection.request('GET', path)
            response = connection.getresponse()
            return response.status, response.read(), response.getheader('Content-Type')
        finally:
            connection.close()

    def test_health_and_unknown_path(self):
        self.assertEqual(self.request('/healthz')[:2], (200, b'ok\n'))
        self.assertEqual(self.request('/secret')[0], 404)

    def test_terminal_stream_is_silent_and_read_only(self):
        status, data, content_type = self.request('/')
        self.assertEqual(status, 200)
        self.assertEqual(content_type, 'text/plain; charset=utf-8')
        self.assertTrue(data.startswith(b'\x1b[2J\x1b[H'))
        self.assertIn(b'No audio', data)
        self.assertTrue(data.endswith(b'\x1b[0m\r\n'))

    def test_connection_limit(self):
        self.assertTrue(self.server.slots.acquire(False))
        try:
            self.assertEqual(self.request('/')[0], 503)
        finally:
            self.server.slots.release()


if __name__ == '__main__':
    unittest.main()
