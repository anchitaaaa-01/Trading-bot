"""
api/_utils.py
-------------
Shared helpers for Vercel serverless handlers.
Prefixed with _ so Vercel does NOT turn this file into an HTTP endpoint.
"""

import json
import sys
import os

# Make the project root importable from within the api/ directory
_ROOT = os.path.dirname(os.path.dirname(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def send_json(handler, status: int, data: dict) -> None:
    """Write a JSON response through a BaseHTTPRequestHandler."""
    body = json.dumps(data, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(handler) -> dict:
    """Read and parse the JSON request body."""
    length = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
