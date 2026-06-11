# Binance Futures Testnet Trading Bot

A clean, production-style Python CLI application for placing orders on the Binance Futures Testnet (USDT-M).

---

## Features

- **MARKET** and **LIMIT** order types *(core)*
- **STOP_MARKET** order type *(bonus — third order type)*
- Both **BUY** and **SELL** sides
- Full **input validation** with descriptive error messages
- **Structured logging** to console + rotating log file (`logs/trading_bot.log`)
- **Layered architecture** — separate client, order-logic, validation, and CLI layers
- **.env support** for keeping credentials out of the command line

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, HTTP, error handling)
│   ├── orders.py          # Order placement logic + output formatting
│   ├── validators.py      # Input validation (all raises ValueError)
│   └── logging_config.py  # Rotating file + console logger setup
├── logs/
│   └── trading_bot.log    # Live log file (all runs appended here)
├── cli.py                 # CLI entry point (argparse)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Register on Binance Futures Testnet

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with GitHub OAuth
3. Navigate to **API Management** → generate a new key pair
4. Copy your **API Key** and **Secret Key**

### 2. Install dependencies

```bash
# Python 3.8+ required
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
# Edit .env and paste your testnet API key and secret
```

Your `.env` file should look like:
```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

---

## How to Run

### Basic syntax

```bash
python cli.py --symbol <SYMBOL> --side <BUY|SELL> --type <ORDER_TYPE> --quantity <QTY> [--price <PRICE>] [--stop-price <PRICE>]
```

### Examples

**Market BUY — buy 0.001 BTC at current market price**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Limit SELL — place a sell order at $70,000**
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000
```

**Stop-Market BUY — trigger a buy if price drops to $25,000**
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 25000
```

**Dry run (validate without placing)**
```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 50000 --dry-run
```

**Pass credentials inline (bypasses .env)**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 \
  --api-key YOUR_KEY --api-secret YOUR_SECRET
```

**Verbose debug logging**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --log-level DEBUG
```

---

## Sample Output

```
─────────────────────────────────────────────
  ORDER REQUEST SUMMARY
─────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
─────────────────────────────────────────────
─────────────────────────────────────────────
  ORDER RESPONSE
─────────────────────────────────────────────
  Order ID   : 14804234455
  Status     : NEW
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Orig Qty   : 0.0010
  Exec Qty   : 0.0000
  Avg Price  : None
  Time       : 1781190624911
─────────────────────────────────────────────

✓  Order placed successfully! Order ID: 14804234455
```

---

## Log Files

All logs are written to `logs/trading_bot.log` (rotating, max 5 MB, 3 backups). Every order run — MARKET, LIMIT, or STOP_MARKET — is appended there automatically.

To see full DEBUG output including raw request/response bodies:
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --log-level DEBUG
```

---

## Assumptions

1. **Testnet only** — the base URL is hardcoded to `https://testnet.binancefuture.com`. Swap `TESTNET_BASE_URL` in `bot/client.py` for production use (with real money — be careful).
2. **USDT-M Futures** — only perpetual USDT-margined contracts are targeted; coin-margined (COIN-M) endpoints differ.
3. **Quantity precision** — the bot sends raw quantity values. If the testnet rejects your order with a precision error, reduce decimal places (e.g., `0.001` → `0.01`).
4. **GTC time-in-force** — all LIMIT orders use Good-Till-Cancelled.
5. **No position management** — the bot only places orders; it does not track open positions, PnL, or account balance.
6. **Dependencies are minimal** — only `requests` and `python-dotenv` are used (no `python-binance` SDK) for transparency and portability.
