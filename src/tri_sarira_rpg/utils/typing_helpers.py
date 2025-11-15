"""Type aliasen en protocoldefinities."""

from __future__ import annotations

from typing import Protocol


class SupportsUpdate(Protocol):
    """Protocol voor objecten met een update(dt)-methode."""

    def update(self, dt: float) -> None:  # pragma: no cover - signature only
        ...


__all__ = ["SupportsUpdate"]
