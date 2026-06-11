"""
Binance Futures Testnet REST client.
Handles request signing, sending, and response parsing.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logging

logger = setup_logging()

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
REQUEST_TIMEOUT = 10  # seconds


class BinanceAPIError(Exception):
    # Raised when Binance returns a non-2xx response or an error payload

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:

    def __init__(self, api_key: str, api_secret: str, base_url: str = TESTNET_BASE_URL) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": self.api_key})

    #  Signing and timestamp helpers

    def _get_server_time(self) -> int:
        """Fetch Binance server time to avoid clock-skew errors."""
        try:
            resp = self._session.get(
                f"{self.base_url}/fapi/v1/time", timeout=REQUEST_TIMEOUT
            )
            return resp.json()["serverTime"]
        except Exception:
            return int(time.time() * 1000)  # fallback to local time

    def _sign(self, params: dict[str, Any]) -> dict[str, Any]:
        params["timestamp"] = self._get_server_time()
        params["recvWindow"] = 10000
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    #  HTTP helpers

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> dict[str, Any]:
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        logger.debug("REQUEST  %s %s | params: %s", method.upper(), url, params)

        try:
            response = self._session.request(
                method,
                url,
                params=params if method.upper() == "GET" else None,
                data=params if method.upper() == "POST" else None,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error while calling %s: %s", url, exc)
            raise ConnectionError(f"Could not reach Binance Testnet ({url}). Check your internet connection.") from exc
        except requests.exceptions.Timeout:
            logger.error("Request timed out: %s", url)
            raise TimeoutError(f"Request to {url} timed out after {REQUEST_TIMEOUT}s.")

        logger.debug("RESPONSE %s %s | body: %s", response.status_code, url, response.text)

        try:
            data = response.json()
        except ValueError:
            logger.error("Non-JSON response from %s: %s", url, response.text)
            raise BinanceAPIError(-1, f"Unexpected non-JSON response: {response.text}")

        if not response.ok or (isinstance(data, dict) and "code" in data and data["code"] < 0):
            code = data.get("code", response.status_code)
            msg = data.get("msg", response.text)
            logger.error("API error %s: %s", code, msg)
            raise BinanceAPIError(code, msg)

        return data  # type: ignore[return-value]

    #  Public API  

    def get_exchange_info(self) -> dict[str, Any]:
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> dict[str, Any]:
        return self._request("GET", "/fapi/v2/account", signed=True)

    #  Order placement  

    def place_order(self, **kwargs: Any) -> dict[str, Any]:
        """
        Place a futures order. kwargs are passed directly as POST params.
        Required keys vary by order type; validation is done in orders.py.
        """
        return self._request("POST", "/fapi/v1/order", params=kwargs, signed=True)
