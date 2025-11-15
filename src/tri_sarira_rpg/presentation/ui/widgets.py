"""Basale UI-widgets."""

from __future__ import annotations

import pygame


class Widget:
    """Abstracte widget die getekend kan worden."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect

    def handle_event(self, event: pygame.event.Event) -> None:
        """Ontvang input voor klik- of key-events."""

        pass

    def update(self, dt: float) -> None:
        """Laat animaties/overgangen verlopen."""

        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Teken de widget binnen zijn rect."""

        pass


class Container(Widget):
    """Groepering van child-widgets."""

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self._children: list[Widget] = []

    def add_child(self, widget: Widget) -> None:
        """Voeg een widget toe."""

        self._children.append(widget)

    def iter_children(self) -> list[Widget]:
        """Retourneer huidige children voor lay-out."""

        return list(self._children)


__all__ = ["Widget", "Container"]
