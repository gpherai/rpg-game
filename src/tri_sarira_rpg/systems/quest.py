"""Quest system for Tri-Śarīra RPG.

Handles quest state, progression, and rewards.
See: docs/architecture/3.4 Quests & Dialogue System Spec – Tri-Śarīra RPG.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class QuestStatus(Enum):
    """Status of a quest."""

    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"  # For future use


@dataclass
class QuestRewardDefinition:
    """Rewards given when a quest is completed."""

    xp: int = 0
    money: int = 0
    items: list[dict[str, Any]] = field(default_factory=list)  # [{"item_id": str, "quantity": int}]


@dataclass
class QuestStageDefinition:
    """A stage within a quest."""

    stage_id: str
    description: str
    is_final: bool = False
    next_stage_id: str | None = None


@dataclass
class QuestDefinition:
    """Complete definition of a quest loaded from JSON."""

    quest_id: str
    title: str
    description: str
    stages: list[QuestStageDefinition]
    rewards: QuestRewardDefinition | None = None


@dataclass
class QuestState:
    """Runtime state of a quest."""

    quest_id: str
    status: QuestStatus
    current_stage_id: str | None = None


@dataclass
class QuestLogEntry:
    """UI-friendly quest entry for quest log."""

    quest_id: str
    title: str
    status: QuestStatus
    current_stage_description: str
    is_tracked: bool = False  # For future use


class QuestSystem:
    """Manages quest state and progression."""

    def __init__(
        self,
        party_system: Any | None = None,
        inventory_system: Any | None = None,
    ) -> None:
        """Initialize QuestSystem.

        Parameters
        ----------
        party_system : Any | None
            PartySystem for XP rewards
        inventory_system : Any | None
            InventorySystem for item and money rewards
        """
        self._definitions: dict[str, QuestDefinition] = {}
        self._states: dict[str, QuestState] = {}
        self._party_system = party_system
        self._inventory_system = inventory_system

    def load_definitions(self, data_repository: Any) -> None:
        """Load quest definitions from data repository.

        Parameters
        ----------
        data_repository : DataRepository
            Repository to load quest data from
        """
        quest_data_list = data_repository.get_all_quests()
        definitions = load_quests_from_data(quest_data_list)
        self._definitions = definitions
        logger.info(f"Loaded {len(definitions)} quest definitions")

    def get_definition(self, quest_id: str) -> QuestDefinition | None:
        """Get quest definition by ID.

        Parameters
        ----------
        quest_id : str
            Quest ID

        Returns
        -------
        QuestDefinition | None
            Quest definition if found
        """
        return self._definitions.get(quest_id)

    def get_state(self, quest_id: str) -> QuestState:
        """Get quest state, creating NOT_STARTED if doesn't exist.

        Parameters
        ----------
        quest_id : str
            Quest ID

        Returns
        -------
        QuestState
            Current quest state
        """
        if quest_id not in self._states:
            self._states[quest_id] = QuestState(
                quest_id=quest_id,
                status=QuestStatus.NOT_STARTED,
                current_stage_id=None,
            )
        return self._states[quest_id]

    def start_quest(self, quest_id: str) -> QuestState:
        """Start a quest.

        Parameters
        ----------
        quest_id : str
            Quest ID to start

        Returns
        -------
        QuestState
            Updated quest state
        """
        state = self.get_state(quest_id)
        definition = self.get_definition(quest_id)

        if not definition:
            logger.error(f"Cannot start quest '{quest_id}': definition not found")
            raise ValueError(f"Quest definition not found: {quest_id}")

        if state.status == QuestStatus.COMPLETED:
            logger.info(f"Quest '{quest_id}' already completed, not starting")
            return state

        if state.status == QuestStatus.ACTIVE:
            logger.info(f"Quest '{quest_id}' already active")
            raise ValueError(f"Quest '{quest_id}' is already active")

        # Start the quest
        state.status = QuestStatus.ACTIVE
        if definition.stages:
            state.current_stage_id = definition.stages[0].stage_id
            logger.info(f"Started quest '{quest_id}' at stage '{state.current_stage_id}'")
        else:
            logger.warning(f"Quest '{quest_id}' has no stages")

        return state

    def advance_quest(self, quest_id: str, next_stage_id: str | None = None) -> QuestState:
        """Advance quest to next stage.

        Parameters
        ----------
        quest_id : str
            Quest ID
        next_stage_id : str | None
            Explicit next stage ID, or None to use current stage's next_stage_id

        Returns
        -------
        QuestState
            Updated quest state
        """
        state = self.get_state(quest_id)
        definition = self.get_definition(quest_id)

        if not definition:
            logger.error(f"Cannot advance quest '{quest_id}': definition not found")
            raise ValueError(f"Quest definition not found: {quest_id}")

        if state.status != QuestStatus.ACTIVE:
            logger.error(f"Quest '{quest_id}' is not active (status: {state.status.value})")
            raise ValueError(f"Quest '{quest_id}' is not active")

        # Determine next stage
        target_stage_id = next_stage_id

        if target_stage_id is None:
            # Use current stage's next_stage_id
            current_stage = self._get_stage_definition(definition, state.current_stage_id)
            if current_stage:
                target_stage_id = current_stage.next_stage_id
            else:
                logger.warning(f"Cannot find current stage '{state.current_stage_id}' in quest '{quest_id}'")
                return state

        if target_stage_id is None:
            logger.warning(f"No next stage defined for quest '{quest_id}' stage '{state.current_stage_id}'")
            return state

        # Advance to target stage
        target_stage = self._get_stage_definition(definition, target_stage_id)
        if not target_stage:
            logger.error(f"Target stage '{target_stage_id}' not found in quest '{quest_id}'")
            return state

        state.current_stage_id = target_stage_id
        logger.info(f"Advanced quest '{quest_id}' to stage '{target_stage_id}'")

        if target_stage.is_final:
            logger.info(f"Quest '{quest_id}' reached final stage '{target_stage_id}'")

        return state

    def complete_quest(self, quest_id: str) -> QuestState:
        """Complete a quest and apply rewards.

        Parameters
        ----------
        quest_id : str
            Quest ID to complete

        Returns
        -------
        QuestState
            Updated quest state
        """
        state = self.get_state(quest_id)
        definition = self.get_definition(quest_id)

        if not definition:
            logger.error(f"Cannot complete quest '{quest_id}': definition not found")
            raise ValueError(f"Quest definition not found: {quest_id}")

        if state.status != QuestStatus.ACTIVE:
            logger.error(f"Quest '{quest_id}' is not active (status: {state.status.value})")
            raise ValueError(f"Quest '{quest_id}' is not active")

        # Mark as completed
        state.status = QuestStatus.COMPLETED
        logger.info(f"Completed quest '{quest_id}'")

        # Apply rewards
        if definition.rewards:
            self._apply_rewards(quest_id, definition.rewards)

        return state

    def get_active_quests(self) -> list[QuestState]:
        """Get all active quests.

        Returns
        -------
        list[QuestState]
            List of active quest states
        """
        return [state for state in self._states.values() if state.status == QuestStatus.ACTIVE]

    def build_quest_log_view(self) -> list[QuestLogEntry]:
        """Build quest log view for UI.

        Returns
        -------
        list[QuestLogEntry]
            List of quest log entries (ACTIVE and COMPLETED quests)
        """
        entries = []

        for state in self._states.values():
            # Show ACTIVE and COMPLETED quests (not NOT_STARTED or FAILED)
            if state.status not in (QuestStatus.ACTIVE, QuestStatus.COMPLETED):
                continue

            definition = self.get_definition(state.quest_id)
            if not definition:
                continue

            # Get current stage description
            stage_desc = ""
            if state.status == QuestStatus.COMPLETED:
                stage_desc = "Quest voltooid!"
            elif state.current_stage_id:
                stage = self._get_stage_definition(definition, state.current_stage_id)
                if stage:
                    stage_desc = stage.description

            entries.append(
                QuestLogEntry(
                    quest_id=state.quest_id,
                    title=definition.title,
                    status=state.status,
                    current_stage_description=stage_desc,
                    is_tracked=False,
                )
            )

        return entries

    def get_save_state(self) -> list[dict[str, Any]]:
        """Get serializable quest state for saving.

        Returns
        -------
        list[dict[str, Any]]
            List of quest states (only non-NOT_STARTED quests)
        """
        save_data = []

        for state in self._states.values():
            if state.status == QuestStatus.NOT_STARTED:
                continue

            save_data.append({
                "quest_id": state.quest_id,
                "status": state.status.value,
                "current_stage_id": state.current_stage_id,
            })

        return save_data

    def restore_from_save(self, save_data: list[dict[str, Any]]) -> None:
        """Restore quest state from save data.

        Parameters
        ----------
        save_data : list[dict[str, Any]]
            List of saved quest states
        """
        self._states.clear()

        for quest_data in save_data:
            quest_id = quest_data.get("quest_id")
            if not quest_id:
                logger.warning("Quest data missing quest_id, skipping")
                continue

            # Check if quest definition exists
            if quest_id not in self._definitions:
                logger.warning(f"Quest '{quest_id}' in save data but definition not found, skipping")
                continue

            status_str = quest_data.get("status", "NOT_STARTED")
            try:
                status = QuestStatus(status_str)
            except ValueError:
                logger.warning(f"Invalid quest status '{status_str}' for quest '{quest_id}', using NOT_STARTED")
                status = QuestStatus.NOT_STARTED

            self._states[quest_id] = QuestState(
                quest_id=quest_id,
                status=status,
                current_stage_id=quest_data.get("current_stage_id"),
            )

        logger.info(f"Restored {len(self._states)} quest states from save")

    def _get_stage_definition(
        self, definition: QuestDefinition, stage_id: str | None
    ) -> QuestStageDefinition | None:
        """Get stage definition by ID."""
        if not stage_id:
            return None

        for stage in definition.stages:
            if stage.stage_id == stage_id:
                return stage

        return None

    def _apply_rewards(self, quest_id: str, rewards: QuestRewardDefinition) -> None:
        """Apply quest rewards.

        Parameters
        ----------
        quest_id : str
            Quest ID (for logging)
        rewards : QuestRewardDefinition
            Rewards to apply
        """
        logger.info(f"Applying rewards for quest '{quest_id}'")

        # XP rewards
        if rewards.xp > 0:
            if self._party_system:
                # Grant XP to all active party members
                active_party = self._party_system.get_active_party()
                for member in active_party:
                    member.xp += rewards.xp
                    logger.info(f"Granted {rewards.xp} XP to {member.actor_id} (total: {member.xp})")
            else:
                logger.warning(f"Cannot grant {rewards.xp} XP: no party system")

        # Money rewards
        if rewards.money > 0:
            if self._inventory_system:
                # Add money to inventory
                if hasattr(self._inventory_system, "add_money"):
                    self._inventory_system.add_money(rewards.money)
                    logger.info(f"Granted {rewards.money} money")
                elif hasattr(self._inventory_system, "money"):
                    self._inventory_system.money += rewards.money
                    logger.info(f"Granted {rewards.money} money (total: {self._inventory_system.money})")
                else:
                    # No money system yet, just log
                    logger.info(f"Would grant {rewards.money} money (not implemented)")
            else:
                logger.warning(f"Cannot grant {rewards.money} money: no inventory system")

        # Item rewards
        if rewards.items:
            if self._inventory_system:
                for item_data in rewards.items:
                    item_id = item_data.get("item_id")
                    quantity = item_data.get("quantity", 1)
                    if item_id:
                        self._inventory_system.add_item(item_id, quantity)
                        logger.info(f"Granted {quantity}x {item_id}")
            else:
                logger.warning(f"Cannot grant items: no inventory system")


def parse_quest_from_json(quest_data: dict[str, Any]) -> QuestDefinition:
    """Parse JSON quest data into QuestDefinition.

    Parameters
    ----------
    quest_data : dict[str, Any]
        Quest data from JSON

    Returns
    -------
    QuestDefinition
        Parsed quest definition
    """
    # Parse stages
    stages = []
    for stage_data in quest_data.get("stages", []):
        stages.append(
            QuestStageDefinition(
                stage_id=stage_data["stage_id"],
                description=stage_data["description"],
                is_final=stage_data.get("is_final", False),
                next_stage_id=stage_data.get("next_stage_id"),
            )
        )

    # Parse rewards
    rewards = None
    rewards_data = quest_data.get("rewards")
    if rewards_data:
        rewards = QuestRewardDefinition(
            xp=rewards_data.get("xp", 0),
            money=rewards_data.get("money", 0),
            items=rewards_data.get("items", []),
        )

    return QuestDefinition(
        quest_id=quest_data["quest_id"],
        title=quest_data["title"],
        description=quest_data["description"],
        stages=stages,
        rewards=rewards,
    )


def load_quests_from_data(quests_data: list[dict[str, Any]]) -> dict[str, QuestDefinition]:
    """Load quests from JSON data.

    Parameters
    ----------
    quests_data : list[dict[str, Any]]
        List of quest data from JSON

    Returns
    -------
    dict[str, QuestDefinition]
        Map of quest_id -> QuestDefinition
    """
    definitions = {}
    for quest_data in quests_data:
        try:
            definition = parse_quest_from_json(quest_data)
            definitions[definition.quest_id] = definition
        except KeyError as e:
            logger.error(f"Failed to parse quest: missing key {e}")
        except Exception as e:
            logger.error(f"Failed to parse quest: {e}")

    return definitions


__all__ = [
    "QuestStatus",
    "QuestRewardDefinition",
    "QuestStageDefinition",
    "QuestDefinition",
    "QuestState",
    "QuestLogEntry",
    "QuestSystem",
    "parse_quest_from_json",
    "load_quests_from_data",
]
