"""Tijd-, dag/nacht- en seizoensbeheer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TimeState:
    """Serieel-opslagbare representatie van tijd."""

    day_index: int = 0
    minutes: int = 0
    season_index: int = 0


class TimeSystem:
    """Beheert tijdsverloop en levert events voor systemen."""

    def __init__(self) -> None:
        self._state = TimeState()

    def advance_minutes(self, minutes: int) -> None:
        """Versnel tijd vooruit en fire events indien grenzen overschreden."""

        pass

    def set_time(self, day_index: int, minutes: int) -> None:
        """Forceer een absolute tijd (bijv. bij load)."""

        pass

    @property
    def state(self) -> TimeState:
        """Huidige tijdsstate die geserialiseerd kan worden."""

        return self._state


__all__ = ["TimeSystem", "TimeState"]
