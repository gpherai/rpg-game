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

    def get_save_state(self) -> dict[str, list[str] | dict[str, str]]:
        """Get serializable flags state for saving.

        Returns
        -------
        dict[str, list[str] | dict[str, str]]
            Flags state as dict
        """
        return {
            "story_flags": list(self._flags),
            "choice_history": dict(self._choices),
        }

    def restore_from_save(self, state_dict: dict[str, list[str] | dict[str, str]]) -> None:
        """Restore flags state from save data.

        Parameters
        ----------
        state_dict : dict[str, list[str] | dict[str, str]]
            Flags state dict from save file
        """
        # Clear current state
        self._flags.clear()
        self._choices.clear()

        # Restore flags
        flags = state_dict.get("story_flags", [])
        if isinstance(flags, list):
            self._flags.update(flags)

        # Restore choices
        choices = state_dict.get("choice_history", {})
        if isinstance(choices, dict):
            self._choices.update(choices)


__all__ = ["GameStateFlags"]
