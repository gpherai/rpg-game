"""Tests for Shrine Dungeon Slice v0 (F10)."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.utils.tiled_loader import TiledLoader


@pytest.fixture
def data_repository() -> DataRepository:
    """Repository for loading game data."""
    return DataRepository()


@pytest.fixture
def tiled_loader() -> TiledLoader:
    """Tiled loader for loading maps."""
    maps_dir = Path(__file__).parent.parent / "maps"
    return TiledLoader(maps_dir=maps_dir)


def test_shrine_inner_zone_exists(data_repository: DataRepository) -> None:
    """Test dat z_r1_shrine_inner zone bestaat in zones.json."""
    zone = data_repository.get_zone("z_r1_shrine_inner")
    assert zone is not None, "z_r1_shrine_inner zone should exist"
    assert zone["id"] == "z_r1_shrine_inner"
    assert zone["type"] == "dungeon"
    assert zone["recommended_level"] == 5
    assert "z_r1_shrine_clearing" in zone["connected_zones"]


def test_shrine_inner_map_loads(tiled_loader: TiledLoader) -> None:
    """Test dat z_r1_shrine_inner.tmx succesvol laadt."""
    tiled_map = tiled_loader.load_map("z_r1_shrine_inner")
    assert tiled_map is not None
    assert tiled_map.width >= 20, "Map should have reasonable width"
    assert tiled_map.height >= 15, "Map should have reasonable height"


def test_shrine_enemies_exist(data_repository: DataRepository) -> None:
    """Test dat alle shrine enemies bestaan."""
    shrine_enemies = [
        "en_corrupted_wisp",
        "en_shrine_construct",
        "en_shadow_apparition",
        "en_shrine_guardian",
    ]

    for enemy_id in shrine_enemies:
        enemy = data_repository.get_enemy(enemy_id)
        assert enemy is not None, f"Enemy {enemy_id} should exist"
        assert "shrine" in enemy["tags"], f"Enemy {enemy_id} should have 'shrine' tag"


def test_enemy_groups_file_exists() -> None:
    """Test dat enemy_groups.json bestaat en valide JSON is."""
    groups_file = Path(__file__).parent.parent / "data" / "enemy_groups.json"
    assert groups_file.exists(), "enemy_groups.json should exist"

    with open(groups_file) as f:
        data = json.load(f)

    assert "enemy_groups" in data
    assert len(data["enemy_groups"]) > 0


def test_shrine_enemy_groups_exist() -> None:
    """Test dat shrine enemy groups correct zijn gedefinieerd."""
    groups_file = Path(__file__).parent.parent / "data" / "enemy_groups.json"

    with open(groups_file) as f:
        data = json.load(f)

    shrine_groups = [g for g in data["enemy_groups"] if "shrine" in g["tags"]]
    assert len(shrine_groups) >= 5, "Should have at least 5 shrine enemy groups"

    # Check for specific groups
    group_ids = [g["group_id"] for g in shrine_groups]
    assert "eg_r1_shrine_wisps" in group_ids
    assert "eg_r1_shrine_constructs" in group_ids
    assert "eg_r1_shrine_elite_trio" in group_ids
    assert "eg_r1_shrine_boss_encounter" in group_ids


def test_shrine_enemy_groups_have_valid_enemies(data_repository: DataRepository) -> None:
    """Test dat alle enemies in enemy groups bestaan."""
    groups_file = Path(__file__).parent.parent / "data" / "enemy_groups.json"

    with open(groups_file) as f:
        data = json.load(f)

    for group in data["enemy_groups"]:
        for enemy_id in group["enemies"]:
            enemy = data_repository.get_enemy(enemy_id)
            assert enemy is not None, f"Enemy {enemy_id} in group {group['group_id']} should exist"


def test_shrine_loot_tables_exist() -> None:
    """Test dat shrine loot tables bestaan."""
    loot_file = Path(__file__).parent.parent / "data" / "loot_tables.json"

    with open(loot_file) as f:
        data = json.load(f)

    shrine_tables = [
        "lt_r1_shrine_spirits",
        "lt_r1_shrine_constructs",
        "lt_r1_shrine_guardian",
    ]

    loot_table_ids = [lt["loot_table_id"] for lt in data["loot_tables"]]

    for table_id in shrine_tables:
        assert table_id in loot_table_ids, f"Loot table {table_id} should exist"


def test_shrine_chests_exist() -> None:
    """Test dat shrine chests correct zijn gedefinieerd."""
    chests_file = Path(__file__).parent.parent / "data" / "chests.json"

    with open(chests_file) as f:
        data = json.load(f)

    shrine_chests = [
        "ch_r1_shrine_inner_01",
        "ch_r1_shrine_inner_02",
        "ch_r1_shrine_inner_03",
        "ch_r1_shrine_inner_completion",
    ]

    chest_ids = [c["chest_id"] for c in data["chests"]]

    for chest_id in shrine_chests:
        assert chest_id in chest_ids, f"Chest {chest_id} should exist"


def test_shrine_chests_have_valid_items(data_repository: DataRepository) -> None:
    """Test dat alle items in shrine chests bestaan."""
    chests_file = Path(__file__).parent.parent / "data" / "chests.json"

    with open(chests_file) as f:
        data = json.load(f)

    shrine_chests = [c for c in data["chests"] if c["zone_id"] == "z_r1_shrine_inner"]

    for chest in shrine_chests:
        for item_entry in chest["contents"]:
            item = data_repository.get_item(item_entry["item_id"])
            assert item is not None, f"Item {item_entry['item_id']} in chest {chest['chest_id']} should exist"


def test_shrine_chests_contain_gear_upgrades(data_repository: DataRepository) -> None:
    """Test dat minstens één chest een gear upgrade bevat."""
    chests_file = Path(__file__).parent.parent / "data" / "chests.json"

    with open(chests_file) as f:
        data = json.load(f)

    shrine_chests = [c for c in data["chests"] if c["zone_id"] == "z_r1_shrine_inner"]

    gear_found = False
    for chest in shrine_chests:
        for item_entry in chest["contents"]:
            item = data_repository.get_item(item_entry["item_id"])
            if item and item.get("type") == "gear":
                gear_found = True
                break
        if gear_found:
            break

    assert gear_found, "At least one shrine chest should contain a gear item"


def test_shrine_quest_exists(data_repository: DataRepository) -> None:
    """Test dat de shrine quest bestaat."""
    quest = data_repository.get_quest("q_r1_shrine_silent")
    assert quest is not None, "Quest q_r1_shrine_silent should exist"
    assert quest["quest_type"] == "MSQ"
    assert quest["tri_focus_primary"] == "SPIRIT"
    assert len(quest["stages"]) >= 4, "Quest should have multiple stages"


def test_shrine_events_exist() -> None:
    """Test dat alle shrine events bestaan."""
    events_file = Path(__file__).parent.parent / "data" / "events.json"

    with open(events_file) as f:
        data = json.load(f)

    shrine_event_ids = [
        "ev_shrine_encounter_wisps",
        "ev_shrine_encounter_constructs",
        "ev_shrine_encounter_elite",
        "ev_shrine_puzzle_pedestal_01",
        "ev_shrine_puzzle_pedestal_02",
        "ev_shrine_boss_guardian",
        "ev_shrine_completion",
    ]

    event_ids = [e["event_id"] for e in data["events"]]

    for event_id in shrine_event_ids:
        assert event_id in event_ids, f"Event {event_id} should exist"


def test_shrine_map_has_required_layers(tiled_loader: TiledLoader) -> None:
    """Test dat de shrine map alle vereiste layers heeft."""
    tiled_map = tiled_loader.load_map("z_r1_shrine_inner")

    # Check for required tile layers
    assert "Ground" in tiled_map.tile_layers, "Map should have Ground layer"
    assert "Collision" in tiled_map.tile_layers, "Map should have Collision layer"


def test_shrine_map_has_spawn_points(tiled_loader: TiledLoader) -> None:
    """Test dat de shrine map spawn points heeft."""
    tiled_map = tiled_loader.load_map("z_r1_shrine_inner")

    # Check if Spawns layer exists
    assert "Spawns" in tiled_map.object_layers, "Map should have Spawns object layer"

    default_spawn = tiled_map.get_default_spawn()
    assert default_spawn is not None, "Map should have a default spawn point"


def test_shrine_map_has_portals(tiled_loader: TiledLoader) -> None:
    """Test dat de shrine map portals heeft."""
    tiled_map = tiled_loader.load_map("z_r1_shrine_inner")

    # Check if Portals layer exists
    assert "Portals" in tiled_map.object_layers, "Map should have Portals object layer"


def test_shrine_map_has_chests(tiled_loader: TiledLoader) -> None:
    """Test dat de shrine map chest objects heeft."""
    tiled_map = tiled_loader.load_map("z_r1_shrine_inner")

    # Check if Chests layer exists
    assert "Chests" in tiled_map.object_layers, "Map should have Chests object layer"


def test_shrine_map_has_events(tiled_loader: TiledLoader) -> None:
    """Test dat de shrine map event triggers heeft."""
    tiled_map = tiled_loader.load_map("z_r1_shrine_inner")

    # Check if Events layer exists
    assert "Events" in tiled_map.object_layers, "Map should have Events object layer"


def test_shrine_map_has_shrine_core_marker(tiled_loader: TiledLoader) -> None:
    """Test dat de shrine map een SHRINE_CORE marker heeft."""
    tiled_map = tiled_loader.load_map("z_r1_shrine_inner")

    # Check if Markers layer exists
    assert "Markers" in tiled_map.object_layers, "Map should have Markers object layer"


def test_shrine_completion_flag_logic() -> None:
    """Test dat de shrine completion logic correct is opgezet."""
    events_file = Path(__file__).parent.parent / "data" / "events.json"

    with open(events_file) as f:
        data = json.load(f)

    completion_event = next(
        (e for e in data["events"] if e["event_id"] == "ev_shrine_completion"),
        None
    )

    assert completion_event is not None, "Shrine completion event should exist"

    # Check that it sets the cleared flag
    set_flag_actions = [
        a for a in completion_event["actions"]
        if a.get("action_type") == "SET_FLAG"
        and a.get("flag_id") == "flag_r1_shrine_inner_cleared"
    ]

    assert len(set_flag_actions) > 0, "Completion event should set flag_r1_shrine_inner_cleared"
