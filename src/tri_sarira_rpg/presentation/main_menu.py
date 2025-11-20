"""Main Menu en Pause Menu scenes/UI components."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager

if TYPE_CHECKING:
    from tri_sarira_rpg.systems.save import SaveSystem

logger = logging.getLogger(__name__)


class MainMenuOption(Enum):
    """Main menu opties."""

    NEW_GAME = 0
    CONTINUE = 1
    LOAD_GAME = 2
    OPTIONS = 3
    QUIT = 4


class MainMenuState(Enum):
    """States voor het main menu."""

    MAIN = "main"
    LOAD_SELECT = "load_select"
    OPTIONS = "options"


class MainMenuScene(Scene):
    """Main menu - eerste scene bij opstarten van de game."""

    def __init__(
        self,
        manager: SceneManager,
        game_instance: Any = None,
    ) -> None:
        """Initialize main menu.

        Parameters
        ----------
        manager : SceneManager
            Scene manager reference
        game_instance : Any, optional
            Reference to Game instance for system access
        """
        super().__init__(manager)
        self._game = game_instance
        self._state = MainMenuState.MAIN
        self._selected_index = 0
        self._selected_slot = 0

        # Feedback message
        self._feedback_message: str = ""
        self._feedback_timer: float = 0.0

        # Screen setup
        screen = pygame.display.get_surface()
        if screen:
            self._screen_width, self._screen_height = screen.get_size()
        else:
            self._screen_width, self._screen_height = 1280, 720

        # Fonts
        pygame.font.init()
        self._font_title = pygame.font.SysFont("monospace", 48, bold=True)
        self._font_menu = pygame.font.SysFont("monospace", 24)
        self._font_info = pygame.font.SysFont("monospace", 16)

        # Colors
        self._bg_color = (15, 15, 25)
        self._text_color = (220, 220, 220)
        self._highlight_color = (255, 220, 100)
        self._title_color = (255, 200, 150)

        # Main menu options
        self._main_options = [
            ("Nieuw spel", MainMenuOption.NEW_GAME),
            ("Doorgaan", MainMenuOption.CONTINUE),
            ("Load spel", MainMenuOption.LOAD_GAME),
            ("Opties", MainMenuOption.OPTIONS),
            ("Afsluiten", MainMenuOption.QUIT),
        ]

        logger.info("MainMenuScene initialized")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Parameters
        ----------
        event : pygame.event.Event
            Pygame event
        """
        if event.type == pygame.KEYDOWN:
            if self._state == MainMenuState.MAIN:
                self._handle_main_menu_input(event.key)
            elif self._state == MainMenuState.LOAD_SELECT:
                self._handle_load_select_input(event.key)
            elif self._state == MainMenuState.OPTIONS:
                self._handle_options_input(event.key)

    def _handle_main_menu_input(self, key: int) -> None:
        """Handle main menu navigation.

        Parameters
        ----------
        key : int
            Pygame key constant
        """
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            self._selected_index = (self._selected_index - 1) % len(self._main_options)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._selected_index = (self._selected_index + 1) % len(self._main_options)

        # Selection
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            self._execute_main_menu_option()

    def _execute_main_menu_option(self) -> None:
        """Execute selected main menu option."""
        _, option = self._main_options[self._selected_index]

        if option == MainMenuOption.NEW_GAME:
            self._start_new_game()
        elif option == MainMenuOption.CONTINUE:
            self._continue_game()
        elif option == MainMenuOption.LOAD_GAME:
            self._state = MainMenuState.LOAD_SELECT
            self._selected_slot = 0
        elif option == MainMenuOption.OPTIONS:
            self._state = MainMenuState.OPTIONS
        elif option == MainMenuOption.QUIT:
            self._quit_game()

    def _start_new_game(self) -> None:
        """Start a new game with fresh state."""
        logger.info("Starting new game...")

        if not self._game:
            logger.error("No game instance available")
            self._show_feedback("Error: Game niet beschikbaar", 3.0)
            return

        # Initialize fresh game state via game instance
        # The game instance will handle system initialization
        try:
            # Start overworld scene
            self._game.start_new_game()
            logger.info("✓ New game started successfully")
        except Exception as e:
            logger.error(f"Failed to start new game: {e}")
            self._show_feedback(f"Error: {e}", 3.0)

    def _continue_game(self) -> None:
        """Continue from last save (slot 1 default)."""
        logger.info("Continuing game...")

        if not self._game:
            logger.error("No game instance available")
            self._show_feedback("Error: Game niet beschikbaar", 3.0)
            return

        # Try to load slot 1
        slot_id = 1
        success = self._game.load_game(slot_id)

        if success:
            logger.info(f"✓ Game loaded from slot {slot_id}")
            # Switch to overworld
            self._game.start_overworld()
        else:
            logger.warning(f"No save found in slot {slot_id}")
            self._show_feedback("Geen save gevonden", 2.0)

    def _handle_load_select_input(self, key: int) -> None:
        """Handle load slot selection.

        Parameters
        ----------
        key : int
            Pygame key constant
        """
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            self._selected_slot = (self._selected_slot - 1) % 5
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._selected_slot = (self._selected_slot + 1) % 5

        # Selection
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            self._load_from_slot(self._selected_slot + 1)

        # Cancel
        elif key in (pygame.K_ESCAPE, pygame.K_x):
            self._state = MainMenuState.MAIN

    def _load_from_slot(self, slot_id: int) -> None:
        """Load game from specified slot.

        Parameters
        ----------
        slot_id : int
            Save slot number (1-5)
        """
        if not self._game:
            logger.error("No game instance available")
            self._show_feedback("Error: Game niet beschikbaar", 3.0)
            return

        logger.info(f"Loading from slot {slot_id}...")
        success = self._game.load_game(slot_id)

        if success:
            logger.info(f"✓ Game loaded from slot {slot_id}")
            # Switch to overworld
            self._game.start_overworld()
        else:
            logger.warning(f"Failed to load from slot {slot_id}")
            self._show_feedback(f"Slot {slot_id}: Load mislukt", 2.0)

    def _handle_options_input(self, key: int) -> None:
        """Handle options menu input.

        Parameters
        ----------
        key : int
            Pygame key constant
        """
        # Back to main menu
        if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_x):
            self._state = MainMenuState.MAIN

    def _quit_game(self) -> None:
        """Quit the game."""
        logger.info("Quitting game...")
        if self._game:
            self._game.stop()

    def _show_feedback(self, message: str, duration: float) -> None:
        """Show feedback message.

        Parameters
        ----------
        message : str
            Message to display
        duration : float
            Duration in seconds
        """
        self._feedback_message = message
        self._feedback_timer = duration

    def update(self, dt: float) -> None:
        """Update menu state.

        Parameters
        ----------
        dt : float
            Delta time in seconds
        """
        # Update feedback timer
        if self._feedback_timer > 0:
            self._feedback_timer -= dt

    def render(self, surface: pygame.Surface) -> None:
        """Render main menu.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        # Clear background
        surface.fill(self._bg_color)

        if self._state == MainMenuState.MAIN:
            self._render_main_menu(surface)
        elif self._state == MainMenuState.LOAD_SELECT:
            self._render_load_select(surface)
        elif self._state == MainMenuState.OPTIONS:
            self._render_options(surface)

        # Render feedback message
        if self._feedback_timer > 0:
            self._render_feedback(surface)

    def _render_main_menu(self, surface: pygame.Surface) -> None:
        """Render main menu options.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        # Title
        title_text = self._font_title.render("Tri-Śarīra RPG", True, self._title_color)
        title_rect = title_text.get_rect(center=(self._screen_width // 2, 150))
        surface.blit(title_text, title_rect)

        # Menu options
        start_y = 300
        for i, (text, _) in enumerate(self._main_options):
            color = self._highlight_color if i == self._selected_index else self._text_color
            prefix = "► " if i == self._selected_index else "  "
            option_text = self._font_menu.render(f"{prefix}{text}", True, color)
            option_rect = option_text.get_rect(center=(self._screen_width // 2, start_y + i * 50))
            surface.blit(option_text, option_rect)

    def _render_load_select(self, surface: pygame.Surface) -> None:
        """Render load slot selection.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        # Title
        title_text = self._font_title.render("Load Spel", True, self._title_color)
        title_rect = title_text.get_rect(center=(self._screen_width // 2, 100))
        surface.blit(title_text, title_rect)

        # Instructions
        info_text = self._font_info.render("Selecteer een save slot (Esc om terug te gaan)", True, self._text_color)
        info_rect = info_text.get_rect(center=(self._screen_width // 2, 150))
        surface.blit(info_text, info_rect)

        # Save slots
        start_y = 220
        for i in range(5):
            slot_id = i + 1
            color = self._highlight_color if i == self._selected_slot else self._text_color
            prefix = "► " if i == self._selected_slot else "  "

            # Check if slot exists and get info
            slot_info = self._get_slot_info(slot_id)
            slot_text = f"{prefix}Slot {slot_id}: {slot_info}"

            text_surface = self._font_menu.render(slot_text, True, color)
            text_rect = text_surface.get_rect(center=(self._screen_width // 2, start_y + i * 50))
            surface.blit(text_surface, text_rect)

    def _get_slot_info(self, slot_id: int) -> str:
        """Get info about a save slot.

        Parameters
        ----------
        slot_id : int
            Save slot number

        Returns
        -------
        str
            Slot info string
        """
        if not self._game:
            return "[Leeg]"

        # Check if slot exists via SaveSystem
        save_system: SaveSystem | None = getattr(self._game, "_save_system", None)
        if not save_system:
            return "[Leeg]"

        if save_system.slot_exists(slot_id):
            # Try to load slot data for preview
            save_data = save_system.load_from_file(slot_id)
            if save_data:
                # Extract some info
                world_state = save_data.get("world_state", {})
                time_state = save_data.get("time_state", {})
                zone_id = world_state.get("current_zone_id", "Unknown")
                dag = time_state.get("dag", 0)

                # Simplify zone name
                zone_name = zone_id.split("_")[-1] if zone_id else "Unknown"
                return f"Dag {dag} - {zone_name}"

        return "[Leeg]"

    def _render_options(self, surface: pygame.Surface) -> None:
        """Render options menu (stub for v0).

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        # Title
        title_text = self._font_title.render("Opties", True, self._title_color)
        title_rect = title_text.get_rect(center=(self._screen_width // 2, 200))
        surface.blit(title_text, title_rect)

        # Stub message
        stub_text = self._font_menu.render("Opties zijn nog niet beschikbaar", True, self._text_color)
        stub_rect = stub_text.get_rect(center=(self._screen_width // 2, 300))
        surface.blit(stub_text, stub_rect)

        # Instructions
        info_text = self._font_info.render("Druk op Esc of Enter om terug te gaan", True, self._text_color)
        info_rect = info_text.get_rect(center=(self._screen_width // 2, 350))
        surface.blit(info_text, info_rect)

    def _render_feedback(self, surface: pygame.Surface) -> None:
        """Render feedback message.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        if not self._feedback_message:
            return

        feedback_text = self._font_info.render(self._feedback_message, True, (255, 100, 100))
        feedback_rect = feedback_text.get_rect(center=(self._screen_width // 2, self._screen_height - 50))
        surface.blit(feedback_text, feedback_rect)


__all__ = ["MainMenuScene"]
