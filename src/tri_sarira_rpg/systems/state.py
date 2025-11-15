"""Globale flags en karma-tracking."""

from __future__ import annotations


class GameStateFlags:
    """Beheert storyflags, karma en choice history."""

    def __init__(self) -> None:
        self._flags: set[str] = set()
        self._choices: dict[str, str] = {}

    def set_flag(self, flag_id: str) -> None:
        """Markeer dat een flag gezet is."""

        self._flags.add(flag_id)

    def clear_flag(self, flag_id: str) -> None:
        """Verwijder een flag indien nodig."""

        self._flags.discard(flag_id)

    def record_choice(self, choice_id: str, outcome: str) -> None:
        """Leg belangrijke keuzes vast voor save/export."""

        self._choices[choice_id] = outcome

    def has_flag(self, flag_id: str) -> bool:
        """Check of een flag actief is."""

        return flag_id in self._flags


__all__ = ["GameStateFlags"]
