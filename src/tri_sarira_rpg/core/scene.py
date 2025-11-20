"""Basale scene-architectuur."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Iterable

import pygame


class Scene(ABC):
    """Abstracte basis voor concrete scenes."""

    def __init__(self, manager: SceneManager) -> None:
        self._manager = manager

    @property
    def manager(self) -> SceneManager:
        """Publieke toegang tot de SceneManager."""
        return self._manager

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Ontvang Pygame-events vanuit de hoofdloop."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Werk interne toestanden bij."""

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Teken de scene op het doeloppervlak."""


class SceneManager:
    """Beheert een stack van scenes en hun lifecycle."""

    def __init__(self) -> None:
        self._scenes: deque[Scene] = deque()

    def push_scene(self, scene: Scene) -> None:
        """Voeg een scene toe bovenop de stack."""

        self._scenes.append(scene)

    def pop_scene(self) -> None:
        """Verwijder de huidige scene van de stack."""

        if self._scenes:
            self._scenes.pop()

    def switch_scene(self, scene: Scene) -> None:
        """Vervang de huidige scene door een nieuwe."""

        self.pop_scene()
        self.push_scene(scene)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Stuur input naar de actieve scene."""

        scene = self.active_scene
        if scene:
            scene.handle_event(event)

    def update(self, dt: float) -> None:
        """Laat de actieve scene updaten."""

        scene = self.active_scene
        if scene:
            scene.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """Laat de actieve scene tekenen."""

        scene = self.active_scene
        if scene:
            scene.render(surface)

    @property
    def active_scene(self) -> Scene | None:
        """Huidige scene bovenaan de stack."""

        return self._scenes[-1] if self._scenes else None

    def iter_scenes(self) -> Iterable[Scene]:
        """Geef een iterator over alle scenes (handig voor debug)."""

        return iter(self._scenes)


__all__ = ["Scene", "SceneManager"]
