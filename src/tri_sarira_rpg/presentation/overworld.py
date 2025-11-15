"""Weergave van de overworld."""

from __future__ import annotations

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager
from tri_sarira_rpg.systems.world import WorldSystem


class OverworldScene(Scene):
    """Toont maps, spelersprite en interacties."""

    def __init__(self, manager: SceneManager, world_system: WorldSystem) -> None:
        super().__init__(manager)
        self._world = world_system

    def handle_event(self, event: pygame.event.Event) -> None:
        """Verwerk beweging en interacties."""

        pass

    def update(self, dt: float) -> None:
        """Vraag world-systemen te updaten."""

        pass

    def render(self, surface: pygame.Surface) -> None:
        """Teken maptiles, actor-sprites en HUD."""

        pass


__all__ = ["OverworldScene"]
