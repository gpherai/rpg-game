"""Tests voor QuestSystem (Step 7 Quest System v0)."""

from __future__ import annotations

import pytest

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.dialogue import (
    DialogueContext,
    DialogueSystem,
)
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.quest import QuestStatus, QuestSystem
from tri_sarira_rpg.systems.state import GameStateFlags


@pytest.fixture
def data_repository() -> DataRepository:
    """Create a DataRepository for testing."""
    return DataRepository()


@pytest.fixture
def party_system(data_repository: DataRepository) -> PartySystem:
    """Create a PartySystem for testing."""
    npc_meta = data_repository.get_npc_meta()
    return PartySystem(data_repository, npc_meta)


@pytest.fixture
def inventory_system() -> InventorySystem:
    """Create an InventorySystem for testing."""
    return InventorySystem()


@pytest.fixture
def quest_system(
    party_system: PartySystem, inventory_system: InventorySystem
) -> QuestSystem:
    """Create a QuestSystem for testing."""
    return QuestSystem(party_system, inventory_system)


def test_load_quest_definitions(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat quest definities geladen kunnen worden uit JSON."""
    quest_system.load_definitions(data_repository)

    # Check that quests were loaded
    definition = quest_system.get_definition("q_r1_shrine_intro")
    assert definition is not None
    assert definition.quest_id == "q_r1_shrine_intro"
    assert definition.title == "De Weg naar het Heiligdom"
    assert len(definition.stages) == 2
    assert definition.rewards is not None
    assert definition.rewards.xp == 20
    assert definition.rewards.money == 10


def test_start_quest(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat een quest gestart kan worden."""
    quest_system.load_definitions(data_repository)

    # Start quest
    state = quest_system.start_quest("q_r1_shrine_intro")

    assert state is not None
    assert state.quest_id == "q_r1_shrine_intro"
    assert state.status == QuestStatus.ACTIVE
    assert state.current_stage_id == "talk_to_elder"

    # Verify quest is in active state
    quest_state = quest_system.get_state("q_r1_shrine_intro")
    assert quest_state is not None
    assert quest_state.status == QuestStatus.ACTIVE


def test_advance_quest(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat een quest naar volgende stage kan worden geadvanced."""
    quest_system.load_definitions(data_repository)

    # Start and advance quest
    quest_system.start_quest("q_r1_shrine_intro")
    state = quest_system.advance_quest("q_r1_shrine_intro")

    assert state is not None
    assert state.current_stage_id == "reach_shrine_clearing"
    assert state.status == QuestStatus.ACTIVE


def test_advance_quest_explicit_stage(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat een quest naar specifieke stage kan worden geadvanced."""
    quest_system.load_definitions(data_repository)

    # Start and advance to specific stage
    quest_system.start_quest("q_r1_shrine_intro")
    state = quest_system.advance_quest("q_r1_shrine_intro", "reach_shrine_clearing")

    assert state is not None
    assert state.current_stage_id == "reach_shrine_clearing"


def test_complete_quest(
    quest_system: QuestSystem,
    data_repository: DataRepository,
    party_system: PartySystem,
    inventory_system: InventorySystem,
) -> None:
    """Test dat een quest completed kan worden met rewards."""
    quest_system.load_definitions(data_repository)

    # Add main character to party for XP rewards
    party_system.add_to_reserve_pool("npc_mc_adhira", "mc_adhira", tier="MC")
    party_system.add_to_active_party("npc_mc_adhira")

    # Get initial XP
    mc = party_system.get_active_party()[0]
    initial_xp = mc.xp

    # Start and complete quest
    quest_system.start_quest("q_r1_shrine_intro")
    state = quest_system.complete_quest("q_r1_shrine_intro")

    assert state is not None
    assert state.status == QuestStatus.COMPLETED

    # Verify rewards applied
    # XP should increase
    assert mc.xp == initial_xp + 20

    # Items should be added (medium herbs)
    assert inventory_system.get_quantity("item_medium_herb") == 2


def test_get_active_quests(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat actieve quests opgehaald kunnen worden."""
    quest_system.load_definitions(data_repository)

    # Start multiple quests
    quest_system.start_quest("q_r1_shrine_intro")
    quest_system.start_quest("q_test_simple")

    active = quest_system.get_active_quests()
    assert len(active) == 2

    # Complete one quest
    quest_system.complete_quest("q_test_simple")

    active = quest_system.get_active_quests()
    assert len(active) == 1
    assert active[0].quest_id == "q_r1_shrine_intro"


def test_build_quest_log_view(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat quest log view gebouwd kan worden."""
    quest_system.load_definitions(data_repository)

    # Start quest
    quest_system.start_quest("q_r1_shrine_intro")

    # Build view
    entries = quest_system.build_quest_log_view()

    assert len(entries) == 1
    entry = entries[0]
    assert entry.quest_id == "q_r1_shrine_intro"
    assert entry.title == "De Weg naar het Heiligdom"
    assert entry.status == QuestStatus.ACTIVE
    assert entry.current_stage_description == "Praat met de dorpsoudste over het heiligdom."


def test_save_and_restore_quest_state(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat quest state correct gesaved en restored wordt."""
    quest_system.load_definitions(data_repository)

    # Start and advance some quests
    quest_system.start_quest("q_r1_shrine_intro")
    quest_system.advance_quest("q_r1_shrine_intro")
    quest_system.start_quest("q_test_simple")

    # Save state
    save_data = quest_system.get_save_state()

    assert len(save_data) == 2
    assert save_data[0]["quest_id"] == "q_r1_shrine_intro"
    assert save_data[0]["status"] == "ACTIVE"
    assert save_data[0]["current_stage_id"] == "reach_shrine_clearing"

    # Create new quest system and restore
    new_quest_system = QuestSystem(None, None)
    new_quest_system.load_definitions(data_repository)
    new_quest_system.restore_from_save(save_data)

    # Verify state restored correctly
    restored_state = new_quest_system.get_state("q_r1_shrine_intro")
    assert restored_state is not None
    assert restored_state.status == QuestStatus.ACTIVE
    assert restored_state.current_stage_id == "reach_shrine_clearing"

    active_quests = new_quest_system.get_active_quests()
    assert len(active_quests) == 2


def test_dialogue_quest_integration(
    quest_system: QuestSystem,
    data_repository: DataRepository,
    party_system: PartySystem,
    inventory_system: InventorySystem,
) -> None:
    """Test dat quest effects werken via DialogueSystem."""
    quest_system.load_definitions(data_repository)

    # Create dialogue system
    dialogue_system = DialogueSystem(data_repository)

    # Create dialogue context with quest system
    flags_system = GameStateFlags()
    context = DialogueContext(
        flags_system=flags_system,
        party_system=party_system,
        inventory_system=inventory_system,
        economy_system=None,
        quest_system=quest_system,
    )

    # Start dialogue that has QUEST_START effect
    dialogue_id = "dlg_r1_elder_shrine_intro"
    session = dialogue_system.start_dialogue(dialogue_id, context)

    assert session is not None

    # Choose option that starts quest
    result = dialogue_system.choose_option(session, "c_help")

    # Verify quest was started
    assert "Started quest: q_r1_shrine_intro" in result.effects_applied

    quest_state = quest_system.get_state("q_r1_shrine_intro")
    assert quest_state is not None
    assert quest_state.status == QuestStatus.ACTIVE


def test_quest_not_found_error(quest_system: QuestSystem) -> None:
    """Test dat een error wordt raised voor ongeldige quest_id."""
    # Don't load definitions
    with pytest.raises(ValueError, match="Quest definition not found"):
        quest_system.start_quest("invalid_quest_id")


def test_quest_already_active_error(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat een error wordt raised bij dubbel starten van quest."""
    quest_system.load_definitions(data_repository)

    quest_system.start_quest("q_test_simple")

    with pytest.raises(ValueError, match="Quest .* is already"):
        quest_system.start_quest("q_test_simple")


def test_advance_not_active_quest_error(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat een error wordt raised bij advance van niet-actieve quest."""
    quest_system.load_definitions(data_repository)

    with pytest.raises(ValueError, match="Quest .* is not active"):
        quest_system.advance_quest("q_test_simple")


def test_complete_not_active_quest_error(
    quest_system: QuestSystem, data_repository: DataRepository
) -> None:
    """Test dat een error wordt raised bij complete van niet-actieve quest."""
    quest_system.load_definitions(data_repository)

    with pytest.raises(ValueError, match="Quest .* is not active"):
        quest_system.complete_quest("q_test_simple")
