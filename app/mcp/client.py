import subprocess
import json
import uuid
import sys
import threading
import time


class MCPClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._start_server()
            return cls._instance

    def _start_server(self):
        self.proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "app.mcp.server"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # wait for server to be ready
        time.sleep(0.3)

        if self.proc.poll() is not None:
            err = self.proc.stderr.read()
            raise RuntimeError(f"MCP failed to start:\n{err}")

    def call_tool(self, tool_name: str, args: dict):
        request = {
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            }
        }

        self.proc.stdin.write(json.dumps(request) + "\n")
        self.proc.stdin.flush()

        response = json.loads(self.proc.stdout.readline())
        return response["result"]
