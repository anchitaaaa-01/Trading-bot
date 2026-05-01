"""
api/health.py
-------------
Vercel serverless function — liveness / readiness probe.

Endpoint: GET /api/health

Response (200):
    {
        "status":    "ok",
        "service":   "binance-futures-trading-bot",
        "testnet":   "https://testnet.binancefuture.com",
        "version":   "1.0.0",
        "endpoints": {
            "place_order": "POST /api/order",
            "health":      "GET  /api/health"
        }
    }
"""

from http.server import BaseHTTPRequestHandler
from ._utils import send_json  # noqa: F401 (ensures sys.path is patched)

SERVICE_INFO = {
    "status": "ok",
    "service": "binance-futures-trading-bot",
    "testnet": "https://testnet.binancefuture.com",
    "version": "1.0.0",
    "endpoints": {
        "place_order": "POST /api/order",
        "health": "GET  /api/health",
    },
    "supported_symbols": [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
        "ADAUSDT", "DOGEUSDT", "MATICUSDT", "LTCUSDT", "DOTUSDT",
    ],
    "order_types": ["MARKET", "LIMIT"],
    "sides": ["BUY", "SELL"],
}


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler for the health-check endpoint."""

    def do_GET(self) -> None:  # noqa: N802
        """Return service metadata and supported configuration."""
        send_json(self, 200, SERVICE_INFO)

    def log_message(self, fmt, *args) -> None:  # noqa: N802
        """Suppress default BaseHTTPRequestHandler stdout logging."""
