"""
app.py
------
Flask application entrypoint for Vercel deployment.

Vercel automatically detects this file and the `app` instance when
Flask is listed in requirements.txt. All routes are proxied through
the /api prefix by vercel.json.

Routes
------
GET  /                  Landing page with API documentation
GET  /api/health        Service liveness probe
POST /api/order         Place a Binance Futures Testnet order
"""

import os
import sys
from flask import Flask, request, jsonify

# Ensure the package root is importable (needed when Vercel invokes app.py directly)
_ROOT = os.path.dirname(__file__)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from trading_bot.logging_config import setup_logging
from trading_bot.orders import place_order
from trading_bot.validators import SUPPORTED_SYMBOLS

setup_logging()

app = Flask(__name__)

# ── Landing page ─────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    """Return an HTML landing page with API usage docs."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Binance Futures Trading Bot API</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f1117; color: #e2e8f0; padding: 2rem; }
    h1   { font-size: 1.8rem; color: #f0b429; margin-bottom: .4rem; }
    h2   { font-size: 1.1rem; color: #63b3ed; margin: 1.6rem 0 .5rem; }
    p    { color: #a0aec0; line-height: 1.6; margin-bottom: .8rem; }
    .badge { display: inline-block; background: #1a202c; border: 1px solid #2d3748;
             padding: .15rem .5rem; border-radius: 4px; font-size: .75rem;
             color: #48bb78; font-family: monospace; margin-right: .3rem; }
    .card { background: #1a202c; border: 1px solid #2d3748; border-radius: 8px;
            padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
    pre  { background: #0d1117; border: 1px solid #2d3748; border-radius: 6px;
           padding: 1rem; overflow-x: auto; font-size: .82rem; color: #e2e8f0; }
    .method-post { color: #68d391; font-weight: 700; }
    .method-get  { color: #63b3ed; font-weight: 700; }
    .url { color: #d6bcfa; }
    footer { margin-top: 2.5rem; color: #4a5568; font-size: .8rem; }
  </style>
</head>
<body>
  <h1>&#x1F916; Binance Futures Testnet Trading Bot API</h1>
  <p>Serverless REST API deployed on Vercel. All orders target the
     <strong>Binance Futures Testnet</strong> — no real funds.</p>

  <div class="badge">Python 3.12</div>
  <div class="badge">Flask</div>
  <div class="badge">Vercel Serverless</div>
  <div class="badge">Testnet Only</div>

  <h2>Endpoints</h2>

  <div class="card">
    <p><span class="method-get">GET</span> <span class="url">/api/health</span></p>
    <p>Returns service status and supported configuration.</p>
  </div>

  <div class="card">
    <p><span class="method-post">POST</span> <span class="url">/api/order</span></p>
    <p>Place a MARKET or LIMIT futures order.</p>

    <h2>Request body</h2>
    <pre>{
  "symbol":     "BTCUSDT",
  "side":       "BUY",
  "order_type": "MARKET",
  "quantity":   0.01,
  "price":      62000.00   // required for LIMIT orders only
}</pre>

    <h2>Success response (200)</h2>
    <pre>{
  "success":      true,
  "order_id":     4917823501,
  "status":       "FILLED",
  "executed_qty": "0.01",
  "avg_price":    "62148.30"
}</pre>

    <h2>Error response (400 / 500)</h2>
    <pre>{
  "success": false,
  "error":   "Unsupported symbol 'FAKECOIN'. Supported symbols: ..."
}</pre>
  </div>

  <h2>Supported Symbols</h2>
  <div class="card">
    <p>BTCUSDT &nbsp; ETHUSDT &nbsp; BNBUSDT &nbsp; XRPUSDT &nbsp; SOLUSDT</p>
    <p>ADAUSDT &nbsp; DOGEUSDT &nbsp; MATICUSDT &nbsp; LTCUSDT &nbsp; DOTUSDT</p>
  </div>

  <h2>Quick Test (curl)</h2>
  <pre>curl -X POST https://YOUR_DEPLOYMENT.vercel.app/api/order \\
  -H "Content-Type: application/json" \\
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "order_type": "MARKET",
    "quantity": 0.01
  }'</pre>

  <footer>Binance Futures Testnet Trading Bot &mdash; Vercel Deployment</footer>
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """Return service status and configuration metadata."""
    return jsonify({
        "status": "ok",
        "service": "binance-futures-trading-bot",
        "testnet": "https://testnet.binancefuture.com",
        "version": "1.0.0",
        "endpoints": {
            "place_order": "POST /api/order",
            "health": "GET  /api/health",
        },
        "supported_symbols": sorted(SUPPORTED_SYMBOLS),
        "order_types": ["MARKET", "LIMIT"],
        "sides": ["BUY", "SELL"],
    })


# ── Order placement ───────────────────────────────────────────────────────────

REQUIRED_FIELDS = ("symbol", "side", "order_type", "quantity")


@app.route("/api/order", methods=["POST"])
def order():
    """
    Place a Binance Futures Testnet order.

    Reads JSON body, validates, and calls the shared order placement logic.
    """
    body = request.get_json(force=True, silent=True) or {}

    # Validate required fields
    missing = [f for f in REQUIRED_FIELDS if f not in body]
    if missing:
        return jsonify({
            "success": False,
            "error": f"Missing required field(s): {', '.join(missing)}",
        }), 400

    # Coerce numeric fields
    try:
        quantity = float(body["quantity"])
        price = float(body["price"]) if "price" in body else None
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": "Fields 'quantity' and 'price' must be numeric.",
        }), 400

    result = place_order(
        symbol=str(body["symbol"]),
        side=str(body["side"]),
        order_type=str(body["order_type"]),
        quantity=quantity,
        price=price,
    )

    if result.success:
        return jsonify({
            "success": True,
            "order_id": result.order_id,
            "status": result.status,
            "executed_qty": result.executed_qty,
            "avg_price": result.avg_price,
            "raw": result.raw,
        }), 200

    # Client vs server error heuristic
    error_lower = (result.error or "").lower()
    client_keywords = ("invalid", "unsupported", "required", "must be",
                       "below minimum", "credentials", "api key", "api error -")
    status_code = 400 if any(kw in error_lower for kw in client_keywords) else 500
    return jsonify({"success": False, "error": result.error}), status_code


# ── Local dev runner ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
