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
        "npcs": ["npc_id", "actor_id", "tier", "is_companion_candidate", "is_main_character"],
        "skills": ["id", "name", "domain", "type", "target", "power"],
        "items": ["id", "name", "type", "category"],
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

        # Required data files
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

        # Optional data files (Step 4+)
        for optional_file, data_type in [
            ("npc_meta.json", "npcs"),
            ("skills.json", "skills"),
            ("items.json", "items"),
        ]:
            try:
                data = self._loader.load_json(optional_file)
                required = self.REQUIRED_KEYS.get(data_type, ["id"])
                errors = self._loader.validate_data(data, data_type, required)

                if errors:
                    self._validation_errors.extend(errors)
                    for error in errors:
                        logger.error(f"Validation error: {error}")
                    # Don't fail validation entirely for optional file
                else:
                    logger.info(f"✓ {optional_file} validated successfully")

            except FileNotFoundError:
                logger.info(f"{optional_file} not found (optional for Step 4+/5+)")
            except ValueError as e:
                self._validation_errors.append(str(e))
                logger.error(f"Invalid {optional_file} data: {e}")
                # Don't fail validation entirely for optional file

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

    # NPC metadata methods
    def get_npc(self, npc_id: str) -> dict[str, Any] | None:
        """Haal een NPC-definitie op uit npc_meta.json."""
        try:
            data = self._loader.load_json("npc_meta.json")
            npcs = data.get("npcs", [])
            for npc in npcs:
                if npc.get("npc_id") == npc_id:
                    return npc
        except FileNotFoundError:
            logger.warning("npc_meta.json not found, NPC metadata not available")
        return None

    def get_all_npcs(self) -> list[dict[str, Any]]:
        """Haal alle NPC-definities op uit npc_meta.json."""
        try:
            data = self._loader.load_json("npc_meta.json")
            return data.get("npcs", [])
        except FileNotFoundError:
            logger.warning("npc_meta.json not found, returning empty list")
            return []

    def get_npc_meta(self) -> dict[str, Any]:
        """Haal de volledige npc_meta.json op voor PartySystem initialisatie."""
        try:
            return self._loader.load_json("npc_meta.json")
        except FileNotFoundError:
            logger.warning("npc_meta.json not found, returning empty structure")
            return {"npcs": []}

    # Skill methods (Step 5: Combat v0)
    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Haal een skill-definitie op uit skills.json."""
        try:
            data = self._loader.load_json("skills.json")
            skills = data.get("skills", [])
            for skill in skills:
                if skill.get("id") == skill_id:
                    return skill
        except FileNotFoundError:
            logger.warning("skills.json not found, skill data not available")
        return None

    def get_all_skills(self) -> list[dict[str, Any]]:
        """Haal alle skill-definities op uit skills.json."""
        try:
            data = self._loader.load_json("skills.json")
            return data.get("skills", [])
        except FileNotFoundError:
            logger.warning("skills.json not found, returning empty list")
            return []

    # Item methods (Step 5: Combat v0)
    def get_item(self, item_id: str) -> dict[str, Any] | None:
        """Haal een item-definitie op uit items.json."""
        try:
            data = self._loader.load_json("items.json")
            items = data.get("items", [])
            for item in items:
                if item.get("id") == item_id:
                    return item
        except FileNotFoundError:
            logger.warning("items.json not found, item data not available")
        return None

    def get_all_items(self) -> list[dict[str, Any]]:
        """Haal alle item-definities op uit items.json."""
        try:
            data = self._loader.load_json("items.json")
            return data.get("items", [])
        except FileNotFoundError:
            logger.warning("items.json not found, returning empty list")
            return []

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
