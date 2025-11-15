"""Spelbootstrap en centrale game-loop."""

from __future__ import annotations

import pygame

from tri_sarira_rpg.core.config import Config
from tri_sarira_rpg.core.scene import SceneManager
from tri_sarira_rpg.presentation.main_menu import TitleScene


class Game:
    """Initialiseert runtime-componenten en beheert de hoofdloop."""

    def __init__(self) -> None:
        """Initialiseer Pygame, config en scenemanager."""
        pygame.init()
        self._config = Config.load()
        self._screen = pygame.display.set_mode(self._config.resolution)
        pygame.display.set_caption(self._config.title)
        self._clock = pygame.time.Clock()
        self._running = True
        self._scene_manager = SceneManager()
        self._scene_manager.push_scene(TitleScene(self._scene_manager))

    def run(self) -> None:
        """Voer de hoofdloop uit totdat de applicatie afsluit."""
        while self._running:
            dt = self._clock.tick(self._config.target_fps) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()

    def stop(self) -> None:
        """Stop de game-loop op het eerstvolgende iteratiemoment."""
        self._running = False

    def _handle_events(self) -> None:
        """Lees Pygame-events en stuur relevante input naar de huidige scene."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop()
            else:
                self._scene_manager.handle_event(event)

    def _update(self, dt: float) -> None:
        """Werk de actieve scene bij."""
        self._scene_manager.update(dt)

    def _render(self) -> None:
        """Laat de actieve scene tekenen en wissel de buffer."""
        self._scene_manager.render(self._screen)
        pygame.display.flip()


__all__ = ["Game"]
