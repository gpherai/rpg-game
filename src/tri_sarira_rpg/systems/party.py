"""Partybeheer en companion-lifecycle."""

from __future__ import annotations

from typing import Any


class PartySystem:
    """Houdt bij wie actief is, welke companions beschikbaar zijn en hun stats."""

    def __init__(self, data_repository: Any | None = None) -> None:
        self._data_repository = data_repository
        self._active_party: list[str] = []

    def add_member(self, actor_id: str) -> None:
        """Voeg een actor toe aan de actieve party indien mogelijk."""

        pass

    def remove_member(self, actor_id: str) -> None:
        """Verwijder een actor uit de actieve partij."""

        pass

    def iterate_members(self) -> list[str]:
        """Retourneer een snapshot van de actieve party."""

        return list(self._active_party)


__all__ = ["PartySystem"]
