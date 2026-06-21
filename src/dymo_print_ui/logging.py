"""Logging setup built on loguru.

A single console sink plus a rotating file sink under the user's app-data
directory. Import :func:`setup_logging` once at startup.
"""

from __future__ import annotations

import sys

from loguru import logger
from platformdirs import user_log_dir

APP_NAME = "dymo-print-ui"


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru with a console and a rotating file sink."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:HH:mm:ss}</green> "
            "<level>{level: <8}</level> "
            "<cyan>{name}</cyan> - <level>{message}</level>"
        ),
    )

    log_dir = user_log_dir(APP_NAME, appauthor=False, ensure_exists=True)
    logger.add(
        f"{log_dir}/app.log",
        level=level,
        rotation="2 MB",
        retention="7 days",
        encoding="utf-8",
    )
    logger.debug("Logging initialised; file sink at {}", log_dir)
