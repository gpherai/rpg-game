"""Spelbootstrap en centrale game-loop."""

from __future__ import annotations

import logging
from pathlib import Path

import pygame

from tri_sarira_rpg.core.config import Config
from tri_sarira_rpg.core.logging_setup import configure_logging
from tri_sarira_rpg.core.scene import SceneManager
from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.presentation.overworld import OverworldScene
from tri_sarira_rpg.systems.combat import CombatSystem
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.time import TimeSystem
from tri_sarira_rpg.systems.world import WorldSystem

logger = logging.getLogger(__name__)


class Game:
    """Initialiseert runtime-componenten en beheert de hoofdloop."""

    def __init__(self) -> None:
        """Initialiseer Pygame, config en scenemanager."""
        # Load config
        self._config = Config.load()

        # Setup logging
        configure_logging(level=self._config.log_level)
        logger.info("Tri-Sarira RPG - Step 3: World & Overworld starting...")

        # Init Pygame
        pygame.init()
        self._screen = pygame.display.set_mode(self._config.resolution)
        pygame.display.set_caption(self._config.title)
        self._clock = pygame.time.Clock()

        # Initialize systems
        project_root = Path.cwd()
        if (project_root / "src").exists():
            maps_dir = project_root / "maps"
            data_dir = project_root / "data"
        else:
            # Running from different directory
            maps_dir = Path("maps")
            data_dir = Path("data")

        self._data_repository = DataRepository(data_dir=data_dir)
        self._world_system = WorldSystem(
            data_repository=self._data_repository, maps_dir=maps_dir
        )
        self._time_system = TimeSystem()

        # Party system (Step 4: NPC & Party)
        npc_meta = self._data_repository.get_npc_meta()
        self._party_system = PartySystem(
            data_repository=self._data_repository, npc_meta=npc_meta
        )

        # Inventory system (Step 5: Combat v0)
        self._inventory_system = InventorySystem()
        # Add some starter items for v0 testing
        self._inventory_system.add_item("item_small_herb", 3)
        self._inventory_system.add_item("item_medium_herb", 1)
        self._inventory_system.add_item("item_stamina_tonic", 2)

        # Combat system (Step 5: Combat v0)
        self._combat_system = CombatSystem(
            party_system=self._party_system,
            data_repository=self._data_repository,
        )

        # Scene manager
        self._running = True
        self._scene_manager = SceneManager()

        # Start directly in overworld (Step 3 requirement)
        # Load initial zone
        start_zone_id = "z_r1_chandrapur_town"
        try:
            self._world_system.load_zone(start_zone_id)
            logger.info(f"✓ Starting in zone: {start_zone_id}")
        except Exception as e:
            logger.error(f"Failed to load start zone {start_zone_id}: {e}")
            logger.info("Will use placeholder zone instead")

        # Create and push overworld scene
        overworld_scene = OverworldScene(
            self._scene_manager,
            self._world_system,
            self._time_system,
            self._party_system,
            self._combat_system,
            self._inventory_system,
            self._data_repository,
        )
        self._scene_manager.push_scene(overworld_scene)

        logger.info("✓ Game initialized, entering overworld")

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
