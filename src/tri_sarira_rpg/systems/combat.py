"""Tactische gevechtslogica."""

from __future__ import annotations

from typing import Any


class CombatSystem:
    """Beheert battles, turn order en skillresolutie."""

    def __init__(self, party_system: Any, items_system: Any | None = None) -> None:
        self._party = party_system
        self._items = items_system

    def start_battle(self, enemy_group_id: str) -> None:
        """Initialiseer een battlecontext voor de gegeven enemy groep."""

        pass

    def update(self, dt: float) -> None:
        """Laat de huidige battle vooruitgaan."""

        pass

    def select_action(self, actor_id: str, action: Any) -> None:
        """Ontvang input over welke actie een actor uitvoert."""

        pass

    def resolve_turn(self) -> None:
        """Voer de acties van de huidige beurt uit en evalueer resultaten."""

        pass


__all__ = ["CombatSystem"]
