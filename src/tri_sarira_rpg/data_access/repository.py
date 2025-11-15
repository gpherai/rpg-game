"""Toegangslayer voor JSON-content."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .loader import DataLoader

logger = logging.getLogger(__name__)


class DataRepository:
    """Biedt get_* methoden voor alle data-entiteiten met validatie."""

    # Required keys per data type
    REQUIRED_KEYS = {
        "actors": ["id", "name", "type", "level"],
        "enemies": ["id", "name", "type", "level"],
        "zones": ["id", "name", "type", "description"],
    }

    def __init__(self, data_dir: Path | None = None) -> None:
        self._loader = DataLoader(data_dir)
        self._validation_errors: list[str] = []

    def load_and_validate_all(self) -> bool:
        """Laad en valideer alle data-bestanden.

        Returns
        -------
        bool
            True als alles OK is, False bij fouten
        """
        self._validation_errors.clear()
        all_ok = True

        for data_type in ["actors", "enemies", "zones"]:
            try:
                data = self._loader.load_json(f"{data_type}.json")
                required = self.REQUIRED_KEYS.get(data_type, ["id", "name"])
                errors = self._loader.validate_data(data, data_type, required)

                if errors:
                    self._validation_errors.extend(errors)
                    all_ok = False
                    for error in errors:
                        logger.error(f"Validation error: {error}")
                else:
                    logger.info(f"✓ {data_type}.json validated successfully")

            except FileNotFoundError as e:
                self._validation_errors.append(str(e))
                logger.error(f"File not found: {e}")
                all_ok = False
            except ValueError as e:
                self._validation_errors.append(str(e))
                logger.error(f"Invalid data: {e}")
                all_ok = False

        return all_ok

    def get_validation_errors(self) -> list[str]:
        """Geef alle validatiefouten terug."""
        return self._validation_errors.copy()

    # Actor methods
    def get_actor(self, actor_id: str) -> dict[str, Any] | None:
        """Haal een actordefinitie op."""
        data = self._loader.load_json("actors.json")
        actors = data.get("actors", [])
        for actor in actors:
            if actor.get("id") == actor_id:
                return actor
        return None

    def get_all_actors(self) -> list[dict[str, Any]]:
        """Haal alle actordefinities op."""
        data = self._loader.load_json("actors.json")
        return data.get("actors", [])

    # Enemy methods
    def get_enemy(self, enemy_id: str) -> dict[str, Any] | None:
        """Haal een enemydefinitie op."""
        data = self._loader.load_json("enemies.json")
        enemies = data.get("enemies", [])
        for enemy in enemies:
            if enemy.get("id") == enemy_id:
                return enemy
        return None

    def get_all_enemies(self) -> list[dict[str, Any]]:
        """Haal alle enemydefinities op."""
        data = self._loader.load_json("enemies.json")
        return data.get("enemies", [])

    # Zone methods
    def get_zone(self, zone_id: str) -> dict[str, Any] | None:
        """Haal een zonedefinitie op."""
        data = self._loader.load_json("zones.json")
        zones = data.get("zones", [])
        for zone in zones:
            if zone.get("id") == zone_id:
                return zone
        return None

    def get_all_zones(self) -> list[dict[str, Any]]:
        """Haal alle zonedefinities op."""
        data = self._loader.load_json("zones.json")
        return data.get("zones", [])

    # Legacy methods (for compatibility)
    def get_enemies_for_group(self, group_id: str) -> list[dict[str, Any]]:
        """Retourneer enemy-entries voor een encountergroep."""
        # For now just return all enemies matching the group_id tag
        enemies = self.get_all_enemies()
        return [e for e in enemies if group_id in e.get("tags", [])]

    def get_quest(self, quest_id: str) -> dict[str, Any] | None:
        """Haal questdata op voor questsystemen."""
        # Not implemented yet (no quests.json in this step)
        return None

    def get_dialogue(self, dialogue_id: str) -> dict[str, Any] | None:
        """Geef dialooggraph-definitie terug."""
        # Not implemented yet (no dialogue.json in this step)
        return None

    def get_events_for_zone(self, zone_id: str) -> list[dict[str, Any]]:
        """Filter eventdefinities voor de opgegeven zone."""
        # Not implemented yet (no events.json in this step)
        return []


__all__ = ["DataRepository"]
