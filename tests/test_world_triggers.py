"""Tests voor WorldSystem triggers en event/collectable flow."""

from __future__ import annotations

from pathlib import Path

from tri_sarira_rpg.core.entities import Position
from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.world import Trigger, WorldSystem
from tri_sarira_rpg.utils.tiled_loader import ObjectLayer, TiledMap, TiledObject


class DummyFlags:
    def __init__(self) -> None:
        self.flags: set[str] = set()

    def has_flag(self, flag_id: str) -> bool:
        return flag_id in self.flags

    def set_flag(self, flag_id: str) -> None:
        self.flags.add(flag_id)

    def clear_flag(self, flag_id: str) -> None:
        self.flags.discard(flag_id)


class DummyInventory:
    def __init__(self) -> None:
        self.items: dict[str, int] = {}

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        self.items[item_id] = self.items.get(item_id, 0) + quantity


class DummyQuest:
    def __init__(self) -> None:
        self.started: list[str] = []
        self.advanced: list[tuple[str, str | None]] = []
        self.completed: list[str] = []

    def start_quest(self, quest_id: str) -> None:
        self.started.append(quest_id)

    def advance_quest(self, quest_id: str, next_stage_id: str | None = None) -> None:
        self.advanced.append((quest_id, next_stage_id))

    def complete_quest(self, quest_id: str) -> None:
        self.completed.append(quest_id)


class DummyCombat:
    def __init__(self) -> None:
        self.started: list[list[str]] = []

    def start_battle(self, enemy_ids: list[str]) -> None:
        self.started.append(list(enemy_ids))


def make_world(data_dir: Path | None = None) -> WorldSystem:
    repo = DataRepository(data_dir=data_dir)
    world = WorldSystem(data_repository=repo)
    flags = DummyFlags()
    inv = DummyInventory()
    quest = DummyQuest()
    combat = DummyCombat()
    world.attach_systems(flags_system=flags, quest_system=quest, inventory_system=inv, combat_system=combat)
    return world


def test_chest_grants_items_and_sets_flag(tmp_path: Path) -> None:
    world = make_world()

    trigger = Trigger(
        trigger_id="ch_r1_shrine_inner_01",
        trigger_type="ON_INTERACT",
        position=Position(x=0, y=0),
        event_id="ch_r1_shrine_inner_01",
        once_per_save=True,
    )

    world._trigger_event(trigger)

    # Inventory should contain chest loot and flag should be set
    assert world._inventory.items.get("item_gear_simple_staff") == 1
    assert "chest_opened_ch_r1_shrine_inner_01" in world._flags.flags

    # Second trigger should not duplicate loot
    world._trigger_event(trigger)
    assert world._inventory.items.get("item_gear_simple_staff") == 1


def test_start_battle_uses_enemy_group() -> None:
    world = make_world()

    trigger = Trigger(
        trigger_id="ev_shrine_guardian_encounter",
        trigger_type="ON_ENTER",
        position=Position(x=0, y=0),
        event_id="ev_shrine_guardian_encounter",
        once_per_save=True,
    )

    world._trigger_event(trigger)

    # Should start battle with enemies defined in enemy_groups.json
    assert world._combat.started
    group = world._combat.started[-1]
    assert group == ["en_shrine_construct", "en_corrupted_wisp", "en_corrupted_wisp"]


def test_restore_from_save_deactivates_once_per_save_triggers() -> None:
    world = make_world()

    # Stub zone and map to avoid real TMX dependency
    world._data_repository.get_zone = lambda zid: {"id": zid}
    tiled_map = TiledMap(width=5, height=5, tile_width=32, tile_height=32)
    chest = TiledObject(
        id=1,
        name="ch_test",
        type="Chest",
        x=0,
        y=0,
        properties={"chest_id": "ch_test"},
    )
    tiled_map.object_layers["Chests"] = ObjectLayer(name="Chests", objects=[chest])
    world._tiled_loader.load_map = lambda zone_id: tiled_map

    save_state = {
        "current_zone_id": "z_test",
        "player_state": {"position": {"x": 0, "y": 0}, "facing": "S"},
        "triggered_ids": ["ch_test"],
    }

    world.restore_from_save(save_state)

    trigger = world._triggers.get("ch_test")
    assert trigger is not None
    assert trigger.active is False
    assert "ch_test" in world._triggered_ids


def test_quest_actions_dispatch() -> None:
    world = make_world()

    # Build a custom event definition to avoid relying on JSON structure
    world._data_repository.get_event = lambda eid: {
        "event_id": "ev_custom_quest",
        "actions": [
            {"action_type": "QUEST_START", "quest_id": "q_r1_shrine_intro"},
            {"action_type": "QUEST_ADVANCE", "quest_id": "q_r1_shrine_intro", "stage_id": "reach_shrine_clearing"},
            {"action_type": "QUEST_COMPLETE", "quest_id": "q_r1_shrine_intro"},
        ],
    }

    trigger = Trigger(
        trigger_id="ev_custom_quest",
        trigger_type="ON_INTERACT",
        position=Position(x=0, y=0),
        event_id="ev_custom_quest",
        once_per_save=True,
    )

    world._trigger_event(trigger)

    assert world._quest.started == ["q_r1_shrine_intro"]
    assert world._quest.advanced == [("q_r1_shrine_intro", "reach_shrine_clearing")]
    assert world._quest.completed == ["q_r1_shrine_intro"]
