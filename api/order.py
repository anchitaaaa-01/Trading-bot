"""
api/order.py
------------
Vercel serverless function — place a Binance Futures Testnet order.

Endpoint: POST /api/order

Request body (JSON):
    {
        "symbol":     "BTCUSDT",
        "side":       "BUY" | "SELL",
        "order_type": "MARKET" | "LIMIT",
        "quantity":   0.01,
        "price":      62000.00   // required for LIMIT orders only
    }

Success response (200):
    {
        "success":      true,
        "order_id":     4917823501,
        "status":       "FILLED",
        "executed_qty": "0.01",
        "avg_price":    "62148.30",
        "raw":          { ...full Binance response... }
    }

Error response (400 / 500):
    {
        "success": false,
        "error":   "human-readable message"
    }
"""

from http.server import BaseHTTPRequestHandler
from ._utils import send_json, read_json_body, _ROOT  # noqa: F401 (ensures sys.path patched)

from trading_bot.logging_config import setup_logging
from trading_bot.orders import place_order

setup_logging()

REQUIRED_FIELDS = ("symbol", "side", "order_type", "quantity")


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler for order placement."""

    def do_POST(self) -> None:  # noqa: N802
        """Handle POST /api/order — validate body and place order."""
        body = read_json_body(self)

        # Check required fields
        missing = [f for f in REQUIRED_FIELDS if f not in body]
        if missing:
            send_json(self, 400, {
                "success": False,
                "error": f"Missing required field(s): {', '.join(missing)}",
            })
            return

        # Coerce quantity / price to float
        try:
            quantity = float(body["quantity"])
            price = float(body["price"]) if "price" in body else None
        except (ValueError, TypeError):
            send_json(self, 400, {
                "success": False,
                "error": "Fields 'quantity' and 'price' must be numeric.",
            })
            return

        result = place_order(
            symbol=str(body["symbol"]),
            side=str(body["side"]),
            order_type=str(body["order_type"]),
            quantity=quantity,
            price=price,
        )

        if result.success:
            send_json(self, 200, {
                "success": True,
                "order_id": result.order_id,
                "status": result.status,
                "executed_qty": result.executed_qty,
                "avg_price": result.avg_price,
                "raw": result.raw,
            })
        else:
            # Distinguish client errors (4xx) from unexpected server errors (5xx)
            status_code = 400 if _is_client_error(result.error) else 500
            send_json(self, status_code, {
                "success": False,
                "error": result.error,
            })

    def do_GET(self) -> None:  # noqa: N802
        """Return a helpful message for accidental GET requests."""
        send_json(self, 405, {
            "error": "Method not allowed. Use POST /api/order with a JSON body.",
            "example": {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 0.01,
            },
        })

    def log_message(self, fmt, *args) -> None:  # noqa: N802
        """Suppress default BaseHTTPRequestHandler stdout logging."""


def _is_client_error(error: str | None) -> bool:
    """Heuristic: treat validation and auth errors as 4xx, others as 5xx."""
    if not error:
        return False
    client_keywords = ("invalid", "unsupported", "required", "must be", "below minimum",
                       "credentials", "api key", "api error -")
    return any(kw in error.lower() for kw in client_keywords)
