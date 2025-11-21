"""Tests voor ShopSystem (Step 8: Shop System v0)."""

from __future__ import annotations

import pytest

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.shop import (
    ShopDefinition,
    ShopInventoryEntry,
    ShopSystem,
)


@pytest.fixture
def data_repository() -> DataRepository:
    """Create a DataRepository for testing."""
    return DataRepository()


@pytest.fixture
def inventory_system() -> InventorySystem:
    """Create an InventorySystem for testing."""
    return InventorySystem()


@pytest.fixture
def shop_system(data_repository: DataRepository, inventory_system: InventorySystem) -> ShopSystem:
    """Create a ShopSystem with initial currency."""
    economy_state = {"currency_amount": 100, "shop_states": {}}
    shop = ShopSystem(data_repository, inventory_system, economy_state)
    return shop


def test_load_shop_definition(shop_system: ShopSystem) -> None:
    """Test dat shop definitie correct wordt geladen uit repository."""
    shop_def = shop_system.get_shop_definition("shop_r1_town_general")

    assert shop_def is not None
    assert isinstance(shop_def, ShopDefinition)
    assert shop_def.shop_id == "shop_r1_town_general"
    assert shop_def.zone_id == "z_r1_chandrapur_town"
    assert shop_def.name == "Chandrapur General"
    assert shop_def.shop_type == "GENERAL"
    assert len(shop_def.inventory_entries) > 0

    # Check that inventory entries are parsed correctly
    assert all(isinstance(entry, ShopInventoryEntry) for entry in shop_def.inventory_entries)


def test_load_nonexistent_shop(shop_system: ShopSystem) -> None:
    """Test dat niet-bestaande shop None teruggeeft."""
    shop_def = shop_system.get_shop_definition("shop_does_not_exist")

    assert shop_def is None


def test_available_items_respects_chapter_bounds(shop_system: ShopSystem) -> None:
    """Test dat available items correct worden gefilterd op chapter bounds."""
    # Get all items without chapter filtering
    all_items = shop_system.get_available_items("shop_r1_town_general", chapter_id=None)
    assert len(all_items) > 0

    # Get items for chapter 1 (should include items with min_chapter=1)
    chapter1_items = shop_system.get_available_items("shop_r1_town_general", chapter_id=1)
    assert len(chapter1_items) > 0

    # All chapter 1 items should have min_chapter <= 1 and max_chapter >= 1
    for item in chapter1_items:
        assert item.min_chapter <= 1
        assert item.max_chapter >= 1

    # Get items for chapter 99 (might exclude some items with max_chapter < 99)
    chapter99_items = shop_system.get_available_items("shop_r1_town_general", chapter_id=99)

    # Items should have min_chapter <= 99 and max_chapter >= 99
    for item in chapter99_items:
        assert item.min_chapter <= 99
        assert item.max_chapter >= 99


def test_buy_item_happy_path_updates_currency_and_inventory(
    shop_system: ShopSystem, inventory_system: InventorySystem
) -> None:
    """Test dat succesvolle aankoop currency verlaagt en item toevoegt aan inventory."""
    initial_currency = shop_system.get_currency()
    assert initial_currency == 100

    # Buy a small herb (base_price: 10)
    result = shop_system.buy_item("shop_r1_town_general", "item_small_herb", quantity=1)

    assert result.success is True
    assert result.reason == "OK"
    assert result.new_currency_amount == initial_currency - 10
    assert result.item_id == "item_small_herb"
    assert result.quantity == 1

    # Verify currency was deducted
    assert shop_system.get_currency() == initial_currency - 10

    # Verify item was added to inventory
    assert inventory_system.has_item("item_small_herb", 1)
    assert inventory_system.get_quantity("item_small_herb") == 1


def test_buy_item_insufficient_funds(shop_system: ShopSystem) -> None:
    """Test dat aankoop faalt bij onvoldoende currency."""
    # Set currency to a low amount
    shop_system.set_currency(5)

    # Try to buy an item that costs 10
    result = shop_system.buy_item("shop_r1_town_general", "item_small_herb", quantity=1)

    assert result.success is False
    assert result.reason == "INSUFFICIENT_FUNDS"
    assert result.new_currency_amount == 5  # Currency unchanged

    # Verify currency was not deducted
    assert shop_system.get_currency() == 5


def test_buy_item_not_in_shop(shop_system: ShopSystem) -> None:
    """Test dat aankoop faalt voor item dat niet in shop is."""
    initial_currency = shop_system.get_currency()

    # Try to buy an item that doesn't exist in this shop
    result = shop_system.buy_item("shop_r1_town_general", "item_nonexistent", quantity=1)

    assert result.success is False
    assert result.reason == "NOT_AVAILABLE"
    assert result.new_currency_amount == initial_currency

    # Verify currency was not deducted
    assert shop_system.get_currency() == initial_currency


def test_buy_item_from_nonexistent_shop(shop_system: ShopSystem) -> None:
    """Test dat aankoop faalt voor niet-bestaande shop."""
    initial_currency = shop_system.get_currency()

    # Try to buy from a shop that doesn't exist
    result = shop_system.buy_item("shop_does_not_exist", "item_small_herb", quantity=1)

    assert result.success is False
    assert result.reason == "SHOP_NOT_FOUND"
    assert result.new_currency_amount == initial_currency

    # Verify currency was not deducted
    assert shop_system.get_currency() == initial_currency


def test_buy_multiple_items(shop_system: ShopSystem, inventory_system: InventorySystem) -> None:
    """Test dat meerdere items tegelijk kopen correct werkt."""
    initial_currency = shop_system.get_currency()
    assert initial_currency == 100

    # Buy 3 small herbs (base_price: 10 each = 30 total)
    result = shop_system.buy_item("shop_r1_town_general", "item_small_herb", quantity=3)

    assert result.success is True
    assert result.reason == "OK"
    assert result.new_currency_amount == initial_currency - 30
    assert result.item_id == "item_small_herb"
    assert result.quantity == 3

    # Verify currency was deducted
    assert shop_system.get_currency() == initial_currency - 30

    # Verify items were added to inventory
    assert inventory_system.get_quantity("item_small_herb") == 3


def test_can_afford(shop_system: ShopSystem) -> None:
    """Test dat can_afford correct checkt of speler item kan betalen."""
    shop_system.set_currency(50)

    # Can afford 1 item of 10
    assert shop_system.can_afford(10, 1) is True

    # Can afford 5 items of 10 (total 50)
    assert shop_system.can_afford(10, 5) is True

    # Cannot afford 6 items of 10 (total 60)
    assert shop_system.can_afford(10, 6) is False

    # Cannot afford 1 item of 100
    assert shop_system.can_afford(100, 1) is False


def test_get_set_currency(shop_system: ShopSystem) -> None:
    """Test dat get/set currency correct werkt."""
    # Initial currency
    assert shop_system.get_currency() == 100

    # Set new currency
    shop_system.set_currency(500)
    assert shop_system.get_currency() == 500

    # Set to 0
    shop_system.set_currency(0)
    assert shop_system.get_currency() == 0

    # Negative values should be clamped to 0
    shop_system.set_currency(-100)
    assert shop_system.get_currency() == 0


def test_save_and_restore_economy_state(
    data_repository: DataRepository, inventory_system: InventorySystem
) -> None:
    """Test dat economy state correct wordt opgeslagen en hersteld."""
    # Create shop with initial state
    economy_state = {"currency_amount": 250, "shop_states": {}}
    shop1 = ShopSystem(data_repository, inventory_system, economy_state)

    # Make a purchase
    shop1.buy_item("shop_r1_town_general", "item_small_herb", quantity=2)

    # Get save state
    save_state = shop1.get_save_state()

    assert save_state["currency_amount"] == 250 - 20  # 230
    assert "shop_states" in save_state

    # Create new shop and restore
    shop2 = ShopSystem(data_repository, inventory_system)
    shop2.restore_from_save(save_state)

    # Verify state was restored
    assert shop2.get_currency() == 230


def test_inventory_accumulates_across_purchases(
    shop_system: ShopSystem, inventory_system: InventorySystem
) -> None:
    """Test dat inventory items accumulate bij meerdere aankopen."""
    # Buy 2 small herbs
    shop_system.buy_item("shop_r1_town_general", "item_small_herb", quantity=2)
    assert inventory_system.get_quantity("item_small_herb") == 2

    # Buy 3 more small herbs
    shop_system.buy_item("shop_r1_town_general", "item_small_herb", quantity=3)
    assert inventory_system.get_quantity("item_small_herb") == 5  # 2 + 3 = 5


def test_buy_different_items_from_same_shop(
    shop_system: ShopSystem, inventory_system: InventorySystem
) -> None:
    """Test dat verschillende items uit dezelfde shop gekocht kunnen worden."""
    initial_currency = shop_system.get_currency()

    # Buy small herb (price: 10)
    result1 = shop_system.buy_item("shop_r1_town_general", "item_small_herb", quantity=1)
    assert result1.success is True

    # Buy stamina tonic (price: 20)
    result2 = shop_system.buy_item("shop_r1_town_general", "item_stamina_tonic", quantity=1)
    assert result2.success is True

    # Verify total cost was deducted (10 + 20 = 30)
    assert shop_system.get_currency() == initial_currency - 30

    # Verify both items are in inventory
    assert inventory_system.has_item("item_small_herb", 1)
    assert inventory_system.has_item("item_stamina_tonic", 1)
