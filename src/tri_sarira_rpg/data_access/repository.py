"""Toegangslayer voor JSON-content."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .exceptions import (
    DataEncodingError,
    DataFileNotFoundError,
    DataParseError,
    DataPermissionError,
)
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
        self._raw_data: dict[str, dict[str, Any]] = {}
        self._reset_cache()

    def _reset_cache(self) -> None:
        """Reset in-memory caches."""
        self._actors: list[dict[str, Any]] | None = None
        self._actors_by_id: dict[str, dict[str, Any]] = {}

        self._enemies: list[dict[str, Any]] | None = None
        self._enemies_by_id: dict[str, dict[str, Any]] = {}

        self._enemy_groups: list[dict[str, Any]] | None = None
        self._enemy_groups_by_id: dict[str, dict[str, Any]] = {}

        self._zones: list[dict[str, Any]] | None = None
        self._zones_by_id: dict[str, dict[str, Any]] = {}

        self._npcs: list[dict[str, Any]] | None = None
        self._npcs_by_id: dict[str, dict[str, Any]] = {}
        self._npc_schedules: list[dict[str, Any]] | None = None

        self._skills: list[dict[str, Any]] | None = None
        self._skills_by_id: dict[str, dict[str, Any]] = {}

        self._items: list[dict[str, Any]] | None = None
        self._items_by_id: dict[str, dict[str, Any]] = {}

        self._quests: list[dict[str, Any]] | None = None
        self._quests_by_id: dict[str, dict[str, Any]] = {}

        self._dialogues: list[dict[str, Any]] | None = None
        self._dialogues_by_id: dict[str, dict[str, Any]] = {}

        self._events: list[dict[str, Any]] | None = None
        self._events_by_id: dict[str, dict[str, Any]] = {}

        self._chests: list[dict[str, Any]] | None = None
        self._chests_by_id: dict[str, dict[str, Any]] = {}

        self._shops: list[dict[str, Any]] | None = None
        self._shops_by_id: dict[str, dict[str, Any]] = {}

        self._loot_tables: list[dict[str, Any]] | None = None

    def load_and_validate_all(self) -> bool:
        """Laad en valideer alle data-bestanden.

        Returns
        -------
        bool
            True als alles OK is, False bij fouten
        """
        self._validation_errors.clear()
        self._raw_data.clear()
        self._reset_cache()
        all_ok = True

        def add_error(message: str) -> None:
            nonlocal all_ok
            self._validation_errors.append(message)
            all_ok = False

        # Load required data into caches (collect errors instead of raising)
        self._ensure_actors(errors=self._validation_errors, required=True)
        self._ensure_enemies(errors=self._validation_errors, required=True)
        self._ensure_enemy_groups(errors=self._validation_errors, required=True)
        self._ensure_items(errors=self._validation_errors, required=True)
        self._ensure_skills(errors=self._validation_errors, required=True)
        self._ensure_zones(errors=self._validation_errors, required=True)
        self._ensure_npcs(errors=self._validation_errors, required=True)
        self._ensure_npc_schedules(errors=self._validation_errors, required=True)
        self._ensure_quests(errors=self._validation_errors, required=True)
        self._ensure_dialogues(errors=self._validation_errors, required=True)
        self._ensure_chests(errors=self._validation_errors, required=True)
        self._ensure_loot_tables(errors=self._validation_errors, required=True)
        self._ensure_events(errors=self._validation_errors, required=True)
        self._ensure_shops(errors=self._validation_errors, required=True)
        if self._validation_errors:
            all_ok = False

        # Basic required-key validation for simple types using raw data
        for filename, data_type in [
            ("actors.json", "actors"),
            ("enemies.json", "enemies"),
            ("zones.json", "zones"),
            ("skills.json", "skills"),
            ("items.json", "items"),
        ]:
            data = self._raw_data.get(filename)
            if not data:
                continue
            required = self.REQUIRED_KEYS.get(data_type, ["id", "name"])
            errors = self._loader.validate_data(data, data_type, required)
            if errors:
                for error in errors:
                    add_error(error)

        # Build lookup sets for cross-ref checks
        actors = self._actors or []
        enemies = self._enemies or []
        items = self._items or []
        skills = self._skills or []
        zones = self._zones or []
        npc_meta = self._npcs or []
        npc_schedules = self._npc_schedules or []
        quest_defs = self._quests or []
        enemy_groups = self._enemy_groups or []

        actor_ids = {a.get("id") for a in actors if a.get("id")}
        enemy_ids = {e.get("id") for e in enemies if e.get("id")}
        item_ids = {i.get("id") for i in items if i.get("id")}
        skill_ids = {s.get("id") for s in skills if s.get("id")}
        zone_ids = {z.get("id") for z in zones if z.get("id")}
        npc_ids = {n.get("npc_id") for n in npc_meta if n.get("npc_id")}
        quest_ids = {q.get("quest_id") for q in quest_defs if q.get("quest_id")}

        # npc_meta basic check (actor_id optional)
        for npc in npc_meta:
            if "npc_id" not in npc:
                add_error("npc_meta.json: entry missing npc_id")
            actor_id = npc.get("actor_id")
            if actor_id and actor_id not in actor_ids:
                add_error(f"npc_meta.json: actor_id {actor_id} not found for npc {npc.get('npc_id')}")

        # Skills referenced by actors/enemies must exist
        for actor in actors:
            actor_id = actor.get("id", "<unknown>")
            for skill_id in actor.get("starting_skills", []):
                if skill_id not in skill_ids:
                    add_error(f"actors.json: actor {actor_id} references unknown skill_id {skill_id}")

        for enemy in enemies:
            enemy_id = enemy.get("id", "<unknown>")
            for skill_id in enemy.get("skills", []):
                if skill_id not in skill_ids:
                    add_error(f"enemies.json: enemy {enemy_id} references unknown skill_id {skill_id}")

        # npc_schedules: npc_id and zone_id must exist
        for sched in npc_schedules:
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
        dialogue_entries = self._dialogues or []
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
        for chest in self._chests or []:
            cid = chest.get("chest_id")
            zone_id = chest.get("zone_id")
            if zone_id and zone_id not in zone_ids:
                add_error(f"chests.json: chest {cid} has unknown zone_id {zone_id}")
            for entry in chest.get("contents", []):
                iid = entry.get("item_id")
                if iid and iid not in item_ids:
                    add_error(f"chests.json: chest {cid} references unknown item_id {iid}")

        # Loot tables: item_ids must exist
        for table in self._loot_tables or []:
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
        for event in self._events or []:
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
        for shop in self._shops or []:
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
        self._ensure_actors()
        return self._actors_by_id.get(actor_id)

    def get_all_actors(self) -> list[dict[str, Any]]:
        """Haal alle actordefinities op."""
        self._ensure_actors()
        return list(self._actors or [])

    # Enemy methods
    def get_enemy(self, enemy_id: str) -> dict[str, Any] | None:
        """Haal een enemydefinitie op."""
        self._ensure_enemies()
        return self._enemies_by_id.get(enemy_id)

    def get_all_enemies(self) -> list[dict[str, Any]]:
        """Haal alle enemydefinities op."""
        self._ensure_enemies()
        return list(self._enemies or [])

    # Enemy groups
    def get_enemy_group(self, group_id: str) -> dict[str, Any] | None:
        """Haal een enemy group op uit enemy_groups.json."""
        self._ensure_enemy_groups()
        return self._enemy_groups_by_id.get(group_id)

    # Zone methods
    def get_zone(self, zone_id: str) -> dict[str, Any] | None:
        """Haal een zonedefinitie op."""
        self._ensure_zones()
        return self._zones_by_id.get(zone_id)

    def get_all_zones(self) -> list[dict[str, Any]]:
        """Haal alle zonedefinities op."""
        self._ensure_zones()
        return list(self._zones or [])

    # NPC metadata methods
    def get_npc(self, npc_id: str) -> dict[str, Any] | None:
        """Haal een NPC-definitie op uit npc_meta.json."""
        self._ensure_npcs()
        return self._npcs_by_id.get(npc_id)

    def get_all_npcs(self) -> list[dict[str, Any]]:
        """Haal alle NPC-definities op uit npc_meta.json."""
        self._ensure_npcs()
        return list(self._npcs or [])

    def get_npc_meta(self) -> dict[str, Any]:
        """Haal de volledige npc_meta.json op voor PartySystem initialisatie."""
        self._ensure_npcs()
        return {"npcs": list(self._npcs or [])}

    # Skill methods (Step 5: Combat v0)
    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Haal een skill-definitie op uit skills.json."""
        self._ensure_skills()
        return self._skills_by_id.get(skill_id)

    def get_all_skills(self) -> list[dict[str, Any]]:
        """Haal alle skill-definities op uit skills.json."""
        self._ensure_skills()
        return list(self._skills or [])

    # Item methods (Step 5: Combat v0)
    def get_item(self, item_id: str) -> dict[str, Any] | None:
        """Haal een item-definitie op uit items.json."""
        self._ensure_items()
        return self._items_by_id.get(item_id)

    def get_all_items(self) -> list[dict[str, Any]]:
        """Haal alle item-definities op uit items.json."""
        self._ensure_items()
        return list(self._items or [])

    def get_quest(self, quest_id: str) -> dict[str, Any] | None:
        """Haal questdata op voor questsystemen."""
        self._ensure_quests()
        return self._quests_by_id.get(quest_id)

    def get_all_quests(self) -> list[dict[str, Any]]:
        """Haal alle quests op."""
        self._ensure_quests()
        return list(self._quests or [])

    def get_dialogue(self, dialogue_id: str) -> dict[str, Any] | None:
        """Geef dialooggraph-definitie terug."""
        self._ensure_dialogues()
        return self._dialogues_by_id.get(dialogue_id)

    def get_all_dialogues(self) -> list[dict[str, Any]]:
        """Haal alle dialooggraphs op."""
        self._ensure_dialogues()
        return list(self._dialogues or [])

    def get_events_for_zone(self, zone_id: str) -> list[dict[str, Any]]:
        """Filter eventdefinities voor de opgegeven zone."""
        self._ensure_events()
        return [
            event for event in (self._events or []) if event.get("trigger", {}).get("zone_id") == zone_id
        ]

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        """Haal een event op uit events.json."""
        self._ensure_events()
        return self._events_by_id.get(event_id)

    def get_all_events(self) -> list[dict[str, Any]]:
        """Haal alle events op uit events.json."""
        self._ensure_events()
        return list(self._events or [])

    def get_chest(self, chest_id: str) -> dict[str, Any] | None:
        """Haal een chestdefinitie op uit chests.json."""
        self._ensure_chests()
        return self._chests_by_id.get(chest_id)

    # Shop methods (Step 8: Shop System v0)
    def get_shop(self, shop_id: str) -> dict[str, Any] | None:
        """Haal een shop-definitie op uit shops.json."""
        self._ensure_shops()
        return self._shops_by_id.get(shop_id)

    def get_all_shops(self) -> list[dict[str, Any]]:
        """Haal alle shop-definities op uit shops.json."""
        self._ensure_shops()
        return list(self._shops or [])

    # ------------------------------------------------------------------
    # Internal loaders with caching
    # ------------------------------------------------------------------

    def _load_entries(
        self,
        filename: str,
        top_key: str,
        *,
        errors: list[str] | None = None,
        required: bool = False,
    ) -> list[dict[str, Any]]:
        try:
            data = self._loader.load_json(filename)
            self._raw_data[filename] = data
        except (DataFileNotFoundError, DataParseError, DataPermissionError, DataEncodingError) as exc:
            message = f"{'Required ' if required else ''}data file missing: {filename} ({exc})"
            if errors is not None:
                errors.append(message)
            else:
                logger.warning(message)
            return []

        entries = data.get(top_key, [])
        if not isinstance(entries, list):
            if errors is not None:
                errors.append(f"Expected '{top_key}' to be a list in {filename}")
            return []
        return [entry for entry in entries if isinstance(entry, dict)]

    def _ensure_actors(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._actors is not None:
            return
        self._actors = self._load_entries("actors.json", "actors", errors=errors, required=required)
        self._actors_by_id = {actor["id"]: actor for actor in self._actors if "id" in actor}

    def _ensure_enemies(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._enemies is not None:
            return
        self._enemies = self._load_entries("enemies.json", "enemies", errors=errors, required=required)
        self._enemies_by_id = {enemy["id"]: enemy for enemy in self._enemies if "id" in enemy}

    def _ensure_enemy_groups(
        self, errors: list[str] | None = None, *, required: bool = False
    ) -> None:
        if self._enemy_groups is not None:
            return
        self._enemy_groups = self._load_entries(
            "enemy_groups.json", "enemy_groups", errors=errors, required=required
        )
        self._enemy_groups_by_id = {
            group["group_id"]: group for group in self._enemy_groups if "group_id" in group
        }

    def _ensure_zones(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._zones is not None:
            return
        self._zones = self._load_entries("zones.json", "zones", errors=errors, required=required)
        self._zones_by_id = {zone["id"]: zone for zone in self._zones if "id" in zone}

    def _ensure_npcs(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._npcs is not None:
            return
        self._npcs = self._load_entries("npc_meta.json", "npcs", errors=errors, required=required)
        self._npcs_by_id = {npc["npc_id"]: npc for npc in self._npcs if "npc_id" in npc}

    def _ensure_npc_schedules(
        self, errors: list[str] | None = None, *, required: bool = False
    ) -> None:
        if self._npc_schedules is not None:
            return
        self._npc_schedules = self._load_entries(
            "npc_schedules.json", "npc_schedules", errors=errors, required=required
        )

    def _ensure_skills(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._skills is not None:
            return
        self._skills = self._load_entries("skills.json", "skills", errors=errors, required=required)
        self._skills_by_id = {skill["id"]: skill for skill in self._skills if "id" in skill}

    def _ensure_items(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._items is not None:
            return
        self._items = self._load_entries("items.json", "items", errors=errors, required=required)
        self._items_by_id = {item["id"]: item for item in self._items if "id" in item}

    def _ensure_quests(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._quests is not None:
            return
        self._quests = self._load_entries("quests.json", "quests", errors=errors, required=required)
        self._quests_by_id = {
            quest["quest_id"]: quest for quest in self._quests if "quest_id" in quest
        }

    def _ensure_dialogues(
        self, errors: list[str] | None = None, *, required: bool = False
    ) -> None:
        if self._dialogues is not None:
            return
        self._dialogues = self._load_entries(
            "dialogue.json", "dialogues", errors=errors, required=required
        )
        self._dialogues_by_id = {
            dlg["dialogue_id"]: dlg for dlg in self._dialogues if "dialogue_id" in dlg
        }

    def _ensure_chests(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._chests is not None:
            return
        self._chests = self._load_entries("chests.json", "chests", errors=errors, required=required)
        self._chests_by_id = {chest["chest_id"]: chest for chest in self._chests if "chest_id" in chest}

    def _ensure_loot_tables(
        self, errors: list[str] | None = None, *, required: bool = False
    ) -> None:
        if self._loot_tables is not None:
            return
        self._loot_tables = self._load_entries(
            "loot_tables.json", "loot_tables", errors=errors, required=required
        )

    def _ensure_events(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._events is not None:
            return
        self._events = self._load_entries("events.json", "events", errors=errors, required=required)
        self._events_by_id = {event["event_id"]: event for event in self._events if "event_id" in event}

    def _ensure_shops(self, errors: list[str] | None = None, *, required: bool = False) -> None:
        if self._shops is not None:
            return
        self._shops = self._load_entries("shops.json", "shops", errors=errors, required=required)
        self._shops_by_id = {shop["shop_id"]: shop for shop in self._shops if "shop_id" in shop}


__all__ = ["DataRepository"]
