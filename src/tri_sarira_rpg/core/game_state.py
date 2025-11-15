"""Globale gamestate container."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GameState:
    """Houdt referenties naar systemen en high-level vlaggen."""

    systems: dict[str, Any]

    def get_system(self, name: str) -> Any:
        """Haal een systeem op uit de state."""

        return self.systems.get(name)

    def reset(self) -> None:
        """Reset tijdelijke runtime-state."""

        pass


__all__ = ["GameState"]
