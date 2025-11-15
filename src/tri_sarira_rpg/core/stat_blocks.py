"""Statistiekstructuren voor actors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StatBlock:
    """Houdt basisstats per actor."""

    strength: int = 0
    mind: int = 0
    spirit: int = 0

    def apply_growth(self, other: "StatBlock") -> None:
        """Pas een groeiprofiel toe."""

        pass


__all__ = ["StatBlock"]
