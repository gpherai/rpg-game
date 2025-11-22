"""Basale scene-architectuur met SceneManager protocol.

Dit bestand bevat:
- Scene: Abstracte basis voor concrete scenes
- SceneManagerProtocol: Interface voor scene managers
- SceneStackManager: Stack-gebaseerde implementatie
- SceneManager: Alias voor backwards compatibility
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Iterable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import pygame

if TYPE_CHECKING:
    pass


# =============================================================================
# SceneManagerProtocol - interface voor scene managers
# =============================================================================


@runtime_checkable
class SceneManagerProtocol(Protocol):
    """Protocol voor scene managers.

    Definieert de interface die alle scene managers moeten implementeren.
    Dit maakt het mogelijk om verschillende implementaties te gebruiken
    (bijv. stack-based, state machine, etc.) zonder de rest van de code
    te wijzigen.

    Toekomstige features die dit patroon ondersteunt:
    - Overlay scenes (pause menu, dialogs)
    - Cutscenes als tijdelijke scenes
    - Scene transitions met animaties
    - Scene caching voor snelle wissels
    """

    @property
    def active_scene(self) -> Scene | None:
        """Huidige actieve scene (top van de stack)."""
        ...

    def push_scene(self, scene: Scene) -> None:
        """Voeg een scene toe bovenop de stack.

        Gebruik voor:
        - Overlay scenes (pause menu blijft boven gameplay)
        - Tijdelijke scenes die terugkeren naar vorige scene
        """
        ...

    def pop_scene(self) -> None:
        """Verwijder de huidige scene van de stack.

        Gebruik voor:
        - Terug naar vorige scene na overlay/popup
        - Scene cleanup
        """
        ...

    def switch_scene(self, scene: Scene) -> None:
        """Vervang de huidige scene door een nieuwe.

        Gebruik voor:
        - Directe scene wissel (bijv. main menu → overworld)
        """
        ...

    def clear_and_set(self, scene: Scene) -> None:
        """Leeg de stack en zet een nieuwe scene.

        Gebruik voor:
        - Volledige reset (bijv. naar main menu)
        - Start van een nieuwe game
        """
        ...

    def handle_event(self, event: pygame.event.Event) -> None:
        """Stuur input naar de actieve scene."""
        ...

    def update(self, dt: float) -> None:
        """Laat de actieve scene updaten."""
        ...

    def render(self, surface: pygame.Surface) -> None:
        """Laat de actieve scene tekenen."""
        ...

    def iter_scenes(self) -> Iterable[Scene]:
        """Geef een iterator over alle scenes (handig voor debug)."""
        ...


# =============================================================================
# Scene - abstracte basis voor concrete scenes
# =============================================================================


class Scene(ABC):
    """Abstracte basis voor concrete scenes.

    Scenes zijn de bouwstenen van de game flow:
    - MainMenuScene: Hoofdmenu
    - OverworldScene: Exploratie en NPC interactie
    - BattleScene: Gevechten

    Elke scene ontvangt een referentie naar de SceneManager voor
    scene-wissels, maar communiceert bij voorkeur via GameProtocol.
    """

    def __init__(self, manager: SceneManagerProtocol) -> None:
        self._manager = manager

    @property
    def manager(self) -> SceneManagerProtocol:
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


# =============================================================================
# SceneStackManager - concrete stack-gebaseerde implementatie
# =============================================================================


class SceneStackManager:
    """Stack-gebaseerde scene manager.

    Beheert een stack van scenes waar alleen de bovenste (actieve) scene
    input ontvangt en gerenderd wordt.

    Stack semantiek:
    - push_scene: Voeg scene toe (voor overlays, pause menu)
    - pop_scene: Verwijder bovenste scene (terug naar vorige)
    - switch_scene: Vervang bovenste scene
    - clear_and_set: Leeg stack en zet nieuwe scene

    Voorbeeld gebruik:
        manager = SceneStackManager()
        manager.push_scene(MainMenuScene(manager))  # Start met menu
        manager.switch_scene(OverworldScene(manager))  # Wissel naar game
        manager.push_scene(PauseMenu(manager))  # Overlay pause menu
        manager.pop_scene()  # Terug naar overworld
    """

    def __init__(self) -> None:
        self._scenes: deque[Scene] = deque()

    @property
    def active_scene(self) -> Scene | None:
        """Huidige scene bovenaan de stack."""
        return self._scenes[-1] if self._scenes else None

    def push_scene(self, scene: Scene) -> None:
        """Voeg een scene toe bovenop de stack."""
        self._scenes.append(scene)

    def pop_scene(self) -> None:
        """Verwijder de huidige scene van de stack.

        Doet niets als de stack leeg is (defensief).
        """
        if self._scenes:
            self._scenes.pop()

    def switch_scene(self, scene: Scene) -> None:
        """Vervang de huidige scene door een nieuwe.

        Equivalent aan pop + push, maar atomair.
        """
        self.pop_scene()
        self.push_scene(scene)

    def clear_and_set(self, scene: Scene) -> None:
        """Leeg de stack en zet een nieuwe scene.

        Handig voor volledige resets zoals terug naar main menu.
        """
        self._scenes.clear()
        self._scenes.append(scene)

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

    def iter_scenes(self) -> Iterable[Scene]:
        """Geef een iterator over alle scenes (handig voor debug)."""
        return iter(self._scenes)

    def __len__(self) -> int:
        """Aantal scenes in de stack."""
        return len(self._scenes)


# =============================================================================
# Backwards compatibility alias
# =============================================================================

# SceneManager is nu een alias voor SceneStackManager
# Dit zorgt ervoor dat bestaande code blijft werken
SceneManager = SceneStackManager


__all__ = [
    "Scene",
    "SceneManagerProtocol",
    "SceneStackManager",
    "SceneManager",  # Backwards compatibility alias
]
