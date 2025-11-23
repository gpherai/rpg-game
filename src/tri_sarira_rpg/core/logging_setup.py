"""Loggingconfiguratie voor de game."""

from __future__ import annotations

import logging
from typing import Any


def configure_logging(level: int = logging.INFO) -> None:
    """Configureer standaard logging-output."""

    try:
        import colorlog

        handler = colorlog.StreamHandler()
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s[%(levelname)s]%(reset)s %(name)s: %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(level)
    except ImportError:
        # Fallback zonder kleur als colorlog niet beschikbaar is
        logging.basicConfig(
            level=level,
            format="[%(levelname)s] %(name)s: %(message)s",
        )


__all__ = ["configure_logging"]
