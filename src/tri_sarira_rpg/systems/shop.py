"""Shop System v0 - Backend voor shop-interacties (buy-only)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import (
        DataRepositoryProtocol,
        InventorySystemProtocol,
    )

logger = logging.getLogger(__name__)


@dataclass
class ShopInventoryEntry:
    """Definitie van een item in shop inventory."""

    item_id: str
    base_price: int
    stock_type: str = "INFINITE"  # INFINITE/LIMITED/PER-DAY/PER-FESTIVAL
    min_chapter: int = 1
    max_chapter: int = 99
    conditions: list[str] = field(default_factory=list)


@dataclass
class ShopDefinition:
    """Definitie van een shop uit shops.json."""

    shop_id: str
    zone_id: str
    name: str
    shop_type: str  # GENERAL/WEAPON_SMITH/CLOTHIER/HEALER/SPECIALTY/SERVICE
    inventory_entries: list[ShopInventoryEntry] = field(default_factory=list)


@dataclass
class ShopState:
    """Runtime state van een shop (voor later: stock tracking, refresh logic)."""

    shop_id: str
    inventory_overrides: dict[str, int] = field(default_factory=dict)  # item_id -> stock_left
    last_refresh_day_index: int = 0
    shop_flags: dict[str, bool] = field(default_factory=dict)


@dataclass
class BuyResult:
    """Resultaat van een buy-transactie."""

    success: bool
    reason: str  # "OK", "INSUFFICIENT_FUNDS", "NOT_AVAILABLE", "INVALID_ITEM", etc.
    new_currency_amount: int
    item_id: str | None = None
    quantity: int = 0


class ShopSystem:
    """Shop System v0 - Backend voor shop-interacties.

    V0 Beperkingen:
    - Buy-only (geen sell)
    - Infinite stock effectief (stock_type niet functioneel gebruikt)
    - Geen tijd/festival refresh logic
    - Geen quest/flag-based conditions evaluatie
    """

    def __init__(
        self,
        data_repository: DataRepositoryProtocol,
        inventory_system: InventorySystemProtocol,
        economy_state: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ShopSystem.

        Parameters
        ----------
        data_repository : DataRepositoryProtocol
            Repository voor data access (shops.json)
        inventory_system : InventorySystemProtocol
            Inventory system voor item management
        economy_state : dict[str, Any] | None
            Economy state dict met currency_amount en shop_states
            Format: {"currency_amount": int, "shop_states": {...}}
        """
        self._repository = data_repository
        self._inventory = inventory_system
        self._economy_state = economy_state or {"currency_amount": 0, "shop_states": {}}

        # Ensure structure exists
        if "currency_amount" not in self._economy_state:
            self._economy_state["currency_amount"] = 0
        if "shop_states" not in self._economy_state:
            self._economy_state["shop_states"] = {}

    def get_shop_definition(self, shop_id: str) -> ShopDefinition | None:
        """Haal shop definitie op uit DataRepository.

        Parameters
        ----------
        shop_id : str
            Shop ID (bijv. "shop_r1_town_general")

        Returns
        -------
        ShopDefinition | None
            Shop definitie of None als niet gevonden
        """
        shop_data = self._repository.get_shop(shop_id)
        if not shop_data:
            logger.warning(f"Shop not found: {shop_id}")
            return None

        # Parse inventory entries
        inventory_entries = []
        for entry_data in shop_data.get("inventory_entries", []):
            entry = ShopInventoryEntry(
                item_id=entry_data["item_id"],
                base_price=entry_data["base_price"],
                stock_type=entry_data.get("stock_type", "INFINITE"),
                min_chapter=entry_data.get("min_chapter", 1),
                max_chapter=entry_data.get("max_chapter", 99),
                conditions=entry_data.get("conditions", []),
            )
            inventory_entries.append(entry)

        return ShopDefinition(
            shop_id=shop_data["shop_id"],
            zone_id=shop_data["zone_id"],
            name=shop_data["name"],
            shop_type=shop_data["shop_type"],
            inventory_entries=inventory_entries,
        )

    def get_available_items(
        self, shop_id: str, *, chapter_id: int | None = None
    ) -> list[ShopInventoryEntry]:
        """Haal beschikbare items op voor een shop (gefilterd op chapter).

        Parameters
        ----------
        shop_id : str
            Shop ID
        chapter_id : int | None
            Current chapter (voor min/max filtering). None = geen filtering.

        Returns
        -------
        list[ShopInventoryEntry]
            Lijst van beschikbare items
        """
        shop_def = self.get_shop_definition(shop_id)
        if not shop_def:
            return []

        # V0: Filter alleen op chapter bounds, geen conditions/flags
        available = []
        for entry in shop_def.inventory_entries:
            # Check chapter bounds
            if chapter_id is not None and (
                chapter_id < entry.min_chapter or chapter_id > entry.max_chapter
            ):
                continue

            # V0: Ignore conditions, stock_type, etc.
            available.append(entry)

        return available

    def get_currency(self) -> int:
        """Haal huidige currency (Rūpa) op.

        Returns
        -------
        int
            Current currency amount
        """
        return self._economy_state.get("currency_amount", 0)

    def set_currency(self, amount: int) -> None:
        """Set currency amount (voor testen/initialization).

        Parameters
        ----------
        amount : int
            New currency amount
        """
        self._economy_state["currency_amount"] = max(0, amount)
        logger.debug(f"Currency set to {amount}")

    def can_afford(self, price: int, quantity: int = 1) -> bool:
        """Check of speler een aankoop kan betalen.

        Parameters
        ----------
        price : int
            Prijs per item
        quantity : int
            Aantal te kopen items

        Returns
        -------
        bool
            True als speler genoeg currency heeft
        """
        total_cost = price * quantity
        return self.get_currency() >= total_cost

    def buy_item(self, shop_id: str, item_id: str, quantity: int = 1) -> BuyResult:
        """Koop een item uit een shop.

        Parameters
        ----------
        shop_id : str
            Shop ID
        item_id : str
            Item ID om te kopen
        quantity : int
            Aantal te kopen items (v0: default 1)

        Returns
        -------
        BuyResult
            Resultaat van de transactie
        """
        current_currency = self.get_currency()

        # Validate shop exists
        shop_def = self.get_shop_definition(shop_id)
        if not shop_def:
            logger.warning(f"Buy failed: shop {shop_id} not found")
            return BuyResult(
                success=False,
                reason="SHOP_NOT_FOUND",
                new_currency_amount=current_currency,
            )

        # Find item in shop inventory
        shop_entry = None
        for entry in shop_def.inventory_entries:
            if entry.item_id == item_id:
                shop_entry = entry
                break

        if not shop_entry:
            logger.warning(f"Buy failed: item {item_id} not in shop {shop_id}")
            return BuyResult(
                success=False,
                reason="NOT_AVAILABLE",
                new_currency_amount=current_currency,
            )

        # Calculate total cost
        total_cost = shop_entry.base_price * quantity

        # Check if player can afford
        if not self.can_afford(shop_entry.base_price, quantity):
            logger.info(
                f"Buy failed: insufficient funds (need {total_cost}, have {current_currency})"
            )
            return BuyResult(
                success=False,
                reason="INSUFFICIENT_FUNDS",
                new_currency_amount=current_currency,
            )

        # V0: No stock checking (all INFINITE effectively)
        # V0: No quest item blocking (items.json doesn't have quest flag yet)

        # Execute transaction
        # 1. Deduct currency
        new_currency = current_currency - total_cost
        self._economy_state["currency_amount"] = new_currency

        # 2. Add item to inventory
        self._inventory.add_item(item_id, quantity)

        logger.info(
            f"Buy successful: {quantity}x {item_id} for {total_cost} Rūpa "
            f"(remaining: {new_currency})"
        )

        return BuyResult(
            success=True,
            reason="OK",
            new_currency_amount=new_currency,
            item_id=item_id,
            quantity=quantity,
        )

    def get_save_state(self) -> dict[str, Any]:
        """Get serializable economy state for saving.

        Returns
        -------
        dict[str, Any]
            Economy state dict
        """
        return {
            "currency_amount": self._economy_state.get("currency_amount", 0),
            "shop_states": self._economy_state.get("shop_states", {}),
        }

    def restore_from_save(self, state_dict: dict[str, Any]) -> None:
        """Restore economy state from save data.

        Parameters
        ----------
        state_dict : dict[str, Any]
            Economy state dict from save file
        """
        self._economy_state["currency_amount"] = state_dict.get("currency_amount", 0)
        self._economy_state["shop_states"] = state_dict.get("shop_states", {})

        logger.info(f"Economy state restored: {self._economy_state['currency_amount']} Rūpa")


__all__ = [
    "ShopSystem",
    "ShopDefinition",
    "ShopInventoryEntry",
    "ShopState",
    "BuyResult",
]
