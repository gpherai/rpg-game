"""Shop Menu UI component."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from .widgets import Widget

if TYPE_CHECKING:
    from tri_sarira_rpg.data_access.repository import DataRepository
    from tri_sarira_rpg.systems.inventory import InventorySystem
    from tri_sarira_rpg.systems.shop import ShopSystem

logger = logging.getLogger(__name__)


class ShopMenuUI(Widget):
    """Shop menu overlay voor buying items uit een shop."""

    def __init__(
        self,
        rect: pygame.Rect,
        shop_system: ShopSystem,
        inventory_system: InventorySystem,
        data_repository: DataRepository,
        shop_id: str,
        chapter_id: int = 1,
    ) -> None:
        """Initialize shop menu.

        Parameters
        ----------
        rect : pygame.Rect
            Menu rectangle (position and size)
        shop_system : ShopSystem
            Shop system reference for transactions
        inventory_system : InventorySystem
            Inventory system reference
        data_repository : DataRepository
            Data repository for item info
        shop_id : str
            Shop ID to display (e.g., "shop_r1_town_general")
        chapter_id : int
            Current chapter for filtering items (default 1)
        """
        super().__init__(rect)
        self._shop = shop_system
        self._inventory = inventory_system
        self._repository = data_repository
        self._shop_id = shop_id
        self._chapter_id = chapter_id

        # UI state
        self._selected_index = 0
        self._feedback_message: str = ""
        self._feedback_timer: float = 0.0

        # Load shop data
        self._shop_def = self._shop.get_shop_definition(shop_id)
        self._available_items = []
        if self._shop_def:
            self._available_items = self._shop.get_available_items(shop_id, chapter_id=chapter_id)

        # Fonts
        pygame.font.init()
        self._font_title = pygame.font.SysFont("monospace", 28, bold=True)
        self._font_header = pygame.font.SysFont("monospace", 18, bold=True)
        self._font_item = pygame.font.SysFont("monospace", 16)
        self._font_desc = pygame.font.SysFont("monospace", 14)
        self._font_small = pygame.font.SysFont("monospace", 12)

        # Colors
        self._bg_color = (20, 20, 40, 240)  # Semi-transparent dark blue
        self._border_color = (100, 150, 200)
        self._text_color = (220, 220, 220)
        self._highlight_color = (255, 220, 100)
        self._title_color = (255, 200, 150)
        self._currency_color = (255, 220, 50)
        self._price_color = (150, 255, 150)
        self._error_color = (255, 100, 100)
        self._success_color = (100, 255, 100)

        logger.debug(f"ShopMenuUI initialized for {shop_id}")

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle keyboard input.

        Parameters
        ----------
        event : pygame.event.Event
            Pygame event

        Returns
        -------
        bool
            True if shop should close, False otherwise
        """
        if event.type != pygame.KEYDOWN:
            return False

        # Close shop (Esc or X)
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            logger.debug("Closing shop menu")
            return True

        # Navigation (Up/Down or W/S)
        if event.key in (pygame.K_UP, pygame.K_w):
            if self._available_items:
                self._selected_index = (self._selected_index - 1) % len(self._available_items)
            return False

        elif event.key in (pygame.K_DOWN, pygame.K_s):
            if self._available_items:
                self._selected_index = (self._selected_index + 1) % len(self._available_items)
            return False

        # Buy item (Enter/Space/Z)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            self._buy_selected_item()
            return False

        return False

    def update(self, dt: float) -> None:
        """Update shop menu (for feedback timer)."""
        if self._feedback_timer > 0:
            self._feedback_timer -= dt

    def draw(self, surface: pygame.Surface) -> None:
        """Render shop menu."""
        # Create semi-transparent background
        bg_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        pygame.draw.rect(bg_surface, self._bg_color, bg_rect)
        pygame.draw.rect(bg_surface, self._border_color, bg_rect, 3)
        surface.blit(bg_surface, self.rect.topleft)

        # Title (shop name)
        y_offset = self.rect.top + 20
        shop_name = self._shop_def.name if self._shop_def else "Shop"
        title_surf = self._font_title.render(shop_name, True, self._title_color)
        title_x = self.rect.left + (self.rect.width - title_surf.get_width()) // 2
        surface.blit(title_surf, (title_x, y_offset))
        y_offset += 45

        # Currency display
        currency = self._shop.get_currency()
        currency_text = f"Rūpa: {currency}"
        currency_surf = self._font_header.render(currency_text, True, self._currency_color)
        surface.blit(currency_surf, (self.rect.left + 30, y_offset))
        y_offset += 35

        # Divider line
        pygame.draw.line(
            surface,
            self._border_color,
            (self.rect.left + 20, y_offset),
            (self.rect.right - 20, y_offset),
            2,
        )
        y_offset += 20

        # Items list (left side) and details (right side)
        if not self._available_items:
            # No items available
            no_items_surf = self._font_item.render("Geen items beschikbaar", True, self._text_color)
            surface.blit(no_items_surf, (self.rect.left + 30, y_offset))
        else:
            # Split into two columns: item list (left) and details (right)
            list_x = self.rect.left + 30
            details_x = self.rect.left + self.rect.width // 2 + 10
            details_width = self.rect.width // 2 - 40

            # Draw items list
            items_y = y_offset
            for i, entry in enumerate(self._available_items):
                is_selected = i == self._selected_index
                color = self._highlight_color if is_selected else self._text_color

                # Item name and price
                item_text = f"{entry.item_id.replace('item_', '').replace('_', ' ').title()}"
                price_text = f"{entry.base_price} Rūpa"

                # Prefix for selected item
                prefix = "> " if is_selected else "  "
                full_text = f"{prefix}{item_text}"

                item_surf = self._font_item.render(full_text, True, color)
                surface.blit(item_surf, (list_x, items_y))

                # Price on the right side of item name
                price_surf = self._font_small.render(price_text, True, self._price_color)
                surface.blit(price_surf, (list_x + 220, items_y + 2))

                items_y += 25

            # Draw selected item details (right side)
            selected_entry = self._available_items[self._selected_index]
            details_y = y_offset

            # Item name (header)
            item_name = selected_entry.item_id.replace("item_", "").replace("_", " ").title()
            name_surf = self._font_header.render(item_name, True, self._highlight_color)
            surface.blit(name_surf, (details_x, details_y))
            details_y += 30

            # Get item data from repository
            item_data = self._repository.get_item(selected_entry.item_id)
            if item_data:
                # Type
                item_type = item_data.get("type", "unknown")
                type_surf = self._font_desc.render(f"Type: {item_type}", True, self._text_color)
                surface.blit(type_surf, (details_x, details_y))
                details_y += 20

                # Description (wrapped)
                desc = item_data.get("description", "Geen beschrijving")
                wrapped_lines = self._wrap_text(desc, details_width)
                for line in wrapped_lines:
                    line_surf = self._font_desc.render(line, True, self._text_color)
                    surface.blit(line_surf, (details_x, details_y))
                    details_y += 18

                details_y += 10

                # Current inventory count
                inv_count = self._inventory.get_quantity(selected_entry.item_id)
                inv_surf = self._font_desc.render(f"In bezit: {inv_count}", True, self._text_color)
                surface.blit(inv_surf, (details_x, details_y))
                details_y += 25

            # Price (large, emphasized)
            price_text = f"Prijs: {selected_entry.base_price} Rūpa"
            price_surf = self._font_header.render(price_text, True, self._price_color)
            surface.blit(price_surf, (details_x, details_y))

        # Feedback message (bottom center)
        if self._feedback_timer > 0:
            feedback_y = self.rect.bottom - 80
            feedback_surf = self._font_item.render(
                self._feedback_message, True, self._success_color
            )
            feedback_x = self.rect.left + (self.rect.width - feedback_surf.get_width()) // 2
            surface.blit(feedback_surf, (feedback_x, feedback_y))

        # Controls hint (bottom)
        controls_y = self.rect.bottom - 50
        controls_text = "↑/↓: Navigeren | Enter/Z: Kopen | Esc/X: Sluiten"
        controls_surf = self._font_small.render(controls_text, True, self._text_color)
        controls_x = self.rect.left + (self.rect.width - controls_surf.get_width()) // 2
        surface.blit(controls_surf, (controls_x, controls_y))

    def _buy_selected_item(self) -> None:
        """Buy the currently selected item."""
        if not self._available_items:
            return

        selected_entry = self._available_items[self._selected_index]
        item_id = selected_entry.item_id
        item_name = item_id.replace("item_", "").replace("_", " ").title()

        logger.info(f"Attempting to buy {item_id}...")

        # Execute buy transaction
        result = self._shop.buy_item(self._shop_id, item_id, quantity=1)

        if result.success:
            self._feedback_message = (
                f"Gekocht: 1x {item_name} voor {selected_entry.base_price} Rūpa"
            )
            self._feedback_timer = 2.5
            logger.info(f"Purchase successful: {item_id}")
        else:
            # Handle errors
            if result.reason == "INSUFFICIENT_FUNDS":
                self._feedback_message = "Niet genoeg Rūpa!"
            elif result.reason == "NOT_AVAILABLE":
                self._feedback_message = "Item niet beschikbaar"
            elif result.reason == "SHOP_NOT_FOUND":
                self._feedback_message = "Shop niet gevonden"
            else:
                self._feedback_message = f"Fout: {result.reason}"

            self._feedback_timer = 2.0
            logger.warning(f"Purchase failed: {result.reason}")

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width pixels.

        Parameters
        ----------
        text : str
            Text to wrap
        max_width : int
            Maximum width in pixels

        Returns
        -------
        list[str]
            List of wrapped text lines
        """
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_surf = self._font_desc.render(test_line, True, (255, 255, 255))

            if test_surf.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines


__all__ = ["ShopMenuUI"]
