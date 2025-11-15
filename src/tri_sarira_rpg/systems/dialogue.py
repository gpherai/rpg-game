"""Dialooggraphs en keuzes."""

from __future__ import annotations

from typing import Any


class DialogueSystem:
    """Beheert dialoogstate en levert nodes aan UI."""

    def __init__(self, data_repository: Any | None = None) -> None:
        self._data_repository = data_repository
        self._active_dialogue: dict[str, Any] | None = None

    def start_dialogue(self, dialogue_id: str) -> None:
        """Laad een dialooggraph en reset state."""

        pass

    def select_choice(self, choice_id: str) -> None:
        """Verwerk spelerkeuze en ga naar volgende node."""

        pass

    def current_node(self) -> dict[str, Any] | None:
        """Retourneer de node die aan UI getoond moet worden."""

        return self._active_dialogue


__all__ = ["DialogueSystem"]
