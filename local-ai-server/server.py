"""
BDX-Mini Droid — Local AI HTTP & Simulator Server
Chạy tại: http://localhost:8080
Kết nối trực tiếp giao diện 3D + OLED Simulator với bộ não Ollama (qwen2.5:3b)
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Thêm đường dẫn local-ai-server vào sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from llm_agent.bdx_brain import ask_bdx_brain, smarthome_state

WEB_SIM_DIR = os.path.join(BASE_DIR, "web_simulator")


class BDXRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_SIM_DIR, **kwargs)

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json({
                "status": "online",
                "model": "qwen2.5:3b",
                "smarthome_state": smarthome_state
            })
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            req_data = json.loads(raw_body)
            user_text = req_data.get("message", "").strip()
            if not user_text:
                self._send_json({"error": "Empty message"}, 400)
                return

            result = ask_bdx_brain(user_text)
            self._send_json(result)
            return

        self._send_json({"error": "Not found"}, 404)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    port = 8080
    print("============================================================")
    print(f"[BDX-Mini] Local AI Server running at: http://localhost:{port}")
    print("[BDX-Mini] AI Brain: Ollama (qwen2.5:3b @ http://localhost:11434)")
    print("============================================================")
    server = HTTPServer(("0.0.0.0", port), BDXRequestHandler)
    server.serve_forever()
