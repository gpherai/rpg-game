"""Tests voor SaveSystem roundtrip (save  load  verify)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.quest import QuestSystem
from tri_sarira_rpg.systems.save import SaveSystem
from tri_sarira_rpg.systems.state import GameStateFlags
from tri_sarira_rpg.systems.time import TimeSystem
from tri_sarira_rpg.systems.world import WorldSystem


@pytest.fixture
def test_save_dir(tmp_path: Path) -> Path:
    """Create a temporary save directory."""
    save_dir = tmp_path / "saves"
    save_dir.mkdir()
    return save_dir


@pytest.fixture
def data_repository() -> DataRepository:
    """Create a DataRepository for testing."""
    return DataRepository()


@pytest.fixture
def party_system(data_repository: DataRepository) -> PartySystem:
    """Create a PartySystem with test data."""
    npc_meta = data_repository.get_npc_meta()
    party = PartySystem(data_repository, npc_meta)

    # Add main character
    party.add_to_reserve_pool("npc_mc_adhira", "mc_adhira", tier="MC")
    party.add_to_active_party("npc_mc_adhira")

    return party


@pytest.fixture
def world_system(data_repository: DataRepository) -> WorldSystem:
    """Create a WorldSystem for testing."""
    project_root = Path.cwd()
    if (project_root / "src").exists():
        maps_dir = project_root / "maps"
    else:
        maps_dir = Path("maps")

    world = WorldSystem(data_repository=data_repository, maps_dir=maps_dir)
    world.load_zone("z_r1_chandrapur_town")
    return world


@pytest.fixture
def time_system() -> TimeSystem:
    """Create a TimeSystem for testing."""
    time_sys = TimeSystem()
    # Advance time a bit for testing
    time_sys.advance_time(120)  # 2 hours
    return time_sys


@pytest.fixture
def inventory_system() -> InventorySystem:
    """Create an InventorySystem with test data."""
    inventory = InventorySystem()
    inventory.add_item("item_small_herb", 5)
    inventory.add_item("item_medium_herb", 2)
    inventory.add_item("item_stamina_tonic", 3)
    return inventory


@pytest.fixture
def flags_system() -> GameStateFlags:
    """Create a GameStateFlags with test data."""
    flags = GameStateFlags()
    flags.set_flag("test_flag_1")
    flags.set_flag("test_flag_2")
    return flags


@pytest.fixture
def quest_system(
    party_system: PartySystem, inventory_system: InventorySystem, data_repository: DataRepository
) -> QuestSystem:
    """Create a QuestSystem with test data."""
    quest = QuestSystem(party_system, inventory_system)
    quest.load_definitions(data_repository)

    # Start a quest
    quest.start_quest("q_r1_shrine_intro")

    return quest


@pytest.fixture
def save_system(
    party_system: PartySystem,
    world_system: WorldSystem,
    time_system: TimeSystem,
    inventory_system: InventorySystem,
    flags_system: GameStateFlags,
    quest_system: QuestSystem,
    test_save_dir: Path,
) -> SaveSystem:
    """Create a SaveSystem with all subsystems."""
    save_sys = SaveSystem(
        party_system=party_system,
        world_system=world_system,
        time_system=time_system,
        inventory_system=inventory_system,
        flags_system=flags_system,
        quest_system=quest_system,
    )
    # Override save directory to use test directory
    save_sys._save_dir = test_save_dir
    return save_sys


def test_build_save_creates_valid_structure(save_system: SaveSystem) -> None:
    """Test dat build_save een valide save structure aanmaakt."""
    save_data = save_system.build_save(play_time=123.45)

    # Check top-level structure
    assert "meta" in save_data
    assert "time_state" in save_data
    assert "world_state" in save_data
    assert "party_state" in save_data
    assert "inventory_state" in save_data
    assert "flags_state" in save_data
    assert "quest_state" in save_data

    # Check meta
    meta = save_data["meta"]
    assert meta["schema_version"] == 1
    assert meta["play_time"] == 123.45
    assert "created_at" in meta

    # Check that subsystems contributed data
    assert save_data["time_state"]  # Should not be empty
    assert save_data["world_state"]  # Should not be empty
    assert save_data["party_state"]  # Should not be empty


def test_save_to_file_creates_json(save_system: SaveSystem, test_save_dir: Path) -> None:
    """Test dat save_to_file een JSON bestand aanmaakt."""
    save_data = save_system.build_save()

    success = save_system.save_to_file(1, save_data)
    assert success is True

    # Verify file exists
    save_file = test_save_dir / "save_slot_1.json"
    assert save_file.exists()

    # Verify it's valid JSON
    with open(save_file) as f:
        loaded = json.load(f)

    assert loaded == save_data


def test_load_from_file_returns_data(save_system: SaveSystem, test_save_dir: Path) -> None:
    """Test dat load_from_file save data teruggeeft."""
    original_data = save_system.build_save(play_time=100.0)
    save_system.save_to_file(1, original_data)

    # Load it back
    loaded_data = save_system.load_from_file(1)

    assert loaded_data is not None
    assert loaded_data["meta"]["play_time"] == 100.0
    assert loaded_data == original_data


def test_load_from_file_nonexistent_returns_none(save_system: SaveSystem) -> None:
    """Test dat load_from_file None teruggeeft voor nonexistent slot."""
    loaded_data = save_system.load_from_file(99)
    assert loaded_data is None


def test_slot_exists(save_system: SaveSystem) -> None:
    """Test dat slot_exists correct werkt."""
    assert save_system.slot_exists(1) is False

    # Save to slot 1
    save_data = save_system.build_save()
    save_system.save_to_file(1, save_data)

    assert save_system.slot_exists(1) is True
    assert save_system.slot_exists(2) is False


def test_save_metadata_written_and_loaded(save_system: SaveSystem, test_save_dir: Path) -> None:
    """Test dat metadata wordt weggeschreven en geladen."""
    save_data = save_system.build_save()
    save_system.save_to_file(1, save_data)

    meta_path = test_save_dir / "save_slot_1_meta.json"
    assert meta_path.exists()

    metadata = save_system.load_metadata(1)
    assert metadata is not None
    assert metadata["slot_id"] == 1
    assert metadata["zone_id"] == save_data["world_state"]["current_zone_id"]
    assert metadata["day_index"] == save_data["time_state"]["day_index"]
    assert "saved_at" in metadata


def test_load_metadata_fallback_when_missing_file(save_system: SaveSystem, test_save_dir: Path) -> None:
    """Als metadata ontbreekt maar de save bestaat, wordt er fallback-metadata opgebouwd."""
    save_data = save_system.build_save()
    save_system.save_to_file(1, save_data)

    # Verwijder meta-bestand om fallback te forceren
    meta_path = test_save_dir / "save_slot_1_meta.json"
    if meta_path.exists():
        meta_path.unlink()

    metadata = save_system.load_metadata(1)
    assert metadata is not None
    assert metadata["zone_id"] == save_data["world_state"]["current_zone_id"]
    assert metadata["day_index"] == save_data["time_state"]["day_index"]


def test_party_state_roundtrip(save_system: SaveSystem, party_system: PartySystem) -> None:
    """Test dat party state correct wordt gesaved en restored."""
    # Get initial state
    initial_active = party_system.get_active_party()
    initial_member = initial_active[0]
    initial_actor_id = initial_member.actor_id

    # Save
    save_data = save_system.build_save()
    assert "party_state" in save_data
    party_state = save_data["party_state"]
    assert "active_party" in party_state
    assert any(m["actor_id"] == initial_actor_id for m in party_state["active_party"])

    # Create new party system
    data_repo = DataRepository()
    npc_meta = data_repo.get_npc_meta()
    new_party = PartySystem(data_repo, npc_meta)

    # Restore
    new_party.restore_from_save(party_state)

    # Verify
    restored_active = new_party.get_active_party()
    assert len(restored_active) == len(initial_active)
    assert restored_active[0].actor_id == initial_actor_id


def test_world_state_roundtrip(save_system: SaveSystem, world_system: WorldSystem) -> None:
    """Test dat world state correct wordt gesaved en restored."""
    # Get initial state
    initial_zone = world_system.current_zone_id
    initial_pos = world_system.player.position

    # Save
    save_data = save_system.build_save()
    world_state = save_data["world_state"]
    assert world_state["current_zone_id"] == initial_zone

    # Create new world system
    data_repo = DataRepository()
    project_root = Path.cwd()
    maps_dir = project_root / "maps" if (project_root / "src").exists() else Path("maps")
    new_world = WorldSystem(data_repository=data_repo, maps_dir=maps_dir)

    # Restore
    new_world.restore_from_save(world_state)

    # Verify
    assert new_world.current_zone_id == initial_zone
    assert new_world.player.position.x == initial_pos.x
    assert new_world.player.position.y == initial_pos.y


def test_time_state_roundtrip(save_system: SaveSystem, time_system: TimeSystem) -> None:
    """Test dat time state correct wordt gesaved en restored."""
    # Get initial state
    initial_day = time_system.state.day_index
    initial_time = time_system.state.time_of_day

    # Save
    save_data = save_system.build_save()
    time_state = save_data["time_state"]
    assert time_state["day_index"] == initial_day
    assert time_state["time_of_day"] == initial_time

    # Create new time system
    new_time = TimeSystem()

    # Restore
    new_time.restore_from_save(time_state)

    # Verify
    assert new_time.state.day_index == initial_day
    assert new_time.state.time_of_day == initial_time


def test_inventory_state_roundtrip(
    save_system: SaveSystem, inventory_system: InventorySystem
) -> None:
    """Test dat inventory state correct wordt gesaved en restored."""
    # Get initial state
    initial_items = inventory_system.get_all_items()

    # Save
    save_data = save_system.build_save()
    inventory_state = save_data["inventory_state"]

    # Verify save structure
    for item_id, quantity in initial_items.items():
        assert inventory_state.get(item_id) == quantity

    # Create new inventory system
    new_inventory = InventorySystem()

    # Restore
    new_inventory.restore_from_save(inventory_state)

    # Verify
    restored_items = new_inventory.get_all_items()
    assert restored_items == initial_items


def test_flags_state_roundtrip(save_system: SaveSystem, flags_system: GameStateFlags) -> None:
    """Test dat flags state correct wordt gesaved en restored."""
    # Save
    save_data = save_system.build_save()
    flags_state = save_data["flags_state"]

    assert "test_flag_1" in flags_state.get("story_flags", [])
    assert "test_flag_2" in flags_state.get("story_flags", [])

    # Create new flags system
    new_flags = GameStateFlags()

    # Restore
    new_flags.restore_from_save(flags_state)

    # Verify
    assert new_flags.has_flag("test_flag_1")
    assert new_flags.has_flag("test_flag_2")
    assert not new_flags.has_flag("nonexistent_flag")


def test_quest_state_roundtrip(
    save_system: SaveSystem, quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat quest state correct wordt gesaved en restored."""
    # Save
    save_data = save_system.build_save()
    quest_state = save_data["quest_state"]

    assert len(quest_state) > 0
    assert quest_state[0]["quest_id"] == "q_r1_shrine_intro"
    assert quest_state[0]["status"] == "ACTIVE"

    # Create new quest system
    new_quest = QuestSystem(None, None)
    new_quest.load_definitions(data_repository)

    # Restore
    new_quest.restore_from_save(quest_state)

    # Verify
    active_quests = new_quest.get_active_quests()
    assert len(active_quests) > 0
    assert active_quests[0].quest_id == "q_r1_shrine_intro"


def test_full_roundtrip_integration(
    save_system: SaveSystem,
    party_system: PartySystem,
    world_system: WorldSystem,
    time_system: TimeSystem,
    inventory_system: InventorySystem,
    flags_system: GameStateFlags,
    quest_system: QuestSystem,
    data_repository: DataRepository,
    test_save_dir: Path,
) -> None:
    """Test een volledige save  load  restore roundtrip."""
    # Modify state
    time_system.advance_time(300)  # 5 hours
    inventory_system.add_item("item_small_herb", 10)
    flags_system.set_flag("roundtrip_test_flag")

    # Save to file
    save_data = save_system.build_save(play_time=555.0)
    success = save_system.save_to_file(3, save_data)
    assert success

    # Create fresh systems
    new_party = PartySystem(data_repository, data_repository.get_npc_meta())
    project_root = Path.cwd()
    maps_dir = project_root / "maps" if (project_root / "src").exists() else Path("maps")
    new_world = WorldSystem(data_repository, maps_dir)
    new_time = TimeSystem()
    new_inventory = InventorySystem()
    new_flags = GameStateFlags()
    new_quest = QuestSystem(new_party, new_inventory)
    new_quest.load_definitions(data_repository)

    # Create new save system
    new_save_system = SaveSystem(
        new_party, new_world, new_time, new_inventory, new_flags, new_quest
    )
    new_save_system._save_dir = test_save_dir

    # Load from file
    loaded_data = new_save_system.load_from_file(3)
    assert loaded_data is not None
    assert loaded_data["meta"]["play_time"] == 555.0

    # Restore all systems
    success = new_save_system.load_save(loaded_data)
    assert success

    # Verify all state restored correctly
    assert new_flags.has_flag("roundtrip_test_flag")
    assert new_inventory.get_quantity("item_small_herb") >= 10
    assert len(new_party.get_active_party()) > 0


def test_corrupted_save_handling(save_system: SaveSystem, test_save_dir: Path) -> None:
    """Test dat corrupted save files nette errors geven."""
    # Create corrupted JSON file
    corrupted_file = test_save_dir / "save_slot_2.json"
    corrupted_file.write_text("{ invalid json }")

    # Try to load
    loaded_data = save_system.load_from_file(2)

    # Should return None instead of crashing
    assert loaded_data is None


def test_missing_system_graceful_handling(test_save_dir: Path) -> None:
    """Test dat SaveSystem graceful omgaat met missing systems."""
    # Create save system without any subsystems
    save_system = SaveSystem()
    save_system._save_dir = test_save_dir

    # Build save should still work (with empty states)
    save_data = save_system.build_save()

    assert save_data["meta"]["schema_version"] == 1
    assert save_data["time_state"] == {}
    assert save_data["world_state"] == {}
    assert save_data["party_state"] == {}

    # Save and load should work
    success = save_system.save_to_file(1, save_data)
    assert success

    loaded_data = save_system.load_from_file(1)
    assert loaded_data is not None


def test_multiple_save_slots(save_system: SaveSystem, test_save_dir: Path) -> None:
    """Test dat meerdere save slots onafhankelijk werken."""
    # Create different save states
    save_data_1 = save_system.build_save(play_time=100.0)
    save_data_2 = save_system.build_save(play_time=200.0)
    save_data_3 = save_system.build_save(play_time=300.0)

    # Save to different slots
    save_system.save_to_file(1, save_data_1)
    save_system.save_to_file(2, save_data_2)
    save_system.save_to_file(5, save_data_3)

    # Load them back
    loaded_1 = save_system.load_from_file(1)
    loaded_2 = save_system.load_from_file(2)
    loaded_5 = save_system.load_from_file(5)

    # Verify they're different
    assert loaded_1["meta"]["play_time"] == 100.0
    assert loaded_2["meta"]["play_time"] == 200.0
    assert loaded_5["meta"]["play_time"] == 300.0

    # Verify slot 3 and 4 don't exist
    assert save_system.slot_exists(3) is False
    assert save_system.slot_exists(4) is False
