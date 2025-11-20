"""Tests voor DialogueSystem (Step 6 Dialogue v0)."""

from __future__ import annotations

import pytest

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.dialogue import (
    DialogueContext,
    DialogueSession,
    DialogueSystem,
)
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.state import GameStateFlags


@pytest.fixture
def data_repository() -> DataRepository:
    """Create a DataRepository for testing."""
    return DataRepository()


@pytest.fixture
def dialogue_system(data_repository: DataRepository) -> DialogueSystem:
    """Create a DialogueSystem for testing."""
    return DialogueSystem(data_repository)


@pytest.fixture
def test_context() -> DialogueContext:
    """Create a test DialogueContext with mock systems."""
    flags = GameStateFlags()
    party = PartySystem()
    inventory = InventorySystem()

    return DialogueContext(
        flags_system=flags,
        party_system=party,
        inventory_system=inventory,
        economy_system=None,
        quest_system=None,
    )


def test_load_dialogue_from_json(data_repository: DataRepository) -> None:
    """Test dat een DialogueGraph geladen kan worden uit dialogue.json."""
    # Test dialogue ID from our test data
    dialogue_id = "dbg_adhira_rajani_intro"

    dialogue_data = data_repository.get_dialogue(dialogue_id)

    assert dialogue_data is not None, f"Dialogue {dialogue_id} not found"
    assert dialogue_data["dialogue_id"] == dialogue_id
    assert dialogue_data["scope"] == "SCENE"
    assert "nodes" in dialogue_data
    assert len(dialogue_data["nodes"]) > 0


def test_start_dialogue_returns_first_node(
    dialogue_system: DialogueSystem, test_context: DialogueContext
) -> None:
    """Test dat start_dialogue() de eerste node geeft met de juiste speaker + tekst."""
    dialogue_id = "dbg_adhira_rajani_intro"

    session = dialogue_system.start_dialogue(dialogue_id, test_context)

    assert session is not None, "Failed to start dialogue"
    assert session.dialogue_id == dialogue_id
    assert session.current_node_id == "n_intro"

    # Get current view
    view = dialogue_system.get_current_view(session)

    assert view is not None, "Failed to get dialogue view"
    assert view.speaker_id == "mc_adhira"
    assert len(view.lines) == 2  # Two lines in intro node
    assert "Adhira" in view.lines[0]
    assert len(view.choices) == 3  # Three choices in intro node


def test_choose_option_advances_to_next_node(
    dialogue_system: DialogueSystem, test_context: DialogueContext
) -> None:
    """Test dat choose_option() de juiste next_node_id kiest."""
    dialogue_id = "dbg_adhira_rajani_intro"

    session = dialogue_system.start_dialogue(dialogue_id, test_context)
    assert session is not None

    # Choose first option (meditate)
    result = dialogue_system.choose_option(session, "c_meditate")

    assert not result.conversation_ended, "Conversation ended too early"
    assert result.next_node_id == "n_meditate"
    assert session.current_node_id == "n_meditate"

    # Verify we're at the next node
    view = dialogue_system.get_current_view(session)
    assert view is not None
    assert view.speaker_id == "mc_adhira"
    assert "energie" in view.lines[0].lower()


def test_choose_option_with_end_conversation(
    dialogue_system: DialogueSystem, test_context: DialogueContext
) -> None:
    """Test dat choose_option() end_conversation = True respecteert."""
    dialogue_id = "dbg_adhira_rajani_intro"

    session = dialogue_system.start_dialogue(dialogue_id, test_context)
    assert session is not None

    # Choose option that leads to farewell node
    result = dialogue_system.choose_option(session, "c_continue")

    # Should advance to farewell node
    assert not result.conversation_ended
    assert result.next_node_id == "n_farewell"

    # Farewell node has end_conversation = true
    view = dialogue_system.get_current_view(session)
    assert view is not None

    # Try to auto-advance (should end conversation)
    result2 = dialogue_system.auto_advance(session)
    assert result2.conversation_ended, "Conversation should have ended"


def test_effect_set_flag(
    dialogue_system: DialogueSystem, test_context: DialogueContext
) -> None:
    """Test dat SET_FLAG effect correct wordt toegepast."""
    dialogue_id = "dbg_adhira_rajani_intro"

    session = dialogue_system.start_dialogue(dialogue_id, test_context)
    assert session is not None

    # Before choosing, flag should not be set
    assert not test_context.flags_system.has_flag("dbg_meditated")

    # Choose option that sets flag
    result = dialogue_system.choose_option(session, "c_meditate")

    # After choosing, flag should be set
    assert test_context.flags_system.has_flag("dbg_meditated")
    assert "Set flag: dbg_meditated" in result.effects_applied


def test_effect_give_item(
    dialogue_system: DialogueSystem, test_context: DialogueContext
) -> None:
    """Test dat GIVE_ITEM effect correct wordt toegepast."""
    dialogue_id = "dbg_adhira_rajani_intro"

    session = dialogue_system.start_dialogue(dialogue_id, test_context)
    assert session is not None

    # Navigate to meditation node first
    dialogue_system.choose_option(session, "c_meditate")

    # Before choosing deep meditation, should have no meditation token
    assert test_context.inventory_system.get_quantity("item_meditation_token") == 0

    # Choose deep meditation (requires flag, gives item)
    result = dialogue_system.choose_option(session, "c_deep_meditation")

    # After choosing, should have received item
    assert test_context.inventory_system.get_quantity("item_meditation_token") == 1
    assert any("item_meditation_token" in effect for effect in result.effects_applied)


def test_condition_flag_set(
    dialogue_system: DialogueSystem, test_context: DialogueContext
) -> None:
    """Test dat FLAG_SET condition correct werkt."""
    dialogue_id = "dbg_adhira_rajani_intro"

    session = dialogue_system.start_dialogue(dialogue_id, test_context)
    assert session is not None

    # Navigate to meditation node
    dialogue_system.choose_option(session, "c_meditate")

    # Get view - deep meditation choice should NOT be visible (flag not set yet)
    view = dialogue_system.get_current_view(session)
    assert view is not None
    visible_choice_ids = [c.choice_id for c in view.choices]

    # Deep meditation requires dbg_meditated flag, but we're IN the meditate node
    # which sets the flag, so actually the flag IS set now
    # Let's verify this
    assert test_context.flags_system.has_flag("dbg_meditated")
    assert "c_deep_meditation" in visible_choice_ids


def test_condition_companion_in_party(
    dialogue_system: DialogueSystem, test_context: DialogueContext
) -> None:
    """Test dat COMPANION_IN_PARTY condition correct werkt."""
    dialogue_id = "dbg_adhira_rajani_intro"

    session = dialogue_system.start_dialogue(dialogue_id, test_context)
    assert session is not None

    # Get initial view
    view = dialogue_system.get_current_view(session)
    assert view is not None

    visible_choice_ids = [c.choice_id for c in view.choices]

    # Rajani choice should NOT be visible (not in party)
    assert "c_call_rajani" not in visible_choice_ids

    # Add Rajani to party
    test_context.party_system.add_to_reserve_pool(
        "npc_comp_rajani", "comp_rajani", tier="A"
    )
    test_context.party_system.add_to_active_party("npc_comp_rajani")

    # Start dialogue again
    session2 = dialogue_system.start_dialogue(dialogue_id, test_context)
    view2 = dialogue_system.get_current_view(session2)
    assert view2 is not None

    visible_choice_ids2 = [c.choice_id for c in view2.choices]

    # NOW Rajani choice SHOULD be visible
    assert "c_call_rajani" in visible_choice_ids2


def test_auto_advance(
    dialogue_system: DialogueSystem, test_context: DialogueContext
) -> None:
    """Test dat auto_advance correct werkt."""
    dialogue_id = "dbg_adhira_rajani_intro"

    session = dialogue_system.start_dialogue(dialogue_id, test_context)
    assert session is not None

    # Navigate to a path that uses auto_advance
    # Choose Rajani (requires adding her first)
    test_context.party_system.add_to_reserve_pool(
        "npc_comp_rajani", "comp_rajani", tier="A"
    )
    test_context.party_system.add_to_active_party("npc_comp_rajani")

    # Navigate: intro -> rajani appears -> gift rajani -> rajani thanks (auto-advances)
    dialogue_system.choose_option(session, "c_call_rajani")
    dialogue_system.choose_option(session, "c_gift_rajani")

    # Now at n_rajani_thanks which has auto_advance_to n_farewell
    view = dialogue_system.get_current_view(session)
    assert view is not None
    assert view.can_auto_advance

    # Auto advance
    result = dialogue_system.auto_advance(session)
    assert not result.conversation_ended
    assert result.next_node_id == "n_farewell"
    assert session.current_node_id == "n_farewell"
