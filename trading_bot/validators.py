"""
validators.py
-------------
Input validation logic for order parameters.
Validates symbol, side, order type, quantity, and price.
"""

import logging
from typing import Optional

logger = logging.getLogger("trading_bot.validators")

# ── Symbol constants ────────────────────────────────────────────────────────
SUPPORTED_SYMBOLS: set[str] = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
    "ADAUSDT", "DOGEUSDT", "MATICUSDT", "LTCUSDT", "DOTUSDT",
}

# ── BTCUSDT typical futures constraints ────────────────────────────────────
MIN_QTY: float = 0.001
STEP_SIZE: float = 0.001
MIN_NOTIONAL: float = 5.0        # USD notional minimum

VALID_SIDES: set[str] = {"BUY", "SELL"}
VALID_ORDER_TYPES: set[str] = {"MARKET", "LIMIT"}


class ValidationError(ValueError):
    """Raised when order parameter validation fails."""


def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol.

    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT').

    Returns:
        Upper-cased symbol string.

    Raises:
        ValidationError: If the symbol is not supported.
    """
    symbol = symbol.strip().upper()
    if symbol not in SUPPORTED_SYMBOLS:
        msg = (
            f"Unsupported symbol '{symbol}'. "
            f"Supported symbols: {', '.join(sorted(SUPPORTED_SYMBOLS))}"
        )
        logger.warning(msg)
        raise ValidationError(msg)
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: 'BUY' or 'SELL'.

    Returns:
        Upper-cased side string.

    Raises:
        ValidationError: If side is not BUY or SELL.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        msg = f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}"
        logger.warning(msg)
        raise ValidationError(msg)
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: 'MARKET' or 'LIMIT'.

    Returns:
        Upper-cased order type string.

    Raises:
        ValidationError: If order type is not MARKET or LIMIT.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        msg = (
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(VALID_ORDER_TYPES)}"
        )
        logger.warning(msg)
        raise ValidationError(msg)
    return order_type


def validate_quantity(quantity: float) -> float:
    """
    Validate order quantity against minimum quantity and step size constraints.

    Args:
        quantity: Order quantity (number of contracts/coins).

    Returns:
        Validated quantity rounded to step size precision.

    Raises:
        ValidationError: If quantity is below minimum or not a multiple of step size.
    """
    if quantity <= 0:
        msg = f"Quantity must be positive, got {quantity}"
        logger.warning(msg)
        raise ValidationError(msg)

    if quantity < MIN_QTY:
        msg = f"Quantity {quantity} is below minimum allowed quantity {MIN_QTY}"
        logger.warning(msg)
        raise ValidationError(msg)

    # Round to step-size precision to avoid floating-point drift
    precision = len(str(STEP_SIZE).rstrip("0").split(".")[-1])
    rounded = round(round(quantity / STEP_SIZE) * STEP_SIZE, precision)

    if rounded != round(quantity, precision):
        logger.debug(
            "Quantity %.8f rounded to nearest step size: %.8f", quantity, rounded
        )

    return rounded


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate limit price.

    Args:
        price: Limit price in USDT. May be None for MARKET orders.
        order_type: 'MARKET' or 'LIMIT'.

    Returns:
        Validated price (or None for MARKET orders).

    Raises:
        ValidationError: If price is missing for LIMIT orders or invalid.
    """
    if order_type == "LIMIT":
        if price is None:
            msg = "Price is required for LIMIT orders."
            logger.warning(msg)
            raise ValidationError(msg)
        if price <= 0:
            msg = f"Price must be positive, got {price}"
            logger.warning(msg)
            raise ValidationError(msg)
    return price


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> dict:
    """
    Run all validations and return a clean, normalized parameter dict.

    Args:
        symbol: Trading pair symbol.
        side: 'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity: Order quantity.
        price: Limit price (required for LIMIT orders).

    Returns:
        Dictionary with validated and normalized parameters.

    Raises:
        ValidationError: On any validation failure.
    """
    logger.debug(
        "Validating order params: symbol=%s side=%s type=%s qty=%s price=%s",
        symbol, side, order_type, quantity, price,
    )
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.upper()),
    }
