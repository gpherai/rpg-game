"""Eenvoudige profiler hooks."""

from __future__ import annotations

import contextlib
import time
from typing import Iterator


@contextlib.contextmanager
def profile_section(label: str) -> Iterator[None]:
    """Contextmanager om ruwe timing te loggen."""

    start = time.perf_counter()
    try:
        yield
    finally:
        _ = time.perf_counter() - start


__all__ = ["profile_section"]
