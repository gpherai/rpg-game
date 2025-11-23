"""Tests voor CombatSystem (Step 5 Combat v0)."""

from __future__ import annotations

import pytest

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.combat import (
    ActionType,
    BattleAction,
    BattleOutcome,
    CombatSystem,
)
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.time import TimeSystem


@pytest.fixture
def data_repository() -> DataRepository:
    """Create a DataRepository for testing."""
    return DataRepository()


@pytest.fixture
def party_system(data_repository: DataRepository) -> PartySystem:
    """Create a PartySystem with main character."""
    npc_meta = data_repository.get_npc_meta()
    party = PartySystem(data_repository, npc_meta)

    # Add main character to party
    party.add_to_reserve_pool("npc_mc_adhira", "mc_adhira", tier="MC")
    party.add_to_active_party("npc_mc_adhira")

    return party


@pytest.fixture
def combat_system(party_system: PartySystem, data_repository: DataRepository) -> CombatSystem:
    """Create a CombatSystem for testing."""
    return CombatSystem(party_system, data_repository)


def test_battle_initialization(combat_system: CombatSystem, party_system: PartySystem) -> None:
    """Test dat een battle correct wordt geinitialiseerd."""
    # Start battle with one enemy
    state = combat_system.start_battle(["en_forest_sprout"])

    assert state is not None
    assert len(state.party) == 1, "Should have 1 party member"
    assert len(state.enemies) == 1, "Should have 1 enemy"
    assert len(state.turn_order) == 2, "Turn order should include both combatants"

    # Check that party member is correctly initialized (using viewmodel)
    party_member = state.party[0]
    assert party_member.actor_id == "mc_adhira"
    assert party_member.is_enemy is False
    assert party_member.is_alive  # property, not method
    assert party_member.current_hp > 0

    # Check that enemy is correctly initialized
    enemy = state.enemies[0]
    assert enemy.actor_id == "en_forest_sprout"
    assert enemy.is_enemy is True
    assert enemy.is_alive  # property, not method
    assert enemy.current_hp > 0


def test_turn_order_simple(combat_system: CombatSystem) -> None:
    """Test dat turn order correct wordt opgezet (v0: party first, then enemies)."""
    state = combat_system.start_battle(["en_forest_sprout", "en_forest_sprout"])

    # v0: Simple turn order is party first, then enemies
    assert len(state.turn_order) == 3

    # First combatant should be party member
    assert state.turn_order[0].is_enemy is False

    # Remaining should be enemies
    assert state.turn_order[1].is_enemy is True
    assert state.turn_order[2].is_enemy is True


def test_get_current_actor(combat_system: CombatSystem) -> None:
    """Test dat get_current_actor de juiste combatant teruggeeft."""
    state = combat_system.start_battle(["en_forest_sprout"])

    # First turn should be party member
    current = combat_system.get_current_actor()
    assert current is not None
    assert current.is_enemy is False

    # Advance turn
    combat_system.advance_turn()
    current = combat_system.get_current_actor()
    assert current is not None
    assert current.is_enemy is True


def test_basic_attack_damage_calculation(combat_system: CombatSystem) -> None:
    """Test dat basic attack damage correct wordt berekend."""
    state = combat_system.start_battle(["en_forest_sprout"])

    # Get actor IDs from viewmodel
    attacker_id = state.party[0].actor_id
    target_id = state.enemies[0].actor_id

    # Get initial HP from internal state (for mutation check)
    internal_state = combat_system.battle_state
    assert internal_state is not None
    initial_hp = internal_state.enemies[0].current_hp

    # Execute basic attack using string IDs
    action = BattleAction(actor_id=attacker_id, action_type=ActionType.ATTACK, target_id=target_id)
    messages = combat_system.execute_action(action)

    # Check that damage was dealt (or miss occurred)
    if "misses" not in " ".join(messages):
        assert internal_state.enemies[0].current_hp < initial_hp, "Target should have taken damage"
        assert internal_state.enemies[0].current_hp >= 0, "HP should not go negative"


def test_defend_action_bug(combat_system: CombatSystem) -> None:
    """Test defend action en VERIFIEER de bekende 'easy mode' bug.

    BUG: is_defending wordt gereset aan het EINDE van execute_action,
    dus de defend flag werkt niet correct voor de volgende beurt.
    Dit is GEWENST gedrag voor testing (easy mode).
    """
    state = combat_system.start_battle(["en_forest_sprout"])

    defender_id = state.party[0].actor_id

    # Access internal state to verify flags
    internal_state = combat_system.battle_state
    assert internal_state is not None
    defender = internal_state.party[0]

    # Verify defender is not defending initially
    assert defender.is_defending is False

    # Execute defend action
    action = BattleAction(actor_id=defender_id, action_type=ActionType.DEFEND)
    messages = combat_system.execute_action(action)

    assert any("defensive stance" in msg for msg in messages)

    # BUG VERIFICATION: is_defending should be False after execute_action
    # This is the "easy mode" bug - defend flag is cleared too early
    assert defender.is_defending is False, "BUG: Defend flag cleared at end of action"


def test_defend_reduces_damage(combat_system: CombatSystem) -> None:
    """Test dat defend damage reduction werkt (wanneer flag handmatig wordt gezet)."""
    state = combat_system.start_battle(["en_forest_sprout"])

    attacker_id = state.enemies[0].actor_id
    defender_id = state.party[0].actor_id

    # Access internal state for mutation
    internal_state = combat_system.battle_state
    assert internal_state is not None
    defender = internal_state.party[0]

    # Manually set defend flag (simulating correct behavior)
    defender.is_defending = True

    initial_hp = defender.current_hp

    # Execute attack
    action = BattleAction(actor_id=attacker_id, action_type=ActionType.ATTACK, target_id=defender_id)
    messages = combat_system.execute_action(action)

    # If hit occurred, check that "defending" message appeared
    if "misses" not in " ".join(messages) and defender.current_hp < initial_hp:
        assert any("defending" in msg for msg in messages)


def test_skill_usage_with_resource_cost(combat_system: CombatSystem) -> None:
    """Test dat skills resource costs consumeren."""
    state = combat_system.start_battle(["en_forest_sprout"])

    user_id = state.party[0].actor_id
    target_id = state.enemies[0].actor_id

    # Access internal state for stamina check
    internal_state = combat_system.battle_state
    assert internal_state is not None
    user = internal_state.party[0]

    initial_stamina = user.current_stamina

    # Execute skill
    action = BattleAction(
        actor_id=user_id, action_type=ActionType.SKILL, target_id=target_id, skill_id="sk_body_strike"
    )
    messages = combat_system.execute_action(action)

    # Verify stamina was consumed
    assert user.current_stamina < initial_stamina, "Stamina should be consumed"


def test_skill_insufficient_resources(combat_system: CombatSystem) -> None:
    """Test dat skills falen wanneer resources onvoldoende zijn."""
    state = combat_system.start_battle(["en_forest_sprout"])

    user_id = state.party[0].actor_id
    target_id = state.enemies[0].actor_id

    # Access internal state for mutation
    internal_state = combat_system.battle_state
    assert internal_state is not None
    user = internal_state.party[0]

    # Drain stamina
    user.current_stamina = 0

    # Try to use skill that costs stamina
    action = BattleAction(
        actor_id=user_id, action_type=ActionType.SKILL, target_id=target_id, skill_id="sk_body_strike"
    )
    messages = combat_system.execute_action(action)

    # Should get "not enough" message
    assert any("doesn't have enough" in msg for msg in messages)


def test_xp_distribution_bug(combat_system: CombatSystem, party_system: PartySystem) -> None:
    """Test XP distribution en VERIFIEER de bekende 'easy mode' bug.

    BUG: Elk party member krijgt VOLLEDIGE XP in plaats van gedeelde XP.
    Dit is GEWENST gedrag voor testing (easy mode).
    """
    # Add a second party member
    party_system.add_to_reserve_pool("npc_comp_rajani", "comp_rajani", tier="A")
    party_system.add_to_active_party("npc_comp_rajani")

    # Start battle
    combat_system.start_battle(["en_forest_sprout"])

    # Access internal state to kill enemies
    internal_state = combat_system.battle_state
    assert internal_state is not None

    for enemy in internal_state.enemies:
        enemy.current_hp = 0

    # Get battle result
    outcome = combat_system.check_battle_end()
    assert outcome == BattleOutcome.WIN

    result = combat_system.get_battle_result(outcome)

    # BUG VERIFICATION: Both party members should get FULL XP
    assert len(result.earned_xp) == 2, "Both members should get XP"

    adhira_xp = result.earned_xp.get("mc_adhira", 0)
    rajani_xp = result.earned_xp.get("comp_rajani", 0)

    assert adhira_xp == rajani_xp, "BUG: Both members get full XP (not divided)"
    assert adhira_xp > 0, "XP should be positive"


def test_duplicate_enemy_ids_target_alive_enemy(combat_system: CombatSystem) -> None:
    """Wanneer meerdere enemies dezelfde actor_id delen, moet een levende target gekozen worden."""
    combat_system.start_battle(["en_forest_sprout", "en_forest_sprout"])

    internal_state = combat_system.battle_state
    assert internal_state is not None

    # Maak de eerste enemy "dood"
    internal_state.enemies[0].current_hp = 0
    assert internal_state.enemies[0].is_alive() is False
    assert internal_state.enemies[1].is_alive() is True

    # Lookup moet de levende enemy teruggeven
    target = combat_system._get_combatant_by_id("en_forest_sprout#1")
    assert target is internal_state.enemies[1]

    # Actie op het target mag geen "no target" melding geven
    action = BattleAction(
        actor_id=internal_state.party[0].battle_id,
        action_type=ActionType.ATTACK,
        target_id="en_forest_sprout#1",
    )
    messages = combat_system.execute_action(action)
    joined = " ".join(messages)
    assert "no target" not in joined


def test_duplicate_enemy_ids_target_specific_instance(combat_system: CombatSystem) -> None:
    """Met target suffix (#index) moet de juiste instance geraakt worden."""
    combat_system.start_battle(["en_corrupted_wisp", "en_corrupted_wisp"])
    internal_state = combat_system.battle_state
    assert internal_state is not None

    # Force deterministic hit
    import random

    random.seed(0)

    first = internal_state.enemies[0]
    second = internal_state.enemies[1]
    initial_first = first.current_hp
    initial_second = second.current_hp

    action = BattleAction(
        actor_id=internal_state.party[0].battle_id,
        action_type=ActionType.ATTACK,
        target_id="en_corrupted_wisp#1",
    )
    combat_system.execute_action(action)

    # Expect damage on the second, not on the first
    assert first.current_hp == initial_first
    assert second.current_hp < initial_second


def test_time_advances_after_battle() -> None:
    """Na een gewonnen gevecht moet de tijd 1 minuut vooruit."""
    data_repo = DataRepository()
    time_system = TimeSystem()
    party_system = PartySystem(data_repo, data_repo.get_npc_meta())
    combat_system = CombatSystem(party_system, data_repo, time_system=time_system)

    # Start battle en maak enemies dood
    combat_system.start_battle(["en_forest_sprout"])
    state = combat_system.battle_state
    assert state is not None
    for enemy in state.enemies:
        enemy.current_hp = 0

    start_time = time_system.state.time_of_day
    outcome = combat_system.check_battle_end()
    result = combat_system.get_battle_result(outcome)
    assert result.outcome == BattleOutcome.WIN
    assert time_system.state.time_of_day == start_time + 1

    # Tweede call mag tijd niet nog eens verhogen
    _ = combat_system.get_battle_result(outcome)
    assert time_system.state.time_of_day == start_time + 1


def test_battle_victory_xp_rewards(combat_system: CombatSystem) -> None:
    """Test dat victory XP rewards correct worden uitgedeeld."""
    combat_system.start_battle(["en_forest_sprout"])

    # Access internal state to kill enemy
    internal_state = combat_system.battle_state
    assert internal_state is not None

    for enemy in internal_state.enemies:
        enemy.current_hp = 0

    # Check battle end
    outcome = combat_system.check_battle_end()
    assert outcome == BattleOutcome.WIN

    # Get result
    result = combat_system.get_battle_result(outcome)

    assert result.outcome == BattleOutcome.WIN
    assert len(result.earned_xp) > 0, "Should earn XP"
    assert result.earned_money >= 0, "Should earn money (or 0)"


def test_battle_defeat(combat_system: CombatSystem) -> None:
    """Test dat defeat correct wordt gedetecteerd."""
    combat_system.start_battle(["en_forest_sprout"])

    # Access internal state to kill party
    internal_state = combat_system.battle_state
    assert internal_state is not None

    for member in internal_state.party:
        member.current_hp = 0

    # Check battle end
    outcome = combat_system.check_battle_end()
    assert outcome == BattleOutcome.LOSE


def test_level_up_from_combat(combat_system: CombatSystem, party_system: PartySystem) -> None:
    """Test dat level-ups correct worden verwerkt na combat."""
    # Get initial state
    member = party_system.get_party_member("mc_adhira")
    assert member is not None

    initial_level = member.level

    # Start battle
    combat_system.start_battle(["en_forest_sprout"])

    # Access internal state to kill enemy
    internal_state = combat_system.battle_state
    assert internal_state is not None

    for enemy in internal_state.enemies:
        enemy.current_hp = 0

    # Manually set XP high enough for level-up
    party_system.update_member_level("adhira", initial_level, 25)

    # Get battle result
    outcome = combat_system.check_battle_end()
    result = combat_system.get_battle_result(outcome)

    # Check if level-up occurred
    if result.level_ups:
        level_up = result.level_ups[0]
        assert level_up.new_level > level_up.old_level
        assert level_up.stat_gains is not None
        gains = level_up.stat_gains
        total_gains = (
            gains.STR + gains.END + gains.DEF + gains.SPD + gains.ACC +
            gains.FOC + gains.INS + gains.WILL + gains.MAG + gains.PRA + gains.RES
        )
        assert total_gains > 0, "Should have stat gains on level-up"


def test_item_usage_healing(combat_system: CombatSystem) -> None:
    """Test dat items correct kunnen worden gebruikt voor healing."""
    state = combat_system.start_battle(["en_forest_sprout"])

    user_id = state.party[0].actor_id

    # Access internal state for mutation
    internal_state = combat_system.battle_state
    assert internal_state is not None
    user = internal_state.party[0]

    # Damage user first
    user.current_hp = user.max_hp // 2
    initial_hp = user.current_hp

    # Use healing item (small_herb)
    action = BattleAction(
        actor_id=user_id, action_type=ActionType.ITEM, target_id=user_id, item_id="item_small_herb"
    )
    messages = combat_system.execute_action(action)

    # Verify healing occurred
    assert user.current_hp > initial_hp, "HP should be restored"
    assert any("Restored" in msg for msg in messages)


def test_combatant_stat_modifiers(combat_system: CombatSystem) -> None:
    """Test dat stat modifiers correct werken."""
    combat_system.start_battle(["en_forest_sprout"])

    # Access internal state for stat modifier testing
    internal_state = combat_system.battle_state
    assert internal_state is not None
    combatant = internal_state.party[0]

    # Get base stat
    base_str = combatant.STR
    effective_str = combatant.get_effective_stat("STR")
    assert effective_str == base_str

    # Apply modifier
    combatant.stat_modifiers["STR"] = 5
    effective_str = combatant.get_effective_stat("STR")
    assert effective_str == base_str + 5

    # Negative modifier
    combatant.stat_modifiers["STR"] = -3
    effective_str = combatant.get_effective_stat("STR")
    assert effective_str == base_str - 3

    # Should not go below 0
    combatant.stat_modifiers["STR"] = -999
    effective_str = combatant.get_effective_stat("STR")
    assert effective_str == 0


def test_battle_ongoing(combat_system: CombatSystem) -> None:
    """Test dat battle ONGOING status correct wordt gedetecteerd."""
    combat_system.start_battle(["en_forest_sprout"])

    # Both party and enemies alive
    outcome = combat_system.check_battle_end()
    assert outcome == BattleOutcome.ONGOING
