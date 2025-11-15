"""UI voor dialogue."""

from __future__ import annotations

import pygame

from .widgets import Widget


class DialogueBox(Widget):
    """Toont dialooglijnen en keuzes."""

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self._lines: list[str] = []
        self._choices: list[str] = []

    def set_content(self, lines: list[str], choices: list[str]) -> None:
        """Update tekst en keuzeopties."""

        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Render dialoogtekst."""

        pass


__all__ = ["DialogueBox"]
