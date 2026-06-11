import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")

_configured = False


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure structured logging to both console and rotating log file.
    Returns the root logger for the trading_bot package.
    """
    global _configured

    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if _configured:
        # Already set up — just update the level if caller changed it
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ── File handler (5 MB max, 3 backup files) ───────────────────────────────
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    _configured = True
    return logger
