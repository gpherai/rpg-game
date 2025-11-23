"""Integratietest: event START_BATTLE → CombatSystem met duplicate enemies."""

from __future__ import annotations

import random

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.combat import ActionType, BattleAction, CombatSystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.world import WorldSystem


class DummyQuestNoop:
    """No-op quest stub to avoid quest errors during event actions."""

    def start_quest(self, quest_id: str) -> None: ...

    def advance_quest(self, quest_id: str, stage_id: str | None = None) -> None: ...

    def complete_quest(self, quest_id: str) -> None: ...


def test_event_start_battle_flow_with_duplicates() -> None:
    """Event actions should start battle with enemy_group (incl. duplicate IDs) and target correctly."""

    repo = DataRepository()
    party = PartySystem(data_repository=repo, npc_meta=repo.get_npc_meta())
    combat = CombatSystem(party_system=party, data_repository=repo)
    world = WorldSystem(data_repository=repo)

    started: list[list[str]] = []

    def on_start_battle(enemy_ids: list[str]) -> None:
        started.append(list(enemy_ids))
        combat.start_battle(enemy_ids)

    world.attach_systems(on_start_battle=on_start_battle, quest_system=DummyQuestNoop())

    event = repo.get_event("ev_shrine_guardian_encounter")
    assert event is not None

    world._execute_event_actions(event.get("actions", []))

    assert started, "Battle callback should have been invoked"
    enemy_ids = started[-1]
    assert enemy_ids == ["en_shrine_construct", "en_corrupted_wisp", "en_corrupted_wisp"]

    state = combat.battle_state
    assert state is not None
    assert len(state.enemies) == 3

    # Battle IDs must be unique even if actor_ids repeat
    battle_ids = {e.battle_id for e in state.enemies}
    assert len(battle_ids) == 3

    # Attack the second enemy explicitly and ensure only that enemy takes damage
    random.seed(0)  # deterministic hit
    target = state.enemies[1]
    initial_hp_target = target.current_hp
    initial_hp_other = state.enemies[2].current_hp

    action = BattleAction(
        actor_id=state.party[0].battle_id,
        action_type=ActionType.ATTACK,
        target_id=target.battle_id,
    )
    combat.execute_action(action)

    assert state.enemies[1].current_hp < initial_hp_target
    assert state.enemies[2].current_hp == initial_hp_other
