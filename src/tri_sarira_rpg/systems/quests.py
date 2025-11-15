"""Quest-logica en state-machine."""

from __future__ import annotations

from typing import Any


class QuestSystem:
    """Beheert queststates, objectives en beloningen."""

    def __init__(self, data_repository: Any | None = None) -> None:
        self._data_repository = data_repository
        self._quests: dict[str, dict[str, Any]] = {}

    def start_quest(self, quest_id: str) -> None:
        """Activeer een quest indien nog niet begonnen."""

        pass

    def advance_stage(self, quest_id: str, stage_id: str) -> None:
        """Markeer dat een stage is voltooid en ga naar de volgende."""

        pass

    def complete_quest(self, quest_id: str) -> None:
        """Rond een quest af en verwerk rewards/flags."""

        pass


__all__ = ["QuestSystem"]
