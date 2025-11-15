"""Loggingconfiguratie voor de game."""

from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configureer standaard logging-output."""

    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(name)s: %(message)s",
    )


__all__ = ["configure_logging"]
