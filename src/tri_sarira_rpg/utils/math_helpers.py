"""Mathematische hulpfuncties."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Beperk een waarde tot het opgegeven bereik."""

    return value


def lerp(a: float, b: float, t: float) -> float:
    """Lineaire interpolatie placeholder."""

    return a + (b - a) * t


__all__ = ["clamp", "lerp"]
