"""Integratietests voor START_BATTLE events met enemy_groups en duplicate enemy IDs."""

from __future__ import annotations

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.combat import ActionType, BattleAction, BattleOutcome, CombatSystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.world import WorldSystem


def _make_world_with_combat() -> tuple[DataRepository, WorldSystem, CombatSystem, list[list[str]]]:
    repo = DataRepository()
    party = PartySystem(data_repository=repo, npc_meta=repo.get_npc_meta())
    combat = CombatSystem(party_system=party, data_repository=repo)
    world = WorldSystem(data_repository=repo)

    captured: list[list[str]] = []

    def start_battle_cb(enemy_ids: list[str]) -> None:
        captured.append(list(enemy_ids))
        combat.start_battle(enemy_ids)

    world.attach_systems(on_start_battle=start_battle_cb)
    return repo, world, combat, captured


def test_start_battle_event_with_enemy_group_and_duplicates() -> None:
    """Event -> START_BATTLE -> CombatSystem flow met enemy_group die duplicate IDs bevat."""
    repo, world, combat, captured = _make_world_with_combat()

    event = repo.get_event("ev_shrine_guardian_encounter")
    assert event is not None

    world._execute_event_actions(event.get("actions", []))

    # Callback ontving de enemy_ids uit de enemy_group (met duplicates)
    assert captured, "Battle callback should have been invoked"
    assert captured[-1] == ["en_shrine_construct", "en_corrupted_wisp", "en_corrupted_wisp"]

    state = combat.battle_state
    assert state is not None
    assert len(state.enemies) == 3

    # Markeer één wisp als dood, zodat targetting de levende wisp moet pakken
    for enemy in state.enemies:
        if enemy.actor_id == "en_corrupted_wisp":
            enemy.current_hp = 0
            break

    # Attack met target_id dat meerdere enemies delen mag geen "no target" opleveren
    action = BattleAction(
        actor_id=state.party[0].actor_id,
        action_type=ActionType.ATTACK,
        target_id="en_corrupted_wisp",
    )
    messages = combat.execute_action(action)
    assert "no target" not in " ".join(messages)

    # Sluit gevecht af door alle enemies op 0 HP te zetten en valideer WIN-pad
    for enemy in state.enemies:
        enemy.current_hp = 0

    outcome = combat.check_battle_end()
    assert outcome == BattleOutcome.WIN

    result = combat.get_battle_result(outcome)
    assert result.outcome == BattleOutcome.WIN
    assert result.total_xp >= 0
