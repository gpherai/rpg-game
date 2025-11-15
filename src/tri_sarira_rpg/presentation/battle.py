"""Battle-presentatie."""

from __future__ import annotations

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager
from tri_sarira_rpg.systems.combat import CombatSystem


class BattleScene(Scene):
    """Visualiseert turn-based gevechten."""

    def __init__(self, manager: SceneManager, combat_system: CombatSystem) -> None:
        super().__init__(manager)
        self._combat = combat_system

    def handle_event(self, event: pygame.event.Event) -> None:
        """Verwerk skillselecties en menu-input."""

        pass

    def update(self, dt: float) -> None:
        """Laat het combatsysteem vooruitgaan."""

        pass

    def render(self, surface: pygame.Surface) -> None:
        """Teken units, UI en feedback."""

        pass


__all__ = ["BattleScene"]
