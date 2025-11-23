"""Eenvoudige profiler hooks."""

from __future__ import annotations

import contextlib
import logging
import time
from collections.abc import Iterator

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def profile_section(label: str) -> Iterator[None]:
    """Contextmanager om ruwe timing te loggen."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.debug("%s: %.4fs", label, elapsed)


__all__ = ["profile_section"]
