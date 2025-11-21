"""Tests voor Equipment System (Step 9: Gear System v0)."""

import pytest

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.equipment import EquipmentSystem
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.party import PartyMember, PartySystem


@pytest.fixture
def mock_repository():
    """Mock DataRepository met gear items."""

    class MockRepo:
        def get_item(self, item_id: str):
            items = {
                "item_gear_simple_staff": {
                    "id": "item_gear_simple_staff",
                    "name": "Simple Staff",
                    "type": "gear",
                    "gear_type": "weapon",
                    "slot": "weapon",
                    "stat_mods": {"STR": 2, "MAG": 1},
                },
                "item_gear_iron_dagger": {
                    "id": "item_gear_iron_dagger",
                    "name": "Iron Dagger",
                    "type": "gear",
                    "gear_type": "weapon",
                    "slot": "weapon",
                    "stat_mods": {"STR": 3, "SPD": 1},
                },
                "item_gear_travelers_cloth": {
                    "id": "item_gear_travelers_cloth",
                    "name": "Traveler's Cloth",
                    "type": "gear",
                    "gear_type": "armor",
                    "slot": "body",
                    "stat_mods": {"DEF": 2, "RES": 1},
                },
                "item_gear_copper_ring": {
                    "id": "item_gear_copper_ring",
                    "name": "Copper Ring",
                    "type": "gear",
                    "gear_type": "accessory",
                    "slot": "accessory1",
                    "stat_mods": {"END": 1, "WILL": 1},
                },
                "item_small_herb": {
                    "id": "item_small_herb",
                    "name": "Small Herb",
                    "type": "consumable",
                },
            }
            return items.get(item_id)

    return MockRepo()


@pytest.fixture
def party_system():
    """Create a basic PartySystem with test members."""
    party = PartySystem(data_repository=None, npc_meta=None)
    # Clear default party and add test members
    party._state.active_party.clear()

    member = PartyMember(
        npc_id="test_npc",
        actor_id="test_actor",
        is_main_character=True,
        level=1,
        base_stats={"STR": 10, "END": 8, "DEF": 6, "MAG": 5, "SPD": 7},
    )
    party._state.active_party.append(member)

    return party


@pytest.fixture
def inventory_system():
    """Create InventorySystem with gear items."""
    inventory = InventorySystem()
    # Add some gear to inventory
    inventory.add_item("item_gear_simple_staff", 1)
    inventory.add_item("item_gear_travelers_cloth", 1)
    inventory.add_item("item_gear_copper_ring", 1)
    inventory.add_item("item_small_herb", 3)
    return inventory


@pytest.fixture
def equipment_system(party_system, inventory_system, mock_repository):
    """Create EquipmentSystem."""
    return EquipmentSystem(
        party_system=party_system,
        inventory_system=inventory_system,
        data_repository=mock_repository,
    )


def test_equip_weapon_success(equipment_system, inventory_system, party_system):
    """Test equipping a weapon successfully."""
    result = equipment_system.equip_gear("test_actor", "item_gear_simple_staff", "weapon")

    assert result.success is True
    assert inventory_system.has_item("item_gear_simple_staff") is False

    member = party_system.get_member_by_actor_id("test_actor")
    assert member.weapon_id == "item_gear_simple_staff"


def test_equip_armor_success(equipment_system, inventory_system, party_system):
    """Test equipping armor successfully."""
    result = equipment_system.equip_gear("test_actor", "item_gear_travelers_cloth", "body")

    assert result.success is True
    assert inventory_system.has_item("item_gear_travelers_cloth") is False

    member = party_system.get_member_by_actor_id("test_actor")
    assert member.armor_id == "item_gear_travelers_cloth"


def test_equip_accessory_success(equipment_system, inventory_system, party_system):
    """Test equipping accessory successfully."""
    result = equipment_system.equip_gear("test_actor", "item_gear_copper_ring", "accessory1")

    assert result.success is True
    assert inventory_system.has_item("item_gear_copper_ring") is False

    member = party_system.get_member_by_actor_id("test_actor")
    assert member.accessory1_id == "item_gear_copper_ring"


def test_equip_wrong_slot(equipment_system):
    """Test equipping gear in wrong slot fails."""
    result = equipment_system.equip_gear(
        "test_actor", "item_gear_simple_staff", "body"
    )  # weapon in body slot

    assert result.success is False
    assert "cannot be equipped" in result.reason.lower()


def test_equip_consumable_fails(equipment_system):
    """Test equipping a consumable item fails."""
    result = equipment_system.equip_gear("test_actor", "item_small_herb", "weapon")

    assert result.success is False
    assert "not gear" in result.reason.lower()


def test_equip_not_in_inventory(equipment_system, inventory_system):
    """Test equipping item not in inventory fails."""
    # Remove item from inventory first
    inventory_system.remove_item("item_gear_simple_staff", 1)

    result = equipment_system.equip_gear("test_actor", "item_gear_simple_staff", "weapon")

    assert result.success is False
    assert "not in inventory" in result.reason.lower()


def test_equip_replaces_existing(equipment_system, inventory_system, party_system):
    """Test equipping new gear replaces old gear and returns it to inventory."""
    # Equip first weapon
    equipment_system.equip_gear("test_actor", "item_gear_simple_staff", "weapon")
    assert party_system.get_member_by_actor_id("test_actor").weapon_id == "item_gear_simple_staff"
    assert inventory_system.has_item("item_gear_simple_staff") is False

    # Add second weapon to inventory
    inventory_system.add_item("item_gear_iron_dagger", 1)

    # Equip second weapon (should unequip first and return to inventory)
    result = equipment_system.equip_gear("test_actor", "item_gear_iron_dagger", "weapon")

    assert result.success is True
    assert party_system.get_member_by_actor_id("test_actor").weapon_id == "item_gear_iron_dagger"
    assert inventory_system.has_item("item_gear_simple_staff") is True
    assert inventory_system.has_item("item_gear_iron_dagger") is False


def test_unequip_weapon_success(equipment_system, inventory_system, party_system):
    """Test unequipping weapon successfully."""
    # Equip weapon first
    equipment_system.equip_gear("test_actor", "item_gear_simple_staff", "weapon")

    # Unequip
    result = equipment_system.unequip_gear("test_actor", "weapon")

    assert result.success is True
    assert party_system.get_member_by_actor_id("test_actor").weapon_id is None
    assert inventory_system.has_item("item_gear_simple_staff") is True


def test_unequip_empty_slot(equipment_system):
    """Test unequipping from empty slot fails."""
    result = equipment_system.unequip_gear("test_actor", "weapon")

    assert result.success is False
    assert "no gear equipped" in result.reason.lower()


def test_get_effective_stats_no_gear(equipment_system, party_system):
    """Test effective stats with no gear equipped (should equal base stats)."""
    member = party_system.get_member_by_actor_id("test_actor")
    base_stats = dict(member.base_stats)

    effective_stats = equipment_system.get_effective_stats("test_actor")

    assert effective_stats == base_stats


def test_get_effective_stats_with_weapon(equipment_system, party_system):
    """Test effective stats with weapon equipped."""
    member = party_system.get_member_by_actor_id("test_actor")
    base_str = member.base_stats["STR"]
    base_mag = member.base_stats["MAG"]

    # Equip staff (+2 STR, +1 MAG)
    equipment_system.equip_gear("test_actor", "item_gear_simple_staff", "weapon")

    effective_stats = equipment_system.get_effective_stats("test_actor")

    assert effective_stats["STR"] == base_str + 2
    assert effective_stats["MAG"] == base_mag + 1


def test_get_effective_stats_with_multiple_gear(equipment_system, party_system):
    """Test effective stats with multiple gear pieces equipped."""
    member = party_system.get_member_by_actor_id("test_actor")
    base_str = member.base_stats["STR"]
    base_mag = member.base_stats["MAG"]
    base_def = member.base_stats["DEF"]
    base_end = member.base_stats["END"]

    # Equip weapon (+2 STR, +1 MAG), armor (+2 DEF, +1 RES), accessory (+1 END, +1 WILL)
    equipment_system.equip_gear("test_actor", "item_gear_simple_staff", "weapon")
    equipment_system.equip_gear("test_actor", "item_gear_travelers_cloth", "body")
    equipment_system.equip_gear("test_actor", "item_gear_copper_ring", "accessory1")

    effective_stats = equipment_system.get_effective_stats("test_actor")

    assert effective_stats["STR"] == base_str + 2  # from weapon
    assert effective_stats["MAG"] == base_mag + 1  # from weapon
    assert effective_stats["DEF"] == base_def + 2  # from armor
    assert effective_stats["END"] == base_end + 1  # from accessory
    assert effective_stats["RES"] == 1  # from armor (was 0 in base)
    assert effective_stats["WILL"] == 1  # from accessory (was 0 in base)


def test_can_equip_valid(equipment_system):
    """Test can_equip returns True for valid gear."""
    can_equip, reason = equipment_system.can_equip("test_actor", "item_gear_simple_staff")

    assert can_equip is True


def test_can_equip_not_in_inventory(equipment_system, inventory_system):
    """Test can_equip returns False for gear not in inventory."""
    inventory_system.remove_item("item_gear_simple_staff", 1)

    can_equip, reason = equipment_system.can_equip("test_actor", "item_gear_simple_staff")

    assert can_equip is False
    assert "not in inventory" in reason.lower()


def test_can_equip_consumable(equipment_system):
    """Test can_equip returns False for consumables."""
    can_equip, reason = equipment_system.can_equip("test_actor", "item_small_herb")

    assert can_equip is False
    assert "not gear" in reason.lower()


def test_get_all_equipped_gear(equipment_system, party_system):
    """Test getting all equipped gear."""
    # Initially all slots empty
    gear = equipment_system.get_all_equipped_gear("test_actor")
    assert gear == {"weapon": None, "body": None, "accessory1": None}

    # Equip some gear
    equipment_system.equip_gear("test_actor", "item_gear_simple_staff", "weapon")
    equipment_system.equip_gear("test_actor", "item_gear_copper_ring", "accessory1")

    gear = equipment_system.get_all_equipped_gear("test_actor")
    assert gear["weapon"] == "item_gear_simple_staff"
    assert gear["body"] is None
    assert gear["accessory1"] == "item_gear_copper_ring"


def test_get_available_gear_for_slot(equipment_system, inventory_system):
    """Test getting available gear for a specific slot."""
    # Add another weapon to inventory
    inventory_system.add_item("item_gear_iron_dagger", 1)

    weapons = equipment_system.get_available_gear_for_slot("weapon")
    assert "item_gear_simple_staff" in weapons
    assert "item_gear_iron_dagger" in weapons
    assert "item_gear_travelers_cloth" not in weapons  # armor, not weapon

    armor = equipment_system.get_available_gear_for_slot("body")
    assert "item_gear_travelers_cloth" in armor
    assert "item_gear_simple_staff" not in armor


def test_save_and_restore_gear_state(party_system, inventory_system):
    """Test saving and restoring gear state through PartySystem."""
    # Create member with gear
    member = party_system.get_member_by_actor_id("test_actor")
    member.weapon_id = "item_gear_simple_staff"
    member.armor_id = "item_gear_travelers_cloth"
    member.accessory1_id = "item_gear_copper_ring"

    # Save state
    save_state = party_system.get_save_state()

    # Clear and restore
    party_system._state.active_party.clear()
    party_system.restore_from_save(save_state)

    # Verify gear restored
    restored_member = party_system.get_member_by_actor_id("test_actor")
    assert restored_member.weapon_id == "item_gear_simple_staff"
    assert restored_member.armor_id == "item_gear_travelers_cloth"
    assert restored_member.accessory1_id == "item_gear_copper_ring"
