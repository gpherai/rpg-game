"""Tests voor WorldSystem triggers en event/collectable flow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tri_sarira_rpg.core.entities import Position
from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.world import Trigger, WorldSystem
from tri_sarira_rpg.systems.time import TimeSystem
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


from tri_sarira_rpg.systems.quest import QuestStatus


class DummyQuest:
    def __init__(self) -> None:
        self.started: list[str] = []
        self.advanced: list[tuple[str, str | None]] = []
        self.completed: list[str] = []
        self.active: set[str] = set()

    def start_quest(self, quest_id: str) -> None:
        self.started.append(quest_id)
        self.active.add(quest_id)

    def advance_quest(self, quest_id: str, next_stage_id: str | None = None) -> None:
        self.advanced.append((quest_id, next_stage_id))

    def complete_quest(self, quest_id: str) -> None:
        self.completed.append(quest_id)
        self.active.discard(quest_id)

    def get_state(self, quest_id: str) -> Any:
        class S:
            def __init__(self, active: bool) -> None:
                self.status = QuestStatus.ACTIVE if active else QuestStatus.NOT_STARTED

        return S(quest_id in self.active)


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
    messages = []
    world.attach_systems(on_show_message=messages.append)

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
    assert messages == ["You found: Simple Staff (x1)"]

    # Second trigger should not duplicate loot or message
    messages.clear()
    world._trigger_event(trigger)
    assert world._inventory.items.get("item_gear_simple_staff") == 1
    assert not messages, "Message should not be shown for already opened chest"


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


def test_play_cutscene_action_stub() -> None:
    messages: list[str] = []

    def show_message(msg: str) -> None:
        messages.append(msg)

    world = make_world()
    world.attach_systems(on_show_message=show_message)

    action = {
        "action_type": "PLAY_CUTSCENE",
        "cutscene_id": "cs_test",
        "message": "Cutscene placeholder",
    }

    world._execute_event_actions([action])
    assert messages == ["Cutscene placeholder"]


def test_time_advances_on_move() -> None:
    """Elke stap in de overworld moet 1 minuut kosten."""
    time_system = TimeSystem()
    world = WorldSystem()
    world.attach_systems(time_system=time_system)

    # Stub map en speler
    world._current_map = TiledMap(
        width=3, height=3, tile_width=32, tile_height=32, properties={}, object_layers={}, tile_layers={}
    )
    from tri_sarira_rpg.core.entities import Position
    from tri_sarira_rpg.systems.world import PlayerState

    world._player = PlayerState(zone_id="z_test", position=Position(x=1, y=1))
    start_time = time_system.state.time_of_day

    moved = world.move_player(1, 0)

    assert moved is True
    assert time_system.state.time_of_day == start_time + 1


def test_time_advances_on_portal_transition(monkeypatch) -> None:
    """Portal/zone wissel moet 1 minuut toevoegen bovenop de stap."""
    time_system = TimeSystem()
    world = WorldSystem(time_system=time_system)

    # Maak een map met een portal op (0,0)
    portal = TiledObject(
        id=1,
        name="portal_to_next",
        type="Portal",
        x=0,
        y=0,
        width=32,
        height=32,
        properties={"target_zone_id": "z_next", "target_spawn_id": None},
    )
    world._current_map = TiledMap(
        width=2,
        height=1,
        tile_width=32,
        tile_height=32,
        properties={},
        object_layers={"Portals": ObjectLayer(name="Portals", objects=[portal])},
    )

    from tri_sarira_rpg.core.entities import Position
    from tri_sarira_rpg.systems.world import PlayerState

    world._player = PlayerState(zone_id="z_curr", position=Position(x=0, y=0))

    # Stub repo + loader om echte fileloads te vermijden
    world._data_repository.get_zone = lambda *_: {"id": "z_next"}  # type: ignore[attr-defined]
    world._tiled_loader.load_map = (
        lambda *_: TiledMap(
            width=1, height=1, tile_width=32, tile_height=32, properties={}, object_layers={}
        )
    )

    start_time = time_system.state.time_of_day
    # Stap naar portal-tegel (x=1,y=0) geeft +1 minuut
    moved = world.move_player(1, 0)
    assert moved is True
    world._check_portal_transition()
    assert time_system.state.time_of_day == start_time + 1


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


def test_quest_actions_dispatch_and_show_messages() -> None:
    world = make_world()
    messages = []
    world.attach_systems(on_show_message=messages.append)

    # Mock the repository to return quest titles
    def get_quest_mock(quest_id: str) -> dict[str, Any] | None:
        if quest_id == "q_r1_shrine_purification":
            return {"title": "Purification Quest"}
        return None

    world._data_repository.get_quest = get_quest_mock

    # Build a custom event definition
    event_def = {
        "event_id": "ev_custom_quest",
        "actions": [
            {"action_type": "QUEST_START", "quest_id": "q_r1_shrine_purification"},
            {"action_type": "QUEST_ADVANCE", "quest_id": "q_r1_shrine_purification", "stage_id": "cleanse_shrine"},
            {"action_type": "QUEST_COMPLETE", "quest_id": "q_r1_shrine_purification"},
        ],
    }
    world._data_repository.get_event = lambda eid: event_def

    trigger = Trigger(
        trigger_id="ev_custom_quest",
        trigger_type="ON_INTERACT",
        position=Position(x=0, y=0),
        event_id="ev_custom_quest",
    )

    world._trigger_event(trigger)

    # Check system calls
    assert world._quest.started == ["q_r1_shrine_purification"]
    assert world._quest.advanced == [("q_r1_shrine_purification", "cleanse_shrine")]
    assert world._quest.completed == ["q_r1_shrine_purification"]

    # Check UI messages
    assert messages == [
        "Quest Started: Purification Quest",
        "Quest Updated: Purification Quest",
        "Quest Completed: Purification Quest",
    ]
