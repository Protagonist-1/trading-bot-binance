# Order placement logic.

from __future__ import annotations

from typing import Any

from bot.client import BinanceClient
from bot.logging_config import setup_logging
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logging()


def _build_payload(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
    stop_price: float | None,
) -> dict[str, Any]:
    """Construct the order parameter dict based on order type."""
    payload: dict[str, Any] = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        payload["price"] = price
        payload["timeInForce"] = "GTC"

    elif order_type == "STOP_MARKET":
        payload["stopPrice"] = stop_price

    return payload


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
) -> dict[str, Any]:

    #  Validate 
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price, order_type)
    stop_price = validate_stop_price(stop_price, order_type)

    #  Build & log request summary 
    payload = _build_payload(symbol, side, order_type, quantity, price, stop_price)
    logger.info(
        "Placing %s %s order | symbol=%s qty=%s price=%s stop_price=%s",
        side,
        order_type,
        symbol,
        quantity,
        price,
        stop_price,
    )

    #  Submit 
    response = client.place_order(**payload)
    logger.info(
        "Order accepted | orderId=%s status=%s executedQty=%s avgPrice=%s",
        response.get("orderId"),
        response.get("status"),
        response.get("executedQty"),
        response.get("avgPrice"),
    )
    return response


def format_order_summary(params: dict[str, Any]) -> str:
    # Human-readable summary of what is about to be placed
    lines = [
        "─" * 45,
        "  ORDER REQUEST SUMMARY",
        "─" * 45,
        f"  Symbol     : {params.get('symbol')}",
        f"  Side       : {params.get('side')}",
        f"  Type       : {params.get('type')}",
        f"  Quantity   : {params.get('quantity')}",
    ]
    if params.get("price"):
        lines.append(f"  Price      : {params.get('price')}")
    if params.get("stop_price"):
        lines.append(f"  Stop Price : {params.get('stop_price')}")
    lines.append("─" * 45)
    return "\n".join(lines)


def format_order_response(response: dict[str, Any]) -> str:
    # Human-readable display of the Binance order response.
    lines = [
        "─" * 45,
        "  ORDER RESPONSE",
        "─" * 45,
        f"  Order ID   : {response.get('orderId')}",
        f"  Status     : {response.get('status')}",
        f"  Symbol     : {response.get('symbol')}",
        f"  Side       : {response.get('side')}",
        f"  Type       : {response.get('type')}",
        f"  Orig Qty   : {response.get('origQty')}",
        f"  Exec Qty   : {response.get('executedQty')}",
        f"  Avg Price  : {response.get('avgPrice')}",
        f"  Time       : {response.get('updateTime')}",
        "─" * 45,
    ]
    return "\n".join(lines)
