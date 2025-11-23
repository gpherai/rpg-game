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

        def add_error(message: str) -> None:
            nonlocal all_ok
            self._validation_errors.append(message)
            all_ok = False

        # Load core files
        required_files = [
            ("actors.json", "actors"),
            ("enemies.json", "enemies"),
            ("items.json", "items"),
            ("skills.json", "skills"),
            ("zones.json", "zones"),
            ("npc_meta.json", "npcs"),
            ("npc_schedules.json", "npc_schedules"),
            ("quests.json", "quests"),
            ("dialogue.json", "dialogues"),
            ("chests.json", "chests"),
            ("enemy_groups.json", "enemy_groups"),
            ("loot_tables.json", "loot_tables"),
            ("events.json", "events"),
            ("shops.json", "shops"),
        ]

        loaded: dict[str, dict[str, Any]] = {}

        for filename, _ in required_files:
            try:
                loaded[filename] = self._loader.load_json(filename)
            except FileNotFoundError as e:
                add_error(f"Required data file missing: {filename} ({e})")
            except ValueError as e:
                add_error(f"Invalid JSON in {filename}: {e}")

        # Basic required-key validation for simple types
        for filename, data_type in [
            ("actors.json", "actors"),
            ("enemies.json", "enemies"),
            ("zones.json", "zones"),
            ("skills.json", "skills"),
            ("items.json", "items"),
        ]:
            data = loaded.get(filename)
            if not data:
                continue
            required = self.REQUIRED_KEYS.get(data_type, ["id", "name"])
            errors = self._loader.validate_data(data, data_type, required)
            if errors:
                for error in errors:
                    add_error(error)

        # Build lookup sets for cross-ref checks
        actor_ids = {a["id"] for a in loaded.get("actors.json", {}).get("actors", [])}
        enemy_ids = {e["id"] for e in loaded.get("enemies.json", {}).get("enemies", [])}
        item_ids = {i["id"] for i in loaded.get("items.json", {}).get("items", [])}
        skill_ids = {s["id"] for s in loaded.get("skills.json", {}).get("skills", [])}
        zone_ids = {z["id"] for z in loaded.get("zones.json", {}).get("zones", [])}
        npc_meta = loaded.get("npc_meta.json", {}).get("npcs", [])
        npc_ids = {n.get("npc_id") for n in npc_meta if n.get("npc_id")}
        quest_defs = loaded.get("quests.json", {}).get("quests", [])
        quest_ids = {q["quest_id"] for q in quest_defs if "quest_id" in q}
        enemy_groups = loaded.get("enemy_groups.json", {}).get("enemy_groups", [])

        # npc_meta basic check (actor_id optional)
        for npc in npc_meta:
            if "npc_id" not in npc:
                add_error("npc_meta.json: entry missing npc_id")
            actor_id = npc.get("actor_id")
            if actor_id and actor_id not in actor_ids:
                add_error(f"npc_meta.json: actor_id {actor_id} not found for npc {npc.get('npc_id')}")

        # npc_schedules: npc_id and zone_id must exist
        for sched in loaded.get("npc_schedules.json", {}).get("npc_schedules", []):
            npc_id = sched.get("npc_id")
            if npc_id and npc_id not in npc_ids:
                add_error(f"npc_schedules.json: npc_id {npc_id} not found in npc_meta.json")
            for rule in sched.get("rules", []):
                z = rule.get("zone_id")
                if z and z not in zone_ids:
                    add_error(f"npc_schedules.json: rule zone_id {z} not found for npc {npc_id}")

        # Quests: stages/rewards/items
        seen_quest_ids: set[str] = set()
        for quest in quest_defs:
            qid = quest.get("quest_id")
            if not qid:
                add_error("quests.json: quest missing quest_id")
                continue
            if qid in seen_quest_ids:
                add_error(f"quests.json: duplicate quest_id {qid}")
            seen_quest_ids.add(qid)

            stages = quest.get("stages", [])
            if not stages:
                add_error(f"quests.json: quest {qid} has no stages")
            for reward in quest.get("rewards", {}).get("items", []):
                iid = reward.get("item_id")
                if iid and iid not in item_ids:
                    add_error(f"quests.json: reward item_id {iid} not found for quest {qid}")

        # Dialogue: speakers/items/quests in effects/conditions
        dialogue_entries = loaded.get("dialogue.json", {}).get("dialogues", [])
        for dlg in dialogue_entries:
            for node in dlg.get("nodes", []):
                speaker = node.get("speaker_id")
                if speaker and speaker not in npc_ids and speaker not in actor_ids:
                    add_error(f"dialogue.json: speaker_id {speaker} not found (dialogue {dlg.get('dialogue_id')})")
                # Node-level effects (rare)
                for eff in node.get("effects", []):
                    iid = eff.get("item_id")
                    if iid and iid not in item_ids:
                        add_error(f"dialogue.json: item_id {iid} not found in node {node.get('node_id')}")
                for choice in node.get("choices", []):
                    for eff in choice.get("effects", []):
                        iid = eff.get("item_id")
                        if iid and iid not in item_ids:
                            add_error(
                                f"dialogue.json: item_id {iid} not found in choice {choice.get('choice_id')} "
                                f"(dialogue {dlg.get('dialogue_id')})"
                            )
                    for cond in choice.get("conditions", []):
                        if cond.get("condition_type") == "COMPANION_IN_PARTY":
                            npc_id = cond.get("params", {}).get("npc_id")
                            if npc_id and npc_id not in npc_ids:
                                add_error(
                                    f"dialogue.json: npc_id {npc_id} in condition not found "
                                    f"(dialogue {dlg.get('dialogue_id')})"
                                )

        # Chests: zone_id and item_ids
        for chest in loaded.get("chests.json", {}).get("chests", []):
            cid = chest.get("chest_id")
            zone_id = chest.get("zone_id")
            if zone_id and zone_id not in zone_ids:
                add_error(f"chests.json: chest {cid} has unknown zone_id {zone_id}")
            for entry in chest.get("contents", []):
                iid = entry.get("item_id")
                if iid and iid not in item_ids:
                    add_error(f"chests.json: chest {cid} references unknown item_id {iid}")

        # Loot tables: item_ids must exist
        for table in loaded.get("loot_tables.json", {}).get("loot_tables", []):
            tid = table.get("loot_table_id")
            for entry in table.get("entries", []):
                iid = entry.get("item_id")
                if iid and iid not in item_ids:
                    add_error(f"loot_tables.json: loot_table {tid} references unknown item_id {iid}")

        # Enemy groups: enemies must exist
        for group in enemy_groups:
            gid = group.get("group_id")
            for enemy in group.get("enemies", []):
                if enemy not in enemy_ids:
                    add_error(f"enemy_groups.json: group {gid} references unknown enemy_id {enemy}")

        # Events: enemy_group_id, quest_id/stage_id, zone_id (if present)
        for event in loaded.get("events.json", {}).get("events", []):
            eid = event.get("event_id")
            trig = event.get("trigger", {})
            z = trig.get("zone_id")
            if z and z not in zone_ids:
                add_error(f"events.json: event {eid} has unknown trigger zone_id {z}")
            for action in event.get("actions", []):
                if "action_type" not in action:
                    add_error(f"events.json: event {eid} has action without action_type")
                    continue
                eg = action.get("enemy_group_id")
                if eg and all(g.get("group_id") != eg for g in enemy_groups):
                    add_error(f"events.json: event {eid} references unknown enemy_group_id {eg}")
                qid = action.get("quest_id")
                if qid and qid not in quest_ids:
                    add_error(f"events.json: event {eid} references unknown quest_id {qid}")
                sid = action.get("stage_id")
                if qid and sid:
                    quest = next((q for q in quest_defs if q.get("quest_id") == qid), None)
                    if quest and all(s.get("stage_id") != sid for s in quest.get("stages", [])):
                        add_error(f"events.json: event {eid} references unknown stage_id {sid} for quest {qid}")

        # Shops: zone_id and item_ids
        for shop in loaded.get("shops.json", {}).get("shops", []):
            sid = shop.get("shop_id")
            zone_id = shop.get("zone_id")
            if zone_id and zone_id not in zone_ids:
                add_error(f"shops.json: shop {sid} has unknown zone_id {zone_id}")
            for entry in shop.get("inventory_entries", []):
                iid = entry.get("item_id")
                if iid and iid not in item_ids:
                    add_error(f"shops.json: shop {sid} references unknown item_id {iid}")

        return all_ok

    def get_validation_errors(self) -> list[str]:
        """Geef alle validatiefouten terug."""
        return self._validation_errors.copy()

    @staticmethod
    def format_validation_errors(errors: list[str]) -> str:
        """Maak een leesbare samenvatting van validatiefouten."""
        if not errors:
            return "Data validation passed with no errors."
        lines = [f"Data validation failed with {len(errors)} error(s):"]
        lines.extend([f"  - {err}" for err in errors])
        return "\n".join(lines)

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

    # Enemy groups
    def get_enemy_group(self, group_id: str) -> dict[str, Any] | None:
        """Haal een enemy group op uit enemy_groups.json."""
        try:
            data = self._loader.load_json("enemy_groups.json")
            for group in data.get("enemy_groups", []):
                if group.get("group_id") == group_id:
                    return group
        except FileNotFoundError:
            logger.warning("enemy_groups.json not found, enemy group data not available")
        return None

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
        try:
            data = self._loader.load_json("quests.json")
            quests = data.get("quests", [])
            for quest in quests:
                if quest.get("quest_id") == quest_id:
                    return quest
            return None
        except FileNotFoundError:
            logger.warning("quests.json not found")
            return None

    def get_all_quests(self) -> list[dict[str, Any]]:
        """Haal alle quests op."""
        try:
            data = self._loader.load_json("quests.json")
            return data.get("quests", [])
        except FileNotFoundError:
            logger.warning("quests.json not found")
            return []

    def get_dialogue(self, dialogue_id: str) -> dict[str, Any] | None:
        """Geef dialooggraph-definitie terug."""
        try:
            data = self._loader.load_json("dialogue.json")
            dialogues = data.get("dialogues", [])
            for dialogue in dialogues:
                if dialogue.get("dialogue_id") == dialogue_id:
                    return dialogue
            return None
        except FileNotFoundError:
            logger.warning("dialogue.json not found")
            return None

    def get_all_dialogues(self) -> list[dict[str, Any]]:
        """Haal alle dialooggraphs op."""
        try:
            data = self._loader.load_json("dialogue.json")
            return data.get("dialogues", [])
        except FileNotFoundError:
            logger.warning("dialogue.json not found")
            return []

    def get_events_for_zone(self, zone_id: str) -> list[dict[str, Any]]:
        """Filter eventdefinities voor de opgegeven zone."""
        events = self.get_all_events()
        return [event for event in events if event.get("trigger", {}).get("zone_id") == zone_id]

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        """Haal een event op uit events.json."""
        events = self.get_all_events()
        for event in events:
            if event.get("event_id") == event_id:
                return event
        return None

    def get_all_events(self) -> list[dict[str, Any]]:
        """Haal alle events op uit events.json."""
        try:
            data = self._loader.load_json("events.json")
            return data.get("events", [])
        except FileNotFoundError:
            logger.warning("events.json not found, returning empty list")
            return []

    def get_chest(self, chest_id: str) -> dict[str, Any] | None:
        """Haal een chestdefinitie op uit chests.json."""
        try:
            data = self._loader.load_json("chests.json")
            for chest in data.get("chests", []):
                if chest.get("chest_id") == chest_id:
                    return chest
        except FileNotFoundError:
            logger.warning("chests.json not found")
        return None

    def get_enemy_group(self, group_id: str) -> dict[str, Any] | None:
        """Haal een enemy group op uit enemy_groups.json."""
        try:
            data = self._loader.load_json("enemy_groups.json")
            for group in data.get("enemy_groups", []):
                if group.get("group_id") == group_id:
                    return group
        except FileNotFoundError:
            logger.warning("enemy_groups.json not found")
        return None

    # Shop methods (Step 8: Shop System v0)
    def get_shop(self, shop_id: str) -> dict[str, Any] | None:
        """Haal een shop-definitie op uit shops.json."""
        try:
            data = self._loader.load_json("shops.json")
            shops = data.get("shops", [])
            for shop in shops:
                if shop.get("shop_id") == shop_id:
                    return shop
        except FileNotFoundError:
            logger.warning("shops.json not found, shop data not available")
        return None

    def get_all_shops(self) -> list[dict[str, Any]]:
        """Haal alle shop-definities op uit shops.json."""
        try:
            data = self._loader.load_json("shops.json")
            return data.get("shops", [])
        except FileNotFoundError:
            logger.warning("shops.json not found, returning empty list")
            return []


__all__ = ["DataRepository"]
