"""Wereld-, map- en overworld-logica."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class WorldSystem:
    """Beheert zones, portals en encounter-triggers."""

    def __init__(self, data: Any | None = None) -> None:
        self._data = data
        self._current_zone_id: str | None = None

    def load_zone(self, zone_id: str, *, from_portal: str | None = None) -> None:
        """Laad de opgegeven zone en bereidt runtime-state voor."""

        self._current_zone_id = zone_id

    def update(self, dt: float) -> None:
        """Werk NPC’s, encountermeters en eventtriggers bij."""

        pass

    def handle_interaction(self, interaction_id: str) -> None:
        """Reageer op een interactie (b.v. portal/chest)."""

        pass

    @property
    def current_zone_id(self) -> str | None:
        """Huidig actieve zone."""

        return self._current_zone_id


__all__ = ["WorldSystem"]
