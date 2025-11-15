"""Menucomponenten (inventory, status, etc.)."""

from __future__ import annotations

import pygame

from .widgets import Widget


class Menu(Widget):
    """Basis voor lijsten/opties."""

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self._options: list[str] = []
        self._selected_index: int = 0

    def set_options(self, options: list[str]) -> None:
        """Vervang menu-inhoud."""

        self._options = options

    def move_selection(self, delta: int) -> None:
        """Verplaats selectie in het menu."""

        pass

    def get_selected_option(self) -> str | None:
        """Retourneer huidige selectie."""

        if not self._options:
            return None
        return self._options[self._selected_index]


__all__ = ["Menu"]
