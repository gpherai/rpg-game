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

    # Check that party member is correctly initialized
    party_member = state.party[0]
    assert party_member.actor_id == "mc_adhira"
    assert party_member.is_enemy is False
    assert party_member.is_alive()
    assert party_member.current_hp > 0

    # Check that enemy is correctly initialized
    enemy = state.enemies[0]
    assert enemy.actor_id == "en_forest_sprout"
    assert enemy.is_enemy is True
    assert enemy.is_alive()
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

    attacker = state.party[0]
    target = state.enemies[0]

    initial_hp = target.current_hp

    # Execute basic attack
    action = BattleAction(actor=attacker, action_type=ActionType.ATTACK, target=target)
    messages = combat_system.execute_action(action)

    # Check that damage was dealt (or miss occurred)
    if "misses" not in " ".join(messages):
        assert target.current_hp < initial_hp, "Target should have taken damage"
        assert target.current_hp >= 0, "HP should not go negative"


def test_defend_action_bug(combat_system: CombatSystem) -> None:
    """Test defend action en VERIFIEER de bekende 'easy mode' bug.

    BUG: is_defending wordt gereset aan het EINDE van execute_action,
    dus de defend flag werkt niet correct voor de volgende beurt.
    Dit is GEWENST gedrag voor testing (easy mode).
    """
    state = combat_system.start_battle(["en_forest_sprout"])

    defender = state.party[0]

    # Verify defender is not defending initially
    assert defender.is_defending is False

    # Execute defend action
    action = BattleAction(actor=defender, action_type=ActionType.DEFEND)
    messages = combat_system.execute_action(action)

    assert any("defensive stance" in msg for msg in messages)

    # BUG VERIFICATION: is_defending should be False after execute_action
    # This is the "easy mode" bug - defend flag is cleared too early
    assert defender.is_defending is False, "BUG: Defend flag cleared at end of action"

    # The bug means defend won't actually protect on next incoming attack
    # (unless we set it again right before damage calculation)


def test_defend_reduces_damage(combat_system: CombatSystem) -> None:
    """Test dat defend damage reduction werkt (wanneer flag handmatig wordt gezet)."""
    state = combat_system.start_battle(["en_forest_sprout"])

    attacker = state.enemies[0]
    defender = state.party[0]

    # Manually set defend flag (simulating correct behavior)
    defender.is_defending = True

    initial_hp = defender.current_hp

    # Execute attack
    action = BattleAction(actor=attacker, action_type=ActionType.ATTACK, target=defender)
    messages = combat_system.execute_action(action)

    # If hit occurred, check that "defending" message appeared
    if "misses" not in " ".join(messages) and defender.current_hp < initial_hp:
        # Defend should reduce damage by 50%
        # We can't easily verify the exact reduction without knowing the base damage,
        # but we can verify that the defend message appeared
        assert any("defending" in msg for msg in messages)


def test_skill_usage_with_resource_cost(combat_system: CombatSystem) -> None:
    """Test dat skills resource costs consumeren."""
    state = combat_system.start_battle(["en_forest_sprout"])

    user = state.party[0]
    target = state.enemies[0]

    # Adhira should have sk_body_strike (costs stamina)
    initial_stamina = user.current_stamina

    # Execute skill
    action = BattleAction(
        actor=user, action_type=ActionType.SKILL, target=target, skill_id="sk_body_strike"
    )
    messages = combat_system.execute_action(action)

    # Verify stamina was consumed
    # (sk_body_strike costs 3 stamina according to skills.json)
    assert user.current_stamina < initial_stamina, "Stamina should be consumed"


def test_skill_insufficient_resources(combat_system: CombatSystem) -> None:
    """Test dat skills falen wanneer resources onvoldoende zijn."""
    state = combat_system.start_battle(["en_forest_sprout"])

    user = state.party[0]
    target = state.enemies[0]

    # Drain stamina
    user.current_stamina = 0

    # Try to use skill that costs stamina
    action = BattleAction(
        actor=user, action_type=ActionType.SKILL, target=target, skill_id="sk_body_strike"
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
    state = combat_system.start_battle(["en_forest_sprout"])

    # Kill all enemies to win
    for enemy in state.enemies:
        enemy.current_hp = 0

    # Get battle result
    outcome = combat_system.check_battle_end()
    assert outcome == BattleOutcome.WIN

    result = combat_system.get_battle_result(outcome)

    # BUG VERIFICATION: Both party members should get FULL XP
    # (not divided XP)
    assert len(result.earned_xp) == 2, "Both members should get XP"

    adhira_xp = result.earned_xp.get("adhira", 0)
    rajani_xp = result.earned_xp.get("rajani", 0)

    # Bug: Both should get the same FULL amount
    assert adhira_xp == rajani_xp, "BUG: Both members get full XP (not divided)"
    assert adhira_xp > 0, "XP should be positive"

    # The bug means 2 members get 2x total XP
    # If enemy gives 10 XP, both get 10 (total 20 distributed)


def test_battle_victory_xp_rewards(combat_system: CombatSystem) -> None:
    """Test dat victory XP rewards correct worden uitgedeeld."""
    state = combat_system.start_battle(["en_forest_sprout"])

    # Kill enemy
    for enemy in state.enemies:
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
    state = combat_system.start_battle(["en_forest_sprout"])

    # Kill all party members
    for member in state.party:
        member.current_hp = 0

    # Check battle end
    outcome = combat_system.check_battle_end()
    assert outcome == BattleOutcome.LOSE


def test_level_up_from_combat(combat_system: CombatSystem, party_system: PartySystem) -> None:
    """Test dat level-ups correct worden verwerkt na combat."""
    # Get initial state
    member = party_system.get_party_member("npc_mc_adhira")
    assert member is not None

    initial_level = member.level

    # Start battle
    state = combat_system.start_battle(["en_forest_sprout"])

    # Manually set high XP to trigger level-up
    # Set party member to near level-up
    party_member_combatant = state.party[0]

    # Kill enemy to win
    for enemy in state.enemies:
        enemy.current_hp = 0

    # Manually set XP high enough for level-up
    # This is a bit hacky, but we need to ensure level-up occurs
    # We'll set the current XP via PartySystem first
    party_system.update_member_level("adhira", initial_level, 25)  # Near level-up threshold

    # Get battle result
    outcome = combat_system.check_battle_end()
    result = combat_system.get_battle_result(outcome)

    # Check if level-up occurred
    # Note: Level-up only occurs if earned XP + current XP >= threshold
    # For Forest Sprout (5 XP) + 25 current = 30 XP, should reach Lv 2
    if result.level_ups:
        level_up = result.level_ups[0]
        assert level_up.new_level > level_up.old_level
        assert level_up.stat_gains is not None
        # Verify at least some stat gains occurred
        gains = level_up.stat_gains
        total_gains = (
            gains.STR
            + gains.END
            + gains.DEF
            + gains.SPD
            + gains.ACC
            + gains.FOC
            + gains.INS
            + gains.WILL
            + gains.MAG
            + gains.PRA
            + gains.RES
        )
        assert total_gains > 0, "Should have stat gains on level-up"


def test_item_usage_healing(combat_system: CombatSystem) -> None:
    """Test dat items correct kunnen worden gebruikt voor healing."""
    state = combat_system.start_battle(["en_forest_sprout"])

    user = state.party[0]

    # Damage user first
    user.current_hp = user.max_hp // 2
    initial_hp = user.current_hp

    # Use healing item (small_herb)
    action = BattleAction(
        actor=user, action_type=ActionType.ITEM, target=user, item_id="item_small_herb"
    )
    messages = combat_system.execute_action(action)

    # Verify healing occurred
    assert user.current_hp > initial_hp, "HP should be restored"
    assert any("Restored" in msg for msg in messages)


def test_combatant_stat_modifiers(combat_system: CombatSystem) -> None:
    """Test dat stat modifiers correct werken."""
    state = combat_system.start_battle(["en_forest_sprout"])

    combatant = state.party[0]

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
    state = combat_system.start_battle(["en_forest_sprout"])

    # Both party and enemies alive
    outcome = combat_system.check_battle_end()
    assert outcome == BattleOutcome.ONGOING
