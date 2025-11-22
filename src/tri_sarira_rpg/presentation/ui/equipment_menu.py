"""Equipment Menu UI component."""

from __future__ import annotations

import logging
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
    from tri_sarira_rpg.services.game_data import GameDataService
    from tri_sarira_rpg.systems.equipment import EquipmentSystem
    from tri_sarira_rpg.systems.party import PartyMember

logger = logging.getLogger(__name__)


class EquipmentMenuUI(Widget):
    """Equipment menu overlay voor equippen/unequippen van gear."""

    def __init__(
        self,
        rect: pygame.Rect,
        equipment_system: EquipmentSystem,
        data_service: GameDataService,
        actor_id: str,
        party_member: PartyMember,
    ) -> None:
        """Initialize equipment menu.

        Parameters
        ----------
        rect : pygame.Rect
            Menu rectangle (position and size)
        equipment_system : EquipmentSystem
            Equipment system reference
        data_service : GameDataService
            Data service for item display info
        actor_id : str
            Actor ID to manage equipment for
        party_member : PartyMember
            Party member reference
        """
        super().__init__(rect)
        self._equipment = equipment_system
        self._data_service = data_service
        self._actor_id = actor_id
        self._member = party_member

        # UI state
        self._mode = "slot_select"  # "slot_select" or "item_select"
        self._selected_slot_index = 0
        self._selected_item_index = 0
        self._slots = ["weapon", "body", "accessory1"]
        self._available_items: list[str] = []
        self._feedback_message: str = ""
        self._feedback_timer: float = 0.0

        # Fonts (via cache)
        self._font_title = FontCache.get(FontSizes.TITLE, bold=True)
        self._font_header = FontCache.get(FontSizes.MEDIUM, bold=True)
        self._font_item = FontCache.get(FontSizes.NORMAL)
        self._font_desc = FontCache.get(FontSizes.SMALL)
        self._font_small = FontCache.get(FontSizes.TINY)

        # Colors (via MenuColors + equipment-specific)
        self._colors = MenuColors()
        self._stat_color = Colors.STAT_BONUS

        logger.debug(f"EquipmentMenuUI initialized for {actor_id}")

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle keyboard input.

        Parameters
        ----------
        event : pygame.event.Event
            Pygame event

        Returns
        -------
        bool
            True if menu should close, False otherwise
        """
        if event.type != pygame.KEYDOWN:
            return False

        # Close menu (ESC or X)
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            logger.debug("Closing equipment menu")
            return True

        if self._mode == "slot_select":
            return self._handle_slot_select(event)
        elif self._mode == "item_select":
            return self._handle_item_select(event)

        return False

    def _handle_slot_select(self, event: pygame.event.Event) -> bool:
        """Handle input in slot selection mode."""
        # Navigation (Up/Down or W/S)
        if event.key in (pygame.K_UP, pygame.K_w):
            self._selected_slot_index = (self._selected_slot_index - 1) % len(self._slots)
            return False

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._selected_slot_index = (self._selected_slot_index + 1) % len(self._slots)
            return False

        # Select slot (Enter/Space/Z) - open item selection
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            slot = self._slots[self._selected_slot_index]
            self._available_items = self._equipment.get_available_gear_for_slot(slot)

            # Add "Unequip" option if something is equipped
            equipped_gear = self._equipment.get_all_equipped_gear(self._actor_id)
            if equipped_gear.get(slot):
                self._available_items.insert(0, "<UNEQUIP>")

            if self._available_items:
                self._mode = "item_select"
                self._selected_item_index = 0
            else:
                self._show_feedback("No items available for this slot", is_error=True)

            return False

        return False

    def _handle_item_select(self, event: pygame.event.Event) -> bool:
        """Handle input in item selection mode."""
        # Cancel item selection (ESC or X) - back to slot select
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            self._mode = "slot_select"
            return False

        # Navigation (Up/Down or W/S)
        if event.key in (pygame.K_UP, pygame.K_w):
            if self._available_items:
                self._selected_item_index = (self._selected_item_index - 1) % len(
                    self._available_items
                )
            return False

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            if self._available_items:
                self._selected_item_index = (self._selected_item_index + 1) % len(
                    self._available_items
                )
            return False

        # Equip/unequip item (Enter/Space/Z)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            if self._available_items:
                item_choice = self._available_items[self._selected_item_index]
                slot = self._slots[self._selected_slot_index]

                if item_choice == "<UNEQUIP>":
                    # Unequip
                    result = self._equipment.unequip_gear(self._actor_id, slot)
                    if result.success:
                        self._show_feedback("Unequipped successfully", is_error=False)
                        self._mode = "slot_select"
                    else:
                        self._show_feedback(f"Failed: {result.reason}", is_error=True)
                else:
                    # Equip
                    result = self._equipment.equip_gear(self._actor_id, item_choice, slot)
                    if result.success:
                        self._show_feedback("Equipped successfully", is_error=False)
                        self._mode = "slot_select"
                    else:
                        self._show_feedback(f"Failed: {result.reason}", is_error=True)

            return False

        return False

    def _show_feedback(self, message: str, is_error: bool) -> None:
        """Show feedback message."""
        self._feedback_message = message
        self._feedback_timer = Timing.FEEDBACK_DURATION
        if is_error:
            logger.warning(f"Equipment menu feedback: {message}")
        else:
            logger.info(f"Equipment menu feedback: {message}")

    def update(self, dt: float) -> None:
        """Update UI state (e.g., feedback timer).

        Parameters
        ----------
        dt : float
            Delta time in seconds
        """
        if self._feedback_timer > 0:
            self._feedback_timer -= dt

    def render(self, surface: pygame.Surface) -> None:
        """Render equipment menu.

        Parameters
        ----------
        surface : pygame.Surface
            Surface to render to
        """
        # Background
        bg_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_surface.fill(self._colors.bg)
        surface.blit(bg_surface, self.rect.topleft)

        # Border
        pygame.draw.rect(surface, self._colors.border, self.rect, 2)

        # Title
        title = f"Equipment - {self._member.actor_id}"
        title_surf = self._font_title.render(title, True, self._colors.title)
        title_x = self.rect.x + (self.rect.width - title_surf.get_width()) // 2
        surface.blit(title_surf, (title_x, self.rect.y + Spacing.SM))

        # Mode-specific rendering
        if self._mode == "slot_select":
            self._render_slot_select(surface)
        elif self._mode == "item_select":
            self._render_item_select(surface)

        # Feedback message
        if self._feedback_timer > 0:
            color = self._colors.error if "Failed" in self._feedback_message else self._colors.success
            feedback_surf = self._font_header.render(self._feedback_message, True, color)
            feedback_x = self.rect.x + (self.rect.width - feedback_surf.get_width()) // 2
            surface.blit(feedback_surf, (feedback_x, self.rect.y + self.rect.height - 50))

        # Controls help
        controls = "ESC/X: Close | Arrow/WASD: Navigate | Enter/Z: Select"
        if self._mode == "item_select":
            controls = "ESC/X: Back | Arrow/WASD: Navigate | Enter/Z: Equip"
        controls_surf = self._font_small.render(controls, True, self._colors.text)
        controls_x = self.rect.x + (self.rect.width - controls_surf.get_width()) // 2
        surface.blit(controls_surf, (controls_x, self.rect.y + self.rect.height - Spacing.XL))

    def _render_slot_select(self, surface: pygame.Surface) -> None:
        """Render slot selection mode."""
        y_offset = self.rect.y + 60

        # Slot list
        header_surf = self._font_header.render("Equipment Slots:", True, self._colors.title)
        surface.blit(header_surf, (self.rect.x + Spacing.LG, y_offset))
        y_offset += Spacing.XXL

        equipped_gear = self._equipment.get_all_equipped_gear(self._actor_id)

        for i, slot in enumerate(self._slots):
            # Slot name
            slot_display = {
                "weapon": "Weapon",
                "body": "Body Armor",
                "accessory1": "Accessory",
            }
            slot_name = slot_display.get(slot, slot)

            # Get equipped item
            equipped_id = equipped_gear.get(slot)
            equipped_name = "< Empty >"
            item_info = None
            if equipped_id:
                item_info = self._data_service.get_item_info(equipped_id)
                if item_info:
                    equipped_name = item_info.name

            # Highlight selected
            is_selected = (i == self._selected_slot_index)
            color = self._colors.highlight if is_selected else self._colors.text

            # Render slot
            slot_text = f"{slot_name}: {equipped_name}"
            slot_surf = self._font_item.render(slot_text, True, color)
            x_pos = self.rect.x + Spacing.XXXL if is_selected else self.rect.x + 50
            surface.blit(slot_surf, (x_pos, y_offset))

            # Show stat mods if equipped
            if item_info and is_selected and item_info.stat_summary:
                stats_surf = self._font_desc.render(f"  [{item_info.stat_summary}]", True, self._stat_color)
                surface.blit(stats_surf, (self.rect.x + 60, y_offset + Spacing.LG))
                y_offset += Spacing.LG

            y_offset += Spacing.XXXL

        # Show total stats on right side
        self._render_stats_panel(surface)

    def _render_item_select(self, surface: pygame.Surface) -> None:
        """Render item selection mode."""
        y_offset = self.rect.y + 60

        # Header
        slot = self._slots[self._selected_slot_index]
        slot_display = {
            "weapon": "Weapon",
            "body": "Body Armor",
            "accessory1": "Accessory",
        }
        header = f"Select {slot_display.get(slot, slot)}:"
        header_surf = self._font_header.render(header, True, self._colors.title)
        surface.blit(header_surf, (self.rect.x + Spacing.LG, y_offset))
        y_offset += Spacing.XXL

        # Item list
        if not self._available_items:
            no_items_surf = self._font_item.render("No items available", True, self._colors.text)
            surface.blit(no_items_surf, (self.rect.x + Spacing.XXXL, y_offset))
        else:
            for i, item_id in enumerate(self._available_items):
                is_selected = (i == self._selected_item_index)
                color = self._colors.highlight if is_selected else self._colors.text

                # Get item name
                if item_id == "<UNEQUIP>":
                    item_name = "< Unequip Current >"
                    item_info = None
                else:
                    item_info = self._data_service.get_item_info(item_id)
                    item_name = item_info.name if item_info else item_id

                # Render item
                item_surf = self._font_item.render(item_name, True, color)
                x_pos = self.rect.x + Spacing.XXXL if is_selected else self.rect.x + 50
                surface.blit(item_surf, (x_pos, y_offset))

                # Show stat mods for selected item
                if is_selected and item_info and item_info.stat_summary:
                    stats_surf = self._font_desc.render(
                        f"  [{item_info.stat_summary}]", True, self._stat_color
                    )
                    surface.blit(stats_surf, (self.rect.x + 60, y_offset + Spacing.LG))
                    y_offset += Spacing.LG

                y_offset += Spacing.XXXL

    def _render_stats_panel(self, surface: pygame.Surface) -> None:
        """Render stats summary panel on the right side."""
        panel_x = self.rect.x + self.rect.width - 250
        panel_y = self.rect.y + 60

        # Header
        header_surf = self._font_header.render("Stats:", True, self._colors.title)
        surface.blit(header_surf, (panel_x, panel_y))
        panel_y += Spacing.XL

        # Get effective stats
        effective_stats = self._equipment.get_effective_stats(self._actor_id)

        # Show key stats
        key_stats = ["STR", "END", "DEF", "SPD", "FOC", "MAG", "RES"]
        for stat_name in key_stats:
            base_value = self._member.base_stats.get(stat_name, 0)
            effective_value = effective_stats.get(stat_name, 0)
            bonus = effective_value - base_value

            if bonus > 0:
                stat_text = f"{stat_name}: {effective_value} (+{bonus})"
                color = self._stat_color
            else:
                stat_text = f"{stat_name}: {effective_value}"
                color = self._colors.text

            stat_surf = self._font_desc.render(stat_text, True, color)
            surface.blit(stat_surf, (panel_x, panel_y))
            panel_y += Spacing.MEDIUM


__all__ = ["EquipmentMenuUI"]
