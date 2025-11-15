"""HUD-componenten voor overworld/battle."""

from __future__ import annotations

import pygame

from .widgets import Widget


class HUD(Widget):
    """Container voor statusinformatie (HP, tijd, etc.)."""

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)

    def update_stats(self, payload: dict[str, object]) -> None:
        """Ontvang data van systemen en sla tijdelijk op."""

        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Render statuselementen."""

        pass


__all__ = ["HUD"]
