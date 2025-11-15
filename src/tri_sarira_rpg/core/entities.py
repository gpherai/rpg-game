"""Basale entitymodellen."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Entity:
    """Algemene entity met een uniek ID."""

    entity_id: str

    def to_dict(self) -> dict[str, object]:
        """Serieel uitgangspunt voor saves."""

        return {"entity_id": self.entity_id}


@dataclass
class Position:
    """2D-positie binnen tile-space."""

    x: int
    y: int


__all__ = ["Entity", "Position"]
