"""Simple inventory system for Combat v0."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InventoryState:
    """Simpele inventory state voor v0 (item_id -> quantity)."""

    items: dict[str, int] = field(default_factory=dict)

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        """Voeg items toe aan inventory."""
        if item_id not in self.items:
            self.items[item_id] = 0
        self.items[item_id] += quantity
        logger.debug(f"Added {quantity}x {item_id} to inventory (total: {self.items[item_id]})")

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Verwijder items uit inventory.

        Returns
        -------
        bool
            True als succesvol, False als niet genoeg items
        """
        if item_id not in self.items or self.items[item_id] < quantity:
            logger.warning(f"Cannot remove {quantity}x {item_id}: insufficient quantity")
            return False

        self.items[item_id] -= quantity
        if self.items[item_id] <= 0:
            del self.items[item_id]
        logger.debug(f"Removed {quantity}x {item_id} from inventory")
        return True

    def get_quantity(self, item_id: str) -> int:
        """Haal het aantal van een item op."""
        return self.items.get(item_id, 0)

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check of er genoeg van een item is."""
        return self.get_quantity(item_id) >= quantity

    def get_all_items(self) -> dict[str, int]:
        """Haal alle items op (item_id -> quantity)."""
        return self.items.copy()

    def get_available_items(self) -> list[str]:
        """Haal alle item IDs met quantity > 0 op."""
        return [item_id for item_id, qty in self.items.items() if qty > 0]

    def iter_items(self) -> Iterable[tuple[str, int]]:
        """Itereer over alle items (item_id, quantity) pairs."""
        return iter(self.items.items())


class InventorySystem:
    """Beheert de inventory state (v0: simpele wrapper)."""

    def __init__(self) -> None:
        self._state = InventoryState()

    @property
    def state(self) -> InventoryState:
        """Geef toegang tot inventory state."""
        return self._state

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        """Voeg items toe."""
        self._state.add_item(item_id, quantity)

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Verwijder items."""
        return self._state.remove_item(item_id, quantity)

    def get_quantity(self, item_id: str) -> int:
        """Haal quantity op."""
        return self._state.get_quantity(item_id)

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check of item beschikbaar is."""
        return self._state.has_item(item_id, quantity)

    def get_all_items(self) -> dict[str, int]:
        """Haal alle items op."""
        return self._state.get_all_items()

    def get_available_items(self) -> list[str]:
        """Haal beschikbare item IDs op."""
        return self._state.get_available_items()

    def iter_items(self) -> Iterable[tuple[str, int]]:
        """Itereer over alle items (item_id, quantity) pairs."""
        return self._state.iter_items()

    def get_save_state(self) -> dict[str, int]:
        """Get serializable inventory state for saving.

        Returns
        -------
        dict[str, int]
            Inventory state as dict (item_id -> quantity)
        """
        return self._state.get_all_items()

    def restore_from_save(self, state_dict: dict[str, int]) -> None:
        """Restore inventory state from save data.

        Parameters
        ----------
        state_dict : dict[str, int]
            Inventory state dict from save file
        """
        # Clear current inventory
        self._state.items.clear()

        # Restore items
        for item_id, quantity in state_dict.items():
            if quantity > 0:
                self._state.items[item_id] = quantity

        logger.info(f"Inventory restored: {len(self._state.items)} item types")


__all__ = ["InventorySystem", "InventoryState"]
