"""Placeholder for the main Pause Menu Scene.

This file is intentionally left mostly empty as a placeholder for a more comprehensive
Pause Menu Scene implementation in a future step.

The current functional Pause Menu *widget* is located at `src/tri_sarira_rpg/presentation/ui/pause_menu.py`.
This placeholder scene might eventually manage that widget or a more complex pause state.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import GameProtocol

logger = logging.getLogger(__name__)


class PauseMenuScene(Scene):
    """Placeholder Scene for the main Pause Menu.

    Currently, a functional PauseMenu widget exists in presentation/ui/pause_menu.py.
    This scene is a placeholder for a dedicated Pause Menu *screen* (a Scene)
    that might integrate that widget or manage more complex pause logic later.
    """

    def __init__(
        self,
        manager: SceneManager,
        game_instance: GameProtocol | None = None,
    ) -> None:
        super().__init__(manager)
        self._game = game_instance
        logger.debug("PauseMenuScene placeholder initialized")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle events for the placeholder scene."""
        # For a placeholder, we might just allow closing
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop_scene()

    def update(self, dt: float) -> None:
        """Update for the placeholder scene."""
        pass  # No logic yet

    def render(self, surface: pygame.Surface) -> None:
        """Render for the placeholder scene."""
        # For a placeholder, we might just draw a simple message
        surface.fill((50, 50, 50))  # Dark grey background
        font = pygame.font.SysFont("monospace", 40)
        text_surface = font.render("PAUZE MENU SCENE (PLACEHOLDER)", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=surface.get_rect().center)
        surface.blit(text_surface, text_rect)
        
        info_font = pygame.font.SysFont("monospace", 20)
        info_text_surface = info_font.render("Druk op ESC om terug te gaan", True, (200, 200, 200))
        info_text_rect = info_text_surface.get_rect(center=(surface.get_rect().centerx, surface.get_rect().centery + 50))
        surface.blit(info_text_surface, info_text_rect)
