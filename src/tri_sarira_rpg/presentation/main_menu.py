"""Titel- en menuscenes."""

from __future__ import annotations

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager


class TitleScene(Scene):
    """Eerste scene met logo en startopties."""

    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Verwerk input zoals 'start game'."""

        pass

    def update(self, dt: float) -> None:
        """Update animaties of timers."""

        pass

    def render(self, surface: pygame.Surface) -> None:
        """Teken placeholder UI."""

        pass


class PauseMenuScene(Scene):
    """Overlay voor pauzemenu's."""

    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Verwerk menu-navigatie."""

        pass

    def update(self, dt: float) -> None:
        """Eventuele animaties of timers."""

        pass

    def render(self, surface: pygame.Surface) -> None:
        """Teken hetpauze-overlay."""

        pass


__all__ = ["TitleScene", "PauseMenuScene"]
