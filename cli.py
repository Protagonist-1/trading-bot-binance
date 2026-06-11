from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import setup_logging
from bot.orders import format_order_response, format_order_summary, place_order
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

load_dotenv()
logger = setup_logging()


# ── Argument parser

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Market BUY
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit SELL
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 50000

  # Stop-Market BUY
  python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 25000
""",
    )

    parser.add_argument(
        "--symbol", required=True,
        help="Trading pair symbol (e.g., BTCUSDT)"
    )
    parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL"],
        help="Order side: BUY or SELL"
    )
    parser.add_argument(
        "--type", required=True, dest="order_type",
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        help="Order type: MARKET | LIMIT | STOP_MARKET"
    )
    parser.add_argument(
        "--quantity", required=True,
        help="Order quantity (e.g., 0.001)"
    )
    parser.add_argument(
        "--price",
        help="Limit price (required for LIMIT orders)"
    )
    parser.add_argument(
        "--stop-price", dest="stop_price",
        help="Stop trigger price (required for STOP_MARKET orders)"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("BINANCE_API_KEY"),
        help="Binance API key (or set BINANCE_API_KEY env var)"
    )
    parser.add_argument(
        "--api-secret",
        default=os.getenv("BINANCE_API_SECRET"),
        help="Binance API secret (or set BINANCE_API_SECRET env var)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate inputs and print summary without placing the order"
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level (default: INFO)"
    )

    return parser


# ── Main

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Re-init logger with user-chosen level
    setup_logging(args.log_level)

    #  Validate credentials 
    if not args.api_key or not args.api_secret:
        parser.error(
            "API credentials missing. Set BINANCE_API_KEY / BINANCE_API_SECRET "
            "environment variables or pass --api-key / --api-secret."
        )

    #  Pre-validate inputs early (before hitting the network) 
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValueError as exc:
        logger.error("Validation failed: %s", exc)
        print(f"\n✗  Validation error: {exc}\n")
        sys.exit(1)

    #  Print request summary 
    summary_params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }
    print(format_order_summary(summary_params))

    if args.dry_run:
        print("  DRY RUN — order not submitted.\n")
        sys.exit(0)

    #  Place order 
    client = BinanceClient(api_key=args.api_key, api_secret=args.api_secret)

    try:
        response = place_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\n✗  Validation error: {exc}\n")
        sys.exit(1)
    except BinanceAPIError as exc:
        logger.error("API error: %s", exc)
        print(f"\n✗  API error {exc.code}: {exc.message}\n")
        sys.exit(2)
    except (ConnectionError, TimeoutError) as exc:
        logger.error("Network error: %s", exc)
        print(f"\n✗  Network error: {exc}\n")
        sys.exit(3)

    #  Print response 
    print(format_order_response(response))
    print(f"\n✓  Order placed successfully! Order ID: {response.get('orderId')}\n")


if __name__ == "__main__":
    main()
