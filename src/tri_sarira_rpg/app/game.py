"""Spelbootstrap en centrale game-loop."""

from __future__ import annotations

import logging
from pathlib import Path

import pygame

from tri_sarira_rpg.core.config import Config
from tri_sarira_rpg.core.logging_setup import configure_logging
from tri_sarira_rpg.core.scene import SceneStackManager
from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.presentation.main_menu import MainMenuScene
from tri_sarira_rpg.presentation.overworld import OverworldScene
from tri_sarira_rpg.systems.combat import CombatSystem
from tri_sarira_rpg.systems.dialogue import DialogueSystem
from tri_sarira_rpg.systems.equipment import EquipmentSystem
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.quest import QuestSystem
from tri_sarira_rpg.systems.save import SaveSystem
from tri_sarira_rpg.systems.shop import ShopSystem
from tri_sarira_rpg.systems.state import GameStateFlags
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
        if not self._data_repository.load_and_validate_all():
            formatted = DataRepository.format_validation_errors(
                self._data_repository.get_validation_errors()
            )
            for line in formatted.splitlines():
                logger.error(line)
            raise RuntimeError(formatted)
        self._world_system = WorldSystem(data_repository=self._data_repository, maps_dir=maps_dir)
        self._time_system = TimeSystem()

        # Dialogue system
        self._dialogue_system = DialogueSystem(self._data_repository)

        # Party system (Step 4: NPC & Party)
        npc_meta = self._data_repository.get_npc_meta()
        self._party_system = PartySystem(data_repository=self._data_repository, npc_meta=npc_meta)

        # Inventory system (Step 5: Combat v0)
        self._inventory_system = InventorySystem()
        # Add some starter items for v0 testing
        self._inventory_system.add_item("item_small_herb", 3)
        self._inventory_system.add_item("item_medium_herb", 1)
        self._inventory_system.add_item("item_stamina_tonic", 2)

        # Add starter gear items (Step 9: Gear System v0)
        self._inventory_system.add_item("item_gear_simple_staff", 1)
        self._inventory_system.add_item("item_gear_iron_dagger", 1)
        self._inventory_system.add_item("item_gear_travelers_cloth", 1)
        self._inventory_system.add_item("item_gear_leather_vest", 1)
        self._inventory_system.add_item("item_gear_copper_ring", 1)
        self._inventory_system.add_item("item_gear_focus_charm", 1)

        # Equipment system (Step 9: Gear System v0)
        self._equipment_system = EquipmentSystem(
            party_system=self._party_system,
            inventory_system=self._inventory_system,
            data_repository=self._data_repository,
        )

        # Combat system (Step 5: Combat v0)
        self._combat_system = CombatSystem(
            party_system=self._party_system,
            data_repository=self._data_repository,
            equipment_system=self._equipment_system,
        )

        # Game state flags
        self._flags_system = GameStateFlags()

        # Quest system (Step 7: Quest System v0)
        self._quest_system = QuestSystem(
            party_system=self._party_system,
            inventory_system=self._inventory_system,
        )
        # Load quest definitions from JSON
        self._quest_system.load_definitions(self._data_repository)

        # Attach shared systems to world (for triggers/events)
        self._world_system.attach_systems(
            flags_system=self._flags_system,
            quest_system=self._quest_system,
            inventory_system=self._inventory_system,
            combat_system=self._combat_system,
        )

        # Shop system (Step 8: Shop System v0)
        economy_state = {"currency_amount": 500, "shop_states": {}}  # Start with 500 Rūpa
        self._shop_system = ShopSystem(
            data_repository=self._data_repository,
            inventory_system=self._inventory_system,
            economy_state=economy_state,
        )

        # Save system
        self._save_system = SaveSystem(
            party_system=self._party_system,
            world_system=self._world_system,
            time_system=self._time_system,
            inventory_system=self._inventory_system,
            flags_system=self._flags_system,
            quest_system=self._quest_system,
            shop_system=self._shop_system,
        )

        # Play time tracking
        self._play_time: float = 0.0  # Total play time in seconds

        # Scene manager (stack-based implementation)
        self._running = True
        self._scene_manager = SceneStackManager()

        # Start with main menu (F11 requirement)
        main_menu = MainMenuScene(self._scene_manager, game_instance=self)
        self._scene_manager.push_scene(main_menu)

        logger.info("✓ Game initialized, entering main menu")

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

        # Track play time
        self._play_time += dt

    def _render(self) -> None:
        """Laat de actieve scene tekenen en wissel de buffer."""
        self._scene_manager.render(self._screen)
        pygame.display.flip()

    def save_game(self, slot_id: int = 1) -> bool:
        """Save game to specified slot.

        Parameters
        ----------
        slot_id : int
            Save slot number (1-5), default 1 for quick save

        Returns
        -------
        bool
            True if save succeeded
        """
        logger.info(f"Saving game to slot {slot_id}...")

        # Build save data
        save_data = self._save_system.build_save(play_time=self._play_time)

        # Write to file
        success = self._save_system.save_to_file(slot_id, save_data)

        if success:
            logger.info(f"✓ Game saved successfully (slot {slot_id})")
        else:
            logger.error(f"✗ Failed to save game (slot {slot_id})")

        return success

    def load_game(self, slot_id: int = 1) -> bool:
        """Load game from specified slot.

        Parameters
        ----------
        slot_id : int
            Save slot number (1-5), default 1 for quick load

        Returns
        -------
        bool
            True if load succeeded
        """
        logger.info(f"Loading game from slot {slot_id}...")

        # Load save data from file
        save_data = self._save_system.load_from_file(slot_id)

        if not save_data:
            logger.error(f"✗ No save found in slot {slot_id}")
            return False

        # Restore game state
        success = self._save_system.load_save(save_data)

        if success:
            # Restore play time
            meta = save_data.get("meta", {})
            self._play_time = meta.get("play_time", 0.0)

            logger.info(f"✓ Game loaded successfully (slot {slot_id})")
        else:
            logger.error(f"✗ Failed to load game (slot {slot_id})")

        return success

    def start_new_game(self) -> None:
        """Start a fresh new game with default state.

        Initializes a new game with:
        - Adhira as main character
        - Starting zone: Chandrapur town
        - Default inventory (healing herbs, tonics)
        - Day 1, Morgen
        """
        logger.info("Initializing new game...")

        # Reset play time
        self._play_time = 0.0

        # Re-initialize time system (Day 1)
        self._time_system = TimeSystem()

        # Re-initialize party with main character
        # NOTE: PartySystem.__init__ automatically reads npc_meta.json and initializes
        # the party based on companion_flags. Adhira (npc_mc_adhira) is already marked
        # with recruited=true and in_party=true, so no manual party manipulation needed.
        npc_meta = self._data_repository.get_npc_meta()
        self._party_system = PartySystem(data_repository=self._data_repository, npc_meta=npc_meta)

        # Re-initialize inventory with starter items
        self._inventory_system = InventorySystem()
        self._inventory_system.add_item("item_small_herb", 3)
        self._inventory_system.add_item("item_medium_herb", 1)
        self._inventory_system.add_item("item_stamina_tonic", 2)

        # Add starter gear items (Step 9: Gear System v0)
        self._inventory_system.add_item("item_gear_simple_staff", 1)
        self._inventory_system.add_item("item_gear_iron_dagger", 1)
        self._inventory_system.add_item("item_gear_travelers_cloth", 1)
        self._inventory_system.add_item("item_gear_leather_vest", 1)
        self._inventory_system.add_item("item_gear_copper_ring", 1)
        self._inventory_system.add_item("item_gear_focus_charm", 1)

        # Re-initialize equipment system
        self._equipment_system = EquipmentSystem(
            party_system=self._party_system,
            inventory_system=self._inventory_system,
            data_repository=self._data_repository,
        )

        # Re-initialize flags and quests
        self._flags_system = GameStateFlags()
        self._quest_system = QuestSystem(
            party_system=self._party_system,
            inventory_system=self._inventory_system,
        )
        self._quest_system.load_definitions(self._data_repository)

        # Re-attach shared systems to world (for triggers/events)
        self._world_system.attach_systems(
            flags_system=self._flags_system,
            quest_system=self._quest_system,
            inventory_system=self._inventory_system,
            combat_system=self._combat_system,
        )

        # Re-initialize shop system with starting currency
        economy_state = {"currency_amount": 500, "shop_states": {}}
        self._shop_system = ShopSystem(
            data_repository=self._data_repository,
            inventory_system=self._inventory_system,
            economy_state=economy_state,
        )

        # Re-initialize combat system with new party
        self._combat_system = CombatSystem(
            party_system=self._party_system,
            data_repository=self._data_repository,
            equipment_system=self._equipment_system,
        )

        # Re-initialize save system with new references
        self._save_system = SaveSystem(
            party_system=self._party_system,
            world_system=self._world_system,
            time_system=self._time_system,
            inventory_system=self._inventory_system,
            flags_system=self._flags_system,
            quest_system=self._quest_system,
            shop_system=self._shop_system,
        )

        # Load starting zone
        start_zone_id = "z_r1_chandrapur_town"
        self._world_system.reset_state()
        try:
            self._world_system.load_zone(start_zone_id)
            logger.info(f"✓ Starting zone loaded: {start_zone_id}")
        except Exception as e:
            logger.error(f"Failed to load start zone {start_zone_id}: {e}")

        # Switch to overworld scene
        self.start_overworld()

    def start_overworld(self) -> None:
        """Create and switch to overworld scene.

        Used when:
        - Starting a new game
        - Loading a game
        - Returning from battle
        """
        logger.info("Starting overworld scene...")

        # Create overworld scene and use clear_and_set to replace entire stack
        overworld_scene = OverworldScene(
            self._scene_manager,
            self._world_system,
            self._time_system,
            self._party_system,
            self._combat_system,
            self._inventory_system,
            self._data_repository,
            self._dialogue_system,
            flags_system=self._flags_system,
            quest_system=self._quest_system,
            shop_system=self._shop_system,
            equipment_system=self._equipment_system,
            game_instance=self,
        )
        self._scene_manager.clear_and_set(overworld_scene)

        logger.info("✓ Overworld scene started")

    def return_to_main_menu(self) -> None:
        """Return to main menu from gameplay.

        Clears all scenes and sets a fresh main menu.
        """
        logger.info("Returning to main menu...")

        # Use clear_and_set to replace entire stack with main menu
        main_menu = MainMenuScene(self._scene_manager, game_instance=self)
        self._scene_manager.clear_and_set(main_menu)

        logger.info("✓ Returned to main menu")


__all__ = ["Game"]
