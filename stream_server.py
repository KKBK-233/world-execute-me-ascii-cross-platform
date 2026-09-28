#!/usr/bin/env python3
"""只读 ANSI 画面服务：让终端通过 curl 直接观看，不接收命令或播放音频。"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socket
import threading
import time

from player import Film


class StreamServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 8

    def __init__(self, address, *, width=100, height=32, fps=8, max_clients=4,
                 duration=None):
        super().__init__(address, StreamHandler)
        self.film = Film()
        self.width = width
        self.height = height
        self.fps = fps
        self.slots = threading.BoundedSemaphore(max_clients)
        self.connections = threading.BoundedSemaphore(max_clients + 4)
        self.duration = self.film.config['duration'] if duration is None else duration

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(3)
        return request, address

    def process_request(self, request, client_address):
        # 在创建线程前限制连接数；空闲连接也不能无限占用 VPS 资源。
        if not self.connections.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.connections.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.connections.release()


class StreamHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def do_GET(self):
        if self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', '3')
            self.end_headers()
            self.wfile.write(b'ok\n')
            return
        if self.path != '/':
            self.send_error(404)
            return
        if not self.server.slots.acquire(blocking=False):
            self.send_error(503, 'Too many viewers')
            return
        try:
            self._stream()
        finally:
            self.server.slots.release()

    def _stream(self):
        # 每次连接从影片开头播放，使用单调时钟保持帧与时间轴同步。
        self.connection.settimeout(3)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Connection', 'close')
        self.end_headers()
        started = time.monotonic()
        frame = 0
        try:
            self.wfile.write(b'\x1b[2J')
            while True:
                elapsed = time.monotonic() - started
                if elapsed >= self.server.duration:
                    break
                canvas = self.server.film.render(
                    elapsed, self.server.width, self.server.height,
                    view_only=True)
                self.wfile.write(canvas.ansi().encode('utf-8'))
                self.wfile.flush()
                frame += 1
                deadline = started + frame / self.server.fps
                time.sleep(max(0, deadline - time.monotonic()))
            self.wfile.write(b'\x1b[0m\r\n')
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            pass

    def log_message(self, format, *args):
        # 公网请求只记录常规 HTTP 状态，不把客户端内容当作命令处理。
        super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description='world.execute(me); 只读终端画面服务')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=41090)
    parser.add_argument('--width', type=int, default=100)
    parser.add_argument('--height', type=int, default=32)
    parser.add_argument('--fps', type=int, default=8)
    parser.add_argument('--max-clients', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('--port 必须在 1–65535 之间')
    if not 64 <= args.width <= 160 or not 24 <= args.height <= 60:
        parser.error('画面尺寸必须在 64–160 列、24–60 行内')
    if not 1 <= args.fps <= 12 or not 1 <= args.max_clients <= 8:
        parser.error('帧率必须在 1–12，连接数必须在 1–8')
    with StreamServer((args.host, args.port), width=args.width,
                      height=args.height, fps=args.fps,
                      max_clients=args.max_clients) as server:
        server.serve_forever(poll_interval=.2)


if __name__ == '__main__':
    main()
