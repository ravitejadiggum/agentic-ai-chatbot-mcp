from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
    JSONResponse
)
from fastapi.staticfiles import StaticFiles

import subprocess
import sys
import json
import threading

# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
app = FastAPI(
    title="Agentic AI Chatbot (Streaming)",
    version="1.0.0"
)

# -------------------------------------------------
# Serve static UI
# -------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")


# -------------------------------------------------
# Agent runner process
# -------------------------------------------------
agent_process = None
lock = threading.Lock()


def start_agent():
    global agent_process
    agent_process = subprocess.Popen(
        [sys.executable, "agent_runner.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )


start_agent()


# -------------------------------------------------
# Streaming chat endpoint (GET – SSE)
# -------------------------------------------------
@app.get("/chat-stream")
def chat_stream(message: str):

    def event_generator():
        with lock:
            try:
                # Send message to agent runner
                agent_process.stdin.write(
                    json.dumps({"message": message}) + "\n"
                )
                agent_process.stdin.flush()

                # Read streaming output
                while True:
                    line = agent_process.stdout.readline()
                    if not line:
                        break

                    data = json.loads(line)

                    if "stream" in data:
                        yield f"data: {data['stream']}\n\n"

                    if "end" in data:
                        break

            except BrokenPipeError:
                start_agent()
                yield "data: [Agent restarted]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# -------------------------------------------------
# Health check
# -------------------------------------------------
@app.get("/health")
def health():
    return {"status": "running"}
