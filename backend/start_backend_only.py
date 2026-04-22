#!/usr/bin/env python
"""
Start only the FastAPI backend (no MCP server)
Use this when you want to run just the API without the MCP components
"""

import subprocess
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

cmd = [
    sys.executable,
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
    "--reload",
    "--log-level",
    "info"
]

print("🚀 Starting FastAPI Backend on http://127.0.0.1:8000...")
print("Press Ctrl+C to stop\n")

subprocess.run(cmd, cwd=str(backend_dir))
