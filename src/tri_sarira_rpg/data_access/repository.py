"""Toegangslayer voor JSON-content."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .loader import DataLoader


class DataRepository:
    """Biedt get_* methoden voor alle data-entiteiten."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._loader = DataLoader(data_dir)

    def get_actor(self, actor_id: str) -> dict[str, Any] | None:
        """Haal een actordefinitie op."""

        return self._loader.load_json("actors.json").get(actor_id)

    def get_enemies_for_group(self, group_id: str) -> list[dict[str, Any]]:
        """Retourneer enemy-entries voor een encountergroep."""

        return self._loader.load_json("enemies.json").get(group_id, [])

    def get_quest(self, quest_id: str) -> dict[str, Any] | None:
        """Haal questdata op voor questsystemen."""

        return self._loader.load_json("quests.json").get(quest_id)

    def get_dialogue(self, dialogue_id: str) -> dict[str, Any] | None:
        """Geef dialooggraph-definitie terug."""

        return self._loader.load_json("dialogue.json").get(dialogue_id)

    def get_zone(self, zone_id: str) -> dict[str, Any] | None:
        """Geef metadata voor een zone."""

        return self._loader.load_json("zones.json").get(zone_id)

    def get_events_for_zone(self, zone_id: str) -> list[dict[str, Any]]:
        """Filter eventdefinities voor de opgegeven zone."""

        return [
            entry
            for entry in self._loader.load_json("events.json")
            if entry.get("zone_id") == zone_id
        ]


__all__ = ["DataRepository"]
