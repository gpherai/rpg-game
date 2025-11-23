"""Tests voor data validation (JSON schema's en DataRepository validatie)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tri_sarira_rpg.data_access.exceptions import DataFileNotFoundError, DataParseError
from tri_sarira_rpg.data_access.loader import DataLoader
from tri_sarira_rpg.data_access.repository import DataRepository


@pytest.fixture
def data_dir() -> Path:
    """Get the data directory path."""
    project_root = Path.cwd()
    if (project_root / "src").exists():
        return project_root / "data"
    return Path("data")


@pytest.fixture
def data_loader(data_dir: Path) -> DataLoader:
    """Create a DataLoader instance."""
    return DataLoader(data_dir=data_dir)


@pytest.fixture
def data_repository(data_dir: Path) -> DataRepository:
    """Create a DataRepository instance."""
    return DataRepository(data_dir=data_dir)


def test_actors_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat actors.json bestaat en valide JSON is."""
    actors_file = data_dir / "actors.json"
    assert actors_file.exists(), "actors.json should exist"

    with open(actors_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "actors.json should be a dict"
    assert "actors" in data, "actors.json should have 'actors' key"
    assert isinstance(data["actors"], list), "'actors' should be a list"


def test_enemies_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat enemies.json bestaat en valide JSON is."""
    enemies_file = data_dir / "enemies.json"
    assert enemies_file.exists(), "enemies.json should exist"

    with open(enemies_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "enemies.json should be a dict"
    assert "enemies" in data, "enemies.json should have 'enemies' key"
    assert isinstance(data["enemies"], list), "'enemies' should be a list"


def test_zones_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat zones.json bestaat en valide JSON is."""
    zones_file = data_dir / "zones.json"
    assert zones_file.exists(), "zones.json should exist"

    with open(zones_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "zones.json should be a dict"
    assert "zones" in data, "zones.json should have 'zones' key"
    assert isinstance(data["zones"], list), "'zones' should be a list"


def test_items_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat items.json bestaat en valide JSON is."""
    items_file = data_dir / "items.json"
    assert items_file.exists(), "items.json should exist"

    with open(items_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "items.json should be a dict"
    assert "items" in data, "items.json should have 'items' key"
    assert isinstance(data["items"], list), "'items' should be a list"


def test_skills_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat skills.json bestaat en valide JSON is."""
    skills_file = data_dir / "skills.json"
    assert skills_file.exists(), "skills.json should exist"

    with open(skills_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "skills.json should be a dict"
    assert "skills" in data, "skills.json should have 'skills' key"
    assert isinstance(data["skills"], list), "'skills' should be a list"


def test_quests_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat quests.json bestaat en valide JSON is."""
    quests_file = data_dir / "quests.json"
    assert quests_file.exists(), "quests.json should exist"

    with open(quests_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "quests.json should be a dict"
    assert "quests" in data, "quests.json should have 'quests' key"
    assert isinstance(data["quests"], list), "'quests' should be a list"


def test_dialogue_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat dialogue.json bestaat en valide JSON is."""
    dialogue_file = data_dir / "dialogue.json"
    assert dialogue_file.exists(), "dialogue.json should exist"

    with open(dialogue_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "dialogue.json should be a dict"
    assert "dialogues" in data, "dialogue.json should have 'dialogues' key"
    assert isinstance(data["dialogues"], list), "'dialogues' should be a list"


def test_shops_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat shops.json bestaat en valide JSON is (stub for v0)."""
    shops_file = data_dir / "shops.json"
    assert shops_file.exists(), "shops.json should exist"

    with open(shops_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "shops.json should be a dict"
    assert "shops" in data, "shops.json should have 'shops' key"


def test_loot_tables_json_exists_and_valid(data_dir: Path) -> None:
    """Test dat loot_tables.json bestaat en valide JSON is (stub for v0)."""
    loot_file = data_dir / "loot_tables.json"
    assert loot_file.exists(), "loot_tables.json should exist"

    with open(loot_file) as f:
        data = json.load(f)

    assert isinstance(data, dict), "loot_tables.json should be a dict"
    assert "loot_tables" in data, "loot_tables.json should have 'loot_tables' key"


def test_actors_have_required_keys(data_loader: DataLoader) -> None:
    """Test dat actors alle vereiste keys hebben."""
    data = data_loader.load_json("actors.json")
    required_keys = ["id", "name", "type", "level"]

    errors = data_loader.validate_data(data, "actors", required_keys)
    assert len(errors) == 0, f"Actors validation errors: {errors}"


def test_enemies_have_required_keys(data_loader: DataLoader) -> None:
    """Test dat enemies alle vereiste keys hebben."""
    data = data_loader.load_json("enemies.json")
    required_keys = ["id", "name", "type", "level"]

    errors = data_loader.validate_data(data, "enemies", required_keys)
    assert len(errors) == 0, f"Enemies validation errors: {errors}"


def test_zones_have_required_keys(data_loader: DataLoader) -> None:
    """Test dat zones alle vereiste keys hebben."""
    data = data_loader.load_json("zones.json")
    required_keys = ["id", "name", "type", "description"]

    errors = data_loader.validate_data(data, "zones", required_keys)
    assert len(errors) == 0, f"Zones validation errors: {errors}"


def test_items_have_required_keys(data_loader: DataLoader) -> None:
    """Test dat items alle vereiste keys hebben."""
    data = data_loader.load_json("items.json")
    required_keys = ["id", "name", "type", "category"]

    errors = data_loader.validate_data(data, "items", required_keys)
    assert len(errors) == 0, f"Items validation errors: {errors}"


def test_skills_have_required_keys(data_loader: DataLoader) -> None:
    """Test dat skills alle vereiste keys hebben."""
    data = data_loader.load_json("skills.json")
    required_keys = ["id", "name", "domain", "type", "target", "power"]

    errors = data_loader.validate_data(data, "skills", required_keys)
    assert len(errors) == 0, f"Skills validation errors: {errors}"


def test_repository_load_and_validate_all(data_repository: DataRepository) -> None:
    """Test dat DataRepository.load_and_validate_all succesvol is."""
    success = data_repository.load_and_validate_all()

    if not success:
        errors = data_repository.get_validation_errors()
        pytest.fail("Data validation failed:\n" + "\n".join(errors))

    assert success is True


def test_all_referenced_skills_exist(data_repository: DataRepository) -> None:
    """Skills die door actors/enemies gebruikt worden moeten bestaan."""
    success = data_repository.load_and_validate_all()
    errors = data_repository.get_validation_errors()
    missing_skill_errors = [e for e in errors if "skill_id" in e]

    assert success is True, f"Validation failed: {errors}"
    assert not missing_skill_errors, f"Missing skill references: {missing_skill_errors}"


def test_r1_main_story_quest_structure(data_loader: DataLoader) -> None:
    """Controleer basisstructuur van de R1 main story quest."""
    data = data_loader.load_json("quests.json")
    quests = {q["quest_id"]: q for q in data.get("quests", [])}
    quest = quests.get("q_r1_shrine_purification")
    assert quest is not None, "q_r1_shrine_purification should exist"

    stages = quest.get("stages", [])
    stage_ids = [s.get("stage_id") for s in stages]
    expected = ["talk_to_elder", "travel_to_shrine", "cleanse_shrine", "report_back"]
    assert stage_ids == expected, f"Unexpected stage order: {stage_ids}"

    # Ensure final stage is marked final
    assert stages[-1].get("is_final") is True, "Final stage should be marked is_final"


def test_repository_get_all_actors(data_repository: DataRepository) -> None:
    """Test dat get_all_actors actors teruggeeft met valide structuur."""
    actors = data_repository.get_all_actors()

    assert len(actors) > 0, "Should have at least one actor"

    for actor in actors:
        assert "id" in actor, "Actor should have 'id'"
        assert "name" in actor, "Actor should have 'name'"
        assert "type" in actor, "Actor should have 'type'"
        assert "level" in actor, "Actor should have 'level'"
        assert isinstance(actor["id"], str), "Actor id should be string"
        assert isinstance(actor["name"], str), "Actor name should be string"
        assert isinstance(actor["level"], int), "Actor level should be int"


def test_repository_get_all_enemies(data_repository: DataRepository) -> None:
    """Test dat get_all_enemies enemies teruggeeft met valide structuur."""
    enemies = data_repository.get_all_enemies()

    assert len(enemies) > 0, "Should have at least one enemy"

    for enemy in enemies:
        assert "id" in enemy, "Enemy should have 'id'"
        assert "name" in enemy, "Enemy should have 'name'"
        assert "type" in enemy, "Enemy should have 'type'"
        assert "level" in enemy, "Enemy should have 'level'"
        assert isinstance(enemy["id"], str), "Enemy id should be string"
        assert isinstance(enemy["name"], str), "Enemy name should be string"
        assert isinstance(enemy["level"], int), "Enemy level should be int"


def test_repository_get_all_zones(data_repository: DataRepository) -> None:
    """Test dat get_all_zones zones teruggeeft met valide structuur."""
    zones = data_repository.get_all_zones()

    assert len(zones) > 0, "Should have at least one zone"

    for zone in zones:
        assert "id" in zone, "Zone should have 'id'"
        assert "name" in zone, "Zone should have 'name'"
        assert "type" in zone, "Zone should have 'type'"
        assert isinstance(zone["id"], str), "Zone id should be string"
        assert isinstance(zone["name"], str), "Zone name should be string"


def test_repository_get_all_items(data_repository: DataRepository) -> None:
    """Test dat get_all_items items teruggeeft met valide structuur."""
    items = data_repository.get_all_items()

    assert len(items) > 0, "Should have at least one item"

    for item in items:
        assert "id" in item, "Item should have 'id'"
        assert "name" in item, "Item should have 'name'"
        assert "type" in item, "Item should have 'type'"
        assert isinstance(item["id"], str), "Item id should be string"
        assert isinstance(item["name"], str), "Item name should be string"


def test_repository_get_all_skills(data_repository: DataRepository) -> None:
    """Test dat get_all_skills skills teruggeeft met valide structuur."""
    skills = data_repository.get_all_skills()

    assert len(skills) > 0, "Should have at least one skill"

    for skill in skills:
        assert "id" in skill, "Skill should have 'id'"
        assert "name" in skill, "Skill should have 'name'"
        assert "domain" in skill, "Skill should have 'domain'"
        assert isinstance(skill["id"], str), "Skill id should be string"
        assert isinstance(skill["name"], str), "Skill name should be string"


def test_repository_get_specific_actor(data_repository: DataRepository) -> None:
    """Test dat get_actor een specifieke actor teruggeeft."""
    actor = data_repository.get_actor("mc_adhira")

    assert actor is not None, "Should find actor 'adhira'"
    assert actor["id"] == "mc_adhira"
    assert "name" in actor
    assert "base_stats" in actor


def test_repository_get_specific_enemy(data_repository: DataRepository) -> None:
    """Test dat get_enemy een specifieke enemy teruggeeft."""
    enemy = data_repository.get_enemy("en_forest_sprout")

    assert enemy is not None, "Should find enemy 'en_forest_sprout'"
    assert enemy["id"] == "en_forest_sprout"
    assert "name" in enemy
    assert "base_stats" in enemy


def test_repository_get_nonexistent_actor(data_repository: DataRepository) -> None:
    """Test dat get_actor None teruggeeft voor nonexistent actor."""
    actor = data_repository.get_actor("nonexistent_actor_id")
    assert actor is None


def test_repository_get_nonexistent_enemy(data_repository: DataRepository) -> None:
    """Test dat get_enemy None teruggeeft voor nonexistent enemy."""
    enemy = data_repository.get_enemy("nonexistent_enemy_id")
    assert enemy is None


def test_dataloader_raises_on_missing_file(tmp_path: Path) -> None:
    """Test dat DataLoader DataFileNotFoundError raised bij missing file."""
    loader = DataLoader(data_dir=tmp_path)

    with pytest.raises(DataFileNotFoundError):
        loader.load_json("nonexistent.json")


def test_dataloader_raises_on_invalid_json(tmp_path: Path) -> None:
    """Test dat DataLoader DataParseError raised bij invalid JSON."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{ invalid json }")

    loader = DataLoader(data_dir=tmp_path)

    with pytest.raises(DataParseError):
        loader.load_json("invalid.json")


def test_dataloader_caches_loaded_data(data_loader: DataLoader) -> None:
    """Test dat DataLoader data cached na eerste load."""
    # Clear cache first
    data_loader.clear_cache()

    # Load once
    data1 = data_loader.load_json("actors.json")

    # Load again (should use cache)
    data2 = data_loader.load_json("actors.json")

    # Should be the same object (from cache)
    assert data1 is data2


def test_validate_data_detects_missing_keys(data_loader: DataLoader) -> None:
    """Test dat validate_data missing keys detecteert."""
    # Create invalid data structure
    invalid_data = {
        "actors": [
            {"id": "test", "name": "Test Actor"},  # Missing 'type' and 'level'
        ]
    }

    errors = data_loader.validate_data(invalid_data, "actors", ["id", "name", "type", "level"])

    assert len(errors) > 0, "Should detect missing keys"
    assert any("type" in error for error in errors)
    assert any("level" in error for error in errors)


def test_validate_data_detects_wrong_types(data_loader: DataLoader) -> None:
    """Test dat validate_data wrong types detecteert."""
    # Create data with wrong types
    invalid_data = {
        "actors": [
            {
                "id": 123,  # Should be string
                "name": 456,  # Should be string
                "type": "test",
                "level": "5",  # Should be int
            }
        ]
    }

    errors = data_loader.validate_data(invalid_data, "actors", ["id", "name", "type", "level"])

    assert len(errors) > 0, "Should detect type errors"


def test_validate_data_detects_missing_top_level_key(data_loader: DataLoader) -> None:
    """Test dat validate_data missing top-level key detecteert."""
    # Create data without expected top-level key
    invalid_data = {"wrong_key": []}

    errors = data_loader.validate_data(invalid_data, "actors", ["id", "name"])

    assert len(errors) > 0, "Should detect missing top-level key"
    assert any("Missing top-level key" in error for error in errors)


def test_all_required_data_files_exist(data_dir: Path) -> None:
    """Test dat alle vereiste data files bestaan."""
    required_files = [
        "actors.json",
        "enemies.json",
        "zones.json",
        "items.json",
        "skills.json",
        "npc_meta.json",
        "quests.json",
        "dialogue.json",
        "shops.json",
        "loot_tables.json",
    ]

    for filename in required_files:
        file_path = data_dir / filename
        assert file_path.exists(), f"Required file {filename} should exist"
