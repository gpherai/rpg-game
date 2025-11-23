"""Pause Menu UI component."""

from __future__ import annotations

import logging
from enum import Enum
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from tri_sarira_rpg.presentation.theme import (
    Colors,
    FontCache,
    FontSizes,
    MenuColors,
    Spacing,
    Timing,
)

from .widgets import Widget

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import GameProtocol, SaveSlotMeta

logger = logging.getLogger(__name__)


class PauseMenuOption(Enum):
    """Pause menu options."""

    RESUME = 0
    SAVE = 1
    LOAD = 2
    MAIN_MENU = 3
    QUIT = 4


class PauseMenuState(Enum):
    """States for the pause menu."""

    MAIN = "main"
    LOAD_SELECT = "load_select"
    SAVE_SELECT = "save_select"
    CONFIRM = "confirm"


class PauseMenu(Widget):
    """Pause menu overlay for gameplay scenes."""

    def __init__(
        self,
        rect: pygame.Rect,
        game_instance: GameProtocol | None = None,
        allow_load: bool = True,
    ) -> None:
        """Initialize pause menu.

        Parameters
        ----------
        rect : pygame.Rect
            Menu rectangle (position and size)
        game_instance : GameProtocol | None, optional
            Reference to Game instance for save/load
        allow_load : bool
            Whether to allow loading during gameplay (default True)
        """
        super().__init__(rect)
        self._game = game_instance
        self._allow_load = allow_load
        self._state = PauseMenuState.MAIN
        self._selected_index = 0
        self._selected_slot = 0

        # Callback for returning to main menu
        self._on_main_menu_callback: Callable[[], None] | None = None

        # Feedback message
        self._feedback_message: str = ""
        self._feedback_timer: float = 0.0

        # Cache for slot info to avoid loading save files every frame
        self._slot_info_cache: dict[int, str] = {}
        self._cache_valid: bool = False

        # Fonts (via cache)
        self._font_title = FontCache.get(FontSizes.SUBTITLE, bold=True)
        self._font_menu = FontCache.get(FontSizes.LARGE)
        self._font_info = FontCache.get(FontSizes.SMALL)

        # Colors (via MenuColors scheme)
        self._colors = MenuColors()

        # Main menu options
        self._main_options = [
            ("Resume", PauseMenuOption.RESUME),
            ("Save Game", PauseMenuOption.SAVE),
            ("Load Game", PauseMenuOption.LOAD),
            ("Main Menu", PauseMenuOption.MAIN_MENU),
            ("Quit Game", PauseMenuOption.QUIT),
        ]

        logger.debug("PauseMenu initialized")

    def set_main_menu_callback(self, callback: Any) -> None:
        """Set callback for returning to main menu.

        Parameters
        ----------
        callback : callable
            Callback to execute when user selects main menu
        """
        self._on_main_menu_callback = callback

    def handle_input(self, key: int) -> bool:
        """Handle keyboard input.

        Parameters
        ----------
        key : int
            Pygame key constant

        Returns
        -------
        bool
            True if menu should close (resume), False otherwise
        """
        if self._state == PauseMenuState.MAIN:
            return self._handle_main_menu_input(key)
        elif self._state == PauseMenuState.LOAD_SELECT:
            return self._handle_load_select_input(key)
        elif self._state == PauseMenuState.SAVE_SELECT:
            return self._handle_save_select_input(key)

        return False

    def _handle_main_menu_input(self, key: int) -> bool:
        """Handle main menu navigation.

        Parameters
        ----------
        key : int
            Pygame key constant

        Returns
        -------
        bool
            True if menu should close
        """
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            self._selected_index = (self._selected_index - 1) % len(self._main_options)
            return False

        elif key in (pygame.K_DOWN, pygame.K_s):
            self._selected_index = (self._selected_index + 1) % len(self._main_options)
            return False

        # Selection
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            return self._execute_main_menu_option()

        # Quick resume (Esc)
        elif key == pygame.K_ESCAPE:
            logger.debug("Resuming game (Esc)")
            return True

        return False

    def _execute_main_menu_option(self) -> bool:
        """Execute selected main menu option.

        Returns
        -------
        bool
            True if menu should close
        """
        _, option = self._main_options[self._selected_index]

        if option == PauseMenuOption.RESUME:
            logger.debug("Resuming game")
            return True

        elif option == PauseMenuOption.SAVE:
            # Open save slot selectie i.p.v. direct saven
            self._state = PauseMenuState.SAVE_SELECT
            self._selected_slot = 0
            self._cache_valid = False
            return False

        elif option == PauseMenuOption.LOAD:
            if self._allow_load:
                self._state = PauseMenuState.LOAD_SELECT
                self._selected_slot = 0
                # Invalidate cache when entering load menu
                self._cache_valid = False
            else:
                self._show_feedback("Loading not available during battle", 2.0)
            return False

        elif option == PauseMenuOption.MAIN_MENU:
            self._return_to_main_menu()
            return True  # Close pause menu

        elif option == PauseMenuOption.QUIT:
            self._quit_game()
            return True

        return False

    def _save_game(self) -> None:
        """Direct save helper (not used directly in UI)."""
        if not self._game:
            logger.error("No game instance available for save")
            self._show_feedback("Error: Cannot save", 2.0)
            return

        logger.info("Saving game from pause menu...")
        slot_id = 1
        success = self._game.save_game(slot_id)

        if success:
            self._show_feedback(f"Saved to slot {slot_id}", 2.0)
        else:
            self._show_feedback("Save failed", 2.0)

    def _handle_load_select_input(self, key: int) -> bool:
        """Handle load slot selection.

        Parameters
        ----------
        key : int
            Pygame key constant

        Returns
        -------
        bool
            True if menu should close
        """
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            self._selected_slot = (self._selected_slot - 1) % 5
            return False

        elif key in (pygame.K_DOWN, pygame.K_s):
            self._selected_slot = (self._selected_slot + 1) % 5
            return False

        # Selection
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            success = self._load_from_slot(self._selected_slot + 1)
            if success:
                return True  # Close menu after successful load
            return False

        # Cancel
        elif key in (pygame.K_ESCAPE, pygame.K_x):
            self._state = PauseMenuState.MAIN
            return False

        return False

    def _handle_save_select_input(self, key: int) -> bool:
        """Handle save slot selectie."""
        if key in (pygame.K_UP, pygame.K_w):
            self._selected_slot = (self._selected_slot - 1) % 5
            return False
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._selected_slot = (self._selected_slot + 1) % 5
            return False
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            return self._save_to_slot(self._selected_slot + 1)
        elif key in (pygame.K_ESCAPE, pygame.K_x):
            self._state = PauseMenuState.MAIN
            return False
        return False

    def _save_to_slot(self, slot_id: int) -> bool:
        """Save to the chosen slot."""
        if not self._game:
            logger.error("No game instance available for save")
            self._show_feedback("Error: Cannot save", 2.0)
            return False

        logger.info(f"Saving to slot {slot_id}...")
        success = self._game.save_game(slot_id)

        if success:
            self._show_feedback(f"Saved to slot {slot_id}", 2.0)
            self._state = PauseMenuState.MAIN
            # Cache verversen zodat previews up-to-date zijn
            self._cache_valid = False
            return True

        self._show_feedback("Save failed", 2.0)
        return False

    def _load_from_slot(self, slot_id: int) -> bool:
        """Load game from specified slot.

        Parameters
        ----------
        slot_id : int
            Save slot number (1-5)

        Returns
        -------
        bool
            True if load succeeded
        """
        if not self._game:
            logger.error("No game instance available for load")
            self._show_feedback("Error: Cannot load", 2.0)
            return False

        logger.info(f"Loading from slot {slot_id}...")
        success = self._game.load_game(slot_id)

        if success:
            self._show_feedback(f"Loaded from slot {slot_id}", 1.5)
            # Return to main state and close menu
            self._state = PauseMenuState.MAIN
            return True
        else:
            self._show_feedback(f"Slot {slot_id}: Load failed", 2.0)
            return False

    def _return_to_main_menu(self) -> None:
        """Return to main menu."""
        logger.info("Returning to main menu from pause menu...")

        if self._on_main_menu_callback:
            self._on_main_menu_callback()
        else:
            logger.warning("No main menu callback set")

    def _quit_game(self) -> None:
        """Quit the game."""
        logger.info("Quitting game from pause menu...")
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
        logger.debug(f"Feedback: {message}")

    def update(self, dt: float) -> None:
        """Update menu state.

        Parameters
        ----------
        dt : float
            Delta time in seconds
        """
        # Refresh slot cache when entering load menu (only once)
        if self._state == PauseMenuState.LOAD_SELECT and not self._cache_valid:
            self._refresh_slot_cache()
        if self._state == PauseMenuState.SAVE_SELECT and not self._cache_valid:
            self._refresh_slot_cache()

        # Update feedback timer
        if self._feedback_timer > 0:
            self._feedback_timer -= dt

    def render(self, surface: pygame.Surface) -> None:
        """Render pause menu overlay.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        # Create semi-transparent background
        overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        overlay.fill(self._colors.bg)

        # Draw border
        pygame.draw.rect(overlay, self._colors.border, overlay.get_rect(), 3)

        # Render current state
        if self._state == PauseMenuState.MAIN:
            self._render_main_menu(overlay)
        elif self._state == PauseMenuState.LOAD_SELECT:
            self._render_load_select(overlay)
        elif self._state == PauseMenuState.SAVE_SELECT:
            self._render_save_select(overlay)

        # Render feedback message
        if self._feedback_timer > 0:
            self._render_feedback(overlay)

        # Blit overlay to surface
        surface.blit(overlay, self.rect.topleft)

    def _render_main_menu(self, surface: pygame.Surface) -> None:
        """Render main pause menu.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        # Title
        title_text = self._font_title.render("PAUSED", True, self._colors.title)
        title_rect = title_text.get_rect(center=(self.rect.width // 2, 60))
        surface.blit(title_text, title_rect)

        # Menu options
        start_y = 140
        for i, (text, option) in enumerate(self._main_options):
            # Skip load option if not allowed
            if option == PauseMenuOption.LOAD and not self._allow_load:
                # Gray out the option
                color = Colors.TEXT_MUTED
                prefix = "  "
            else:
                color = self._colors.highlight if i == self._selected_index else self._colors.text
                prefix = "► " if i == self._selected_index else "  "

            option_text = self._font_menu.render(f"{prefix}{text}", True, color)
            option_rect = option_text.get_rect(center=(self.rect.width // 2, start_y + i * Spacing.XXXL))
            surface.blit(option_text, option_rect)

        # Instructions
        info_text = self._font_info.render("Press Esc to resume", True, self._colors.text)
        info_rect = info_text.get_rect(center=(self.rect.width // 2, self.rect.height - Spacing.XXL))
        surface.blit(info_text, info_rect)

    def _render_load_select(self, surface: pygame.Surface) -> None:
        """Render load slot selection.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        # Title
        title_text = self._font_title.render("Load Game", True, self._colors.title)
        title_rect = title_text.get_rect(center=(self.rect.width // 2, Spacing.XXXL))
        surface.blit(title_text, title_rect)

        # Instructions
        info_text = self._font_info.render(
            "Select a save slot (Esc to return)", True, self._colors.text
        )
        info_rect = info_text.get_rect(center=(self.rect.width // 2, 80))
        surface.blit(info_text, info_rect)

        # Save slots
        start_y = 130
        for i in range(5):
            slot_id = i + 1
            color = self._colors.highlight if i == self._selected_slot else self._colors.text
            prefix = "► " if i == self._selected_slot else "  "

            # Check if slot exists and get info
            slot_info = self._get_slot_info(slot_id)
            slot_text = f"{prefix}Slot {slot_id}: {slot_info}"

            text_surface = self._font_menu.render(slot_text, True, color)
            text_rect = text_surface.get_rect(center=(self.rect.width // 2, start_y + i * Spacing.XXXL))
            surface.blit(text_surface, text_rect)

    def _render_save_select(self, surface: pygame.Surface) -> None:
        """Render save slot selection."""
        title_text = self._font_title.render("Save Game", True, self._colors.title)
        title_rect = title_text.get_rect(center=(self.rect.width // 2, Spacing.XXXL))
        surface.blit(title_text, title_rect)

        info_text = self._font_info.render(
            "Choose a slot to save (Esc to return)", True, self._colors.text
        )
        info_rect = info_text.get_rect(center=(self.rect.width // 2, 80))
        surface.blit(info_text, info_rect)

        start_y = 130
        for i in range(5):
            slot_id = i + 1
            color = self._colors.highlight if i == self._selected_slot else self._colors.text
            prefix = "► " if i == self._selected_slot else "  "
            slot_info = self._get_slot_info(slot_id)
            slot_text = f"{prefix}Slot {slot_id}: {slot_info}"
            text_surface = self._font_menu.render(slot_text, True, color)
            text_rect = text_surface.get_rect(center=(self.rect.width // 2, start_y + i * Spacing.XXXL))
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
        # Use cached info if available
        if self._cache_valid and slot_id in self._slot_info_cache:
            return self._slot_info_cache[slot_id]

        # Load slot info
        info = "[Empty]"
        if self._game:
            try:
                metadata = self._game.get_save_metadata(slot_id)
                if metadata:
                    info = self._format_slot_preview(metadata)
            except Exception:
                info = "[Empty]"

        # Cache the result
        self._slot_info_cache[slot_id] = info
        return info

    def _format_slot_preview(self, metadata: "SaveSlotMeta | None") -> str:
        """Build preview text from metadata."""
        if not metadata:
            return "Unknown save"

        zone = metadata.get("zone_name") or metadata.get("zone_id") or "Unknown area"
        day_index = metadata.get("day_index")
        if isinstance(day_index, int):
            day_text = f"Day {day_index + 1}"
        else:
            day_text = "Day ?"

        time_of_day = metadata.get("time_of_day")
        if isinstance(time_of_day, int):
            hours = (time_of_day // 60) % 24
            minutes = time_of_day % 60
            time_text = f"{hours:02d}:{minutes:02d}"
        else:
            time_text = "??:??"

        return f"{day_text} – {zone} ({time_text})"

    def _refresh_slot_cache(self) -> None:
        """Refresh slot info cache for all 5 slots."""
        self._slot_info_cache.clear()
        for slot_id in range(1, 6):
            self._get_slot_info(slot_id)
        self._cache_valid = True

    def _render_feedback(self, surface: pygame.Surface) -> None:
        """Render feedback message.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render on
        """
        if not self._feedback_message:
            return

        feedback_text = self._font_info.render(self._feedback_message, True, self._colors.success)
        feedback_rect = feedback_text.get_rect(center=(self.rect.width // 2, self.rect.height - 60))
        surface.blit(feedback_text, feedback_rect)


__all__ = ["PauseMenu"]
