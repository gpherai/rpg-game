"""Timing utilities."""

from __future__ import annotations

import time


class GameClock:
    """Houdt delta-time bij voor systemen buiten Pygame."""

    def __init__(self) -> None:
        self._last = time.perf_counter()

    def tick(self) -> float:
        """Retourneer delta sinds de vorige tick."""

        current = time.perf_counter()
        delta = current - self._last
        self._last = current
        return delta


__all__ = ["GameClock"]
