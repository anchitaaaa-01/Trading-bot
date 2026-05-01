"""
orders.py
---------
High-level order placement logic.
Composes validation, the API client, and result formatting into a single
`place_order()` function that the CLI and interactive UI both call.
"""

import logging
from typing import Any, Optional

from .client import BinanceFuturesClient, BinanceAPIError, NetworkError
from .validators import validate_order_params, ValidationError

logger = logging.getLogger("trading_bot.orders")


# ── Result structure ─────────────────────────────────────────────────────────

class OrderResult:
    """
    Holds the outcome of an order placement attempt.

    Attributes:
        success:      True if the order was accepted by the exchange.
        order_id:     Binance order ID (if successful).
        status:       Order status string returned by Binance.
        executed_qty: Quantity that was filled.
        avg_price:    Average fill price (0 for unfilled orders).
        raw:          Full raw response dict from Binance.
        error:        Human-readable error message (if failed).
    """

    def __init__(
        self,
        success: bool,
        order_id: Optional[int] = None,
        status: Optional[str] = None,
        executed_qty: Optional[str] = None,
        avg_price: Optional[str] = None,
        raw: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        self.success = success
        self.order_id = order_id
        self.status = status
        self.executed_qty = executed_qty
        self.avg_price = avg_price
        self.raw = raw or {}
        self.error = error

    def __repr__(self) -> str:
        if self.success:
            return (
                f"OrderResult(success=True, order_id={self.order_id}, "
                f"status={self.status}, executed_qty={self.executed_qty}, "
                f"avg_price={self.avg_price})"
            )
        return f"OrderResult(success=False, error={self.error!r})"


# ── Core function ────────────────────────────────────────────────────────────

def place_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> OrderResult:
    """
    Validate inputs, call the Binance API, and return a structured result.

    Args:
        symbol:     Trading pair symbol (e.g., 'BTCUSDT').
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Number of contracts / coins.
        price:      Limit price in USDT (required for LIMIT orders).

    Returns:
        OrderResult instance with all relevant details.
    """
    # 1. Validate inputs
    try:
        params = validate_order_params(symbol, side, order_type, quantity, price)
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        return OrderResult(success=False, error=str(exc))

    # 2. Create client and place order
    try:
        client = BinanceFuturesClient()
        raw = client.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
        )
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        return OrderResult(success=False, error=str(exc))
    except ValidationError as exc:
        logger.error("Validation error from client layer: %s", exc)
        return OrderResult(success=False, error=str(exc))
    except BinanceAPIError as exc:
        logger.error("Binance API error: %s (HTTP %s, code %s)", exc, exc.status_code, exc.code)
        return OrderResult(success=False, error=str(exc))
    except NetworkError as exc:
        logger.error("Network error: %s", exc)
        return OrderResult(success=False, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error while placing order: %s", exc)
        return OrderResult(success=False, error=f"Unexpected error: {exc}")

    # 3. Parse response
    logger.info("Order placed successfully: %s", raw)
    return OrderResult(
        success=True,
        order_id=raw.get("orderId"),
        status=raw.get("status"),
        executed_qty=raw.get("executedQty", "0"),
        avg_price=raw.get("avgPrice", "0"),
        raw=raw,
    )
