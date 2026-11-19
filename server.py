# -*- coding: utf-8 -*-
"""数码资产记录工具 - 本地服务

负责：
1. 提供静态页面（index.html）
2. 提供数据读写接口，数据自动保存到同目录下的 data.json 文件

用法：python server.py   （或双击 启动.bat）
默认端口：8765
"""
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8765
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
INDEX_FILE = os.path.join(BASE_DIR, "index.html")


def load_data():
    """读取数据文件，不存在或损坏时返回空列表。"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_data(data):
    """将数据写入 data.json。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404, "File not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/data":
            self._send_json(load_data())
        elif path == "/" or path == "/index.html":
            self._send_file(INDEX_FILE, "text/html; charset=utf-8")
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/data":
            length = int(self.headers.get("Content-Length", 0))
            try:
                raw = self.rfile.read(length).decode("utf-8")
                data = json.loads(raw)
                if not isinstance(data, list):
                    raise ValueError("data must be a list")
                save_data(data)
                self._send_json({"ok": True, "count": len(data)})
            except (json.JSONDecodeError, ValueError) as e:
                self._send_json({"ok": False, "error": str(e)}, status=400)
        else:
            self.send_error(404, "Not found")

    def log_message(self, fmt, *args):
        # 静默访问日志，避免控制台刷屏
        pass


def main():
    try:
        server = HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"[错误] 端口 {PORT} 已被占用，可能服务已在运行。")
        sys.exit(1)

    print("=" * 46)
    print("  数码资产记录工具 已启动")
    print(f"  请在浏览器打开: http://127.0.0.1:{PORT}")
    print(f"  数据文件: {DATA_FILE}")
    print("  按 Ctrl+C 停止服务")
    print("=" * 46)

    # 延迟自动打开浏览器
    def _open_browser():
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    threading.Timer(1.0, _open_browser).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
        server.server_close()


if __name__ == "__main__":
    main()
