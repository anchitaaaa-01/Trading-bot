"""
client.py
---------
Low-level API wrapper for Binance Futures Testnet REST API.
Handles authentication, request signing, retries with exponential backoff,
and HTTP error handling.
"""

import hashlib
import hmac
import logging
import os
import time
from typing import Any, Optional
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("trading_bot.client")

# ── Base URL ────────────────────────────────────────────────────────────────
TESTNET_BASE_URL: str = "https://testnet.binancefuture.com"
ORDER_ENDPOINT: str = "/fapi/v1/order"

# ── Retry settings ──────────────────────────────────────────────────────────
MAX_RETRIES: int = 3
BACKOFF_BASE: float = 2.0       # seconds; delay = BACKOFF_BASE ^ attempt
RETRY_STATUS_CODES: set[int] = {429, 500, 502, 503, 504}

# ── Request timeout ─────────────────────────────────────────────────────────
REQUEST_TIMEOUT: int = 10       # seconds


class BinanceAPIError(Exception):
    """Raised for non-retryable Binance API errors (4xx, bad credentials, etc.)."""

    def __init__(self, message: str, status_code: Optional[int] = None, code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class NetworkError(Exception):
    """Raised when all retry attempts are exhausted due to network issues."""


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance Futures Testnet REST API.

    Reads API credentials from environment variables:
        BINANCE_API_KEY
        BINANCE_API_SECRET

    Usage::

        client = BinanceFuturesClient()
        response = client.place_order(symbol="BTCUSDT", side="BUY",
                                       order_type="MARKET", quantity=0.01)
    """

    def __init__(self) -> None:
        self.api_key: str = os.environ.get("BINANCE_API_KEY", "")
        self.api_secret: str = os.environ.get("BINANCE_API_SECRET", "")

        if not self.api_key or not self.api_secret:
            raise EnvironmentError(
                "BINANCE_API_KEY and BINANCE_API_SECRET must be set in your .env file."
            )

        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        logger.info("BinanceFuturesClient initialised (testnet=%s)", TESTNET_BASE_URL)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _sign(self, params: dict) -> dict:
        """
        Add a HMAC-SHA256 signature and timestamp to the parameter dict.

        Args:
            params: Raw request parameters.

        Returns:
            Parameters dict augmented with 'timestamp' and 'signature'.
        """
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        logger.debug("Request signed. timestamp=%s", params["timestamp"])
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> dict:
        """
        Execute a signed HTTP request with retry logic.

        Args:
            method: HTTP method ('GET', 'POST', 'DELETE').
            endpoint: API endpoint path (e.g., '/fapi/v1/order').
            params: Query / body parameters (will be signed automatically).

        Returns:
            Parsed JSON response dict.

        Raises:
            BinanceAPIError: For non-retryable HTTP errors.
            NetworkError: When all retry attempts fail.
        """
        params = params or {}
        params = self._sign(params)
        url = f"{TESTNET_BASE_URL}{endpoint}"

        logger.info("Sending %s %s | params=%s", method, endpoint, {
            k: v for k, v in params.items() if k not in ("signature",)
        })

        last_exception: Exception = Exception("Unknown error")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.request(
                    method,
                    url,
                    params=params if method == "GET" else None,
                    data=params if method == "POST" else None,
                    timeout=REQUEST_TIMEOUT,
                )

                logger.debug(
                    "Response attempt=%d status=%d body=%s",
                    attempt, resp.status_code, resp.text[:500],
                )

                if resp.status_code in RETRY_STATUS_CODES:
                    logger.warning(
                        "Retryable status %d on attempt %d/%d",
                        resp.status_code, attempt, MAX_RETRIES,
                    )
                    last_exception = BinanceAPIError(
                        f"HTTP {resp.status_code}: {resp.text}",
                        status_code=resp.status_code,
                    )
                    self._backoff(attempt)
                    continue

                # Non-retryable 4xx errors
                if 400 <= resp.status_code < 500:
                    try:
                        error_data = resp.json()
                        code = error_data.get("code")
                        msg = error_data.get("msg", resp.text)
                    except Exception:
                        code, msg = None, resp.text
                    logger.error(
                        "Binance API error: code=%s msg=%s status=%d", code, msg, resp.status_code
                    )
                    raise BinanceAPIError(
                        f"Binance API error {code}: {msg}",
                        status_code=resp.status_code,
                        code=code,
                    )

                resp.raise_for_status()
                result = resp.json()
                logger.info("API call succeeded. orderId=%s", result.get("orderId", "N/A"))
                return result

            except (requests.ConnectionError, requests.Timeout) as exc:
                logger.warning(
                    "Network error on attempt %d/%d: %s", attempt, MAX_RETRIES, exc
                )
                last_exception = exc
                self._backoff(attempt)

        raise NetworkError(
            f"All {MAX_RETRIES} retry attempts failed. Last error: {last_exception}"
        ) from last_exception

    @staticmethod
    def _backoff(attempt: int) -> None:
        """Sleep with exponential backoff before the next retry."""
        delay = BACKOFF_BASE ** attempt
        logger.debug("Backing off for %.1f seconds before retry %d", delay, attempt + 1)
        time.sleep(delay)

    # ── Public API ───────────────────────────────────────────────────────────

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> dict[str, Any]:
        """
        Place a new futures order on Binance Testnet.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT').
            side: 'BUY' or 'SELL'.
            order_type: 'MARKET' or 'LIMIT'.
            quantity: Number of contracts.
            price: Limit price (required for LIMIT orders).
            time_in_force: Time-in-force policy for LIMIT orders (default 'GTC').

        Returns:
            Raw Binance order response dict.

        Raises:
            BinanceAPIError: On API-level errors.
            NetworkError: On persistent network failures.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price must be provided for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s",
            side, order_type, symbol, quantity, price,
        )
        return self._request("POST", ORDER_ENDPOINT, params)
