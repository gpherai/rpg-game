"""Equipment system voor gear management (Step 9: Gear System v0)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import (
        DataRepositoryProtocol,
        InventorySystemProtocol,
        PartySystemProtocol,
    )
    from tri_sarira_rpg.systems.party import PartyMember

logger = logging.getLogger(__name__)


@dataclass
class EquipResult:
    """Result van een equip/unequip operatie."""

    success: bool
    reason: str = ""


class EquipmentSystem:
    """Beheert equippen/unequippen van gear en stat calculations.

    Voor Gear System v0:
    - 3 gear slots: weapon, body (armor), accessory1
    - Equip/unequip verplaatst items tussen inventory en gear slots
    - Effective stats = base stats + gear stat_mods
    - Basic validation (gear type matches slot, item exists in inventory)
    """

    def __init__(
        self,
        party_system: PartySystemProtocol,
        inventory_system: InventorySystemProtocol,
        data_repository: DataRepositoryProtocol,
    ) -> None:
        """Initialize EquipmentSystem.

        Parameters
        ----------
        party_system : PartySystemProtocol
            Party system reference
        inventory_system : InventorySystemProtocol
            Inventory system reference
        data_repository : DataRepositoryProtocol
            Data repository for item info
        """
        self._party = party_system
        self._inventory = inventory_system
        self._repository = data_repository

    def equip_gear(self, actor_id: str, item_id: str, slot: str) -> EquipResult:
        """Equip een gear item in een slot.

        Verplaatst item van inventory naar gear slot.
        Als er al gear in dat slot zit, wordt die eerst unequipped.

        Parameters
        ----------
        actor_id : str
            Actor ID
        item_id : str
            Item ID van gear
        slot : str
            Slot name: "weapon", "body", "accessory1"

        Returns
        -------
        EquipResult
            Result met success status en reason
        """
        # Validate slot
        valid_slots = ["weapon", "body", "accessory1"]
        if slot not in valid_slots:
            return EquipResult(False, f"Invalid slot: {slot}")

        # Find party member
        member = self._party.get_member_by_actor_id(actor_id)
        if not member:
            return EquipResult(False, f"Actor {actor_id} not found in party")

        # Check if item exists in inventory
        if not self._inventory.has_item(item_id, quantity=1):
            return EquipResult(False, f"Item {item_id} not in inventory")

        # Get item data
        item_data = self._repository.get_item(item_id)
        if not item_data:
            return EquipResult(False, f"Item {item_id} not found in data")

        # Validate item is gear
        if item_data.get("type") != "gear":
            return EquipResult(False, f"Item {item_id} is not gear")

        # Validate gear type matches slot
        item_slot = item_data.get("slot", "")
        expected_slot_mapping = {
            "weapon": "weapon",
            "body": "body",
            "accessory1": "accessory1",
        }
        expected_item_slot = expected_slot_mapping.get(slot)
        if item_slot != expected_item_slot:
            return EquipResult(
                False,
                f"Item {item_id} (slot={item_slot}) cannot be equipped in {slot} slot",
            )

        # If slot already occupied, unequip first
        current_gear_id = self._get_gear_in_slot(member, slot)
        if current_gear_id:
            unequip_result = self.unequip_gear(actor_id, slot)
            if not unequip_result.success:
                return EquipResult(False, f"Failed to unequip current gear: {unequip_result.reason}")

        # Remove from inventory
        if not self._inventory.remove_item(item_id, quantity=1):
            return EquipResult(False, f"Failed to remove {item_id} from inventory")

        # Equip to slot
        self._set_gear_in_slot(member, slot, item_id)

        logger.info(f"Equipped {item_id} to {actor_id} ({slot} slot)")
        return EquipResult(True, "Equipped successfully")

    def unequip_gear(self, actor_id: str, slot: str) -> EquipResult:
        """Unequip gear from een slot.

        Verplaatst item van gear slot naar inventory.

        Parameters
        ----------
        actor_id : str
            Actor ID
        slot : str
            Slot name: "weapon", "body", "accessory1"

        Returns
        -------
        EquipResult
            Result met success status en reason
        """
        # Validate slot
        valid_slots = ["weapon", "body", "accessory1"]
        if slot not in valid_slots:
            return EquipResult(False, f"Invalid slot: {slot}")

        # Find party member
        member = self._party.get_member_by_actor_id(actor_id)
        if not member:
            return EquipResult(False, f"Actor {actor_id} not found in party")

        # Check if slot is occupied
        gear_id = self._get_gear_in_slot(member, slot)
        if not gear_id:
            return EquipResult(False, f"No gear equipped in {slot} slot")

        # Add to inventory
        self._inventory.add_item(gear_id, quantity=1)

        # Remove from slot
        self._set_gear_in_slot(member, slot, None)

        logger.info(f"Unequipped {gear_id} from {actor_id} ({slot} slot)")
        return EquipResult(True, "Unequipped successfully")

    def get_effective_stats(self, actor_id: str) -> dict[str, int]:
        """Get effective stats (base stats + gear stat_mods) voor een actor.

        Parameters
        ----------
        actor_id : str
            Actor ID

        Returns
        -------
        dict[str, int]
            Effective stats dictionary
        """
        # Find party member
        member = self._party.get_member_by_actor_id(actor_id)
        if not member:
            logger.warning(f"Actor {actor_id} not found in party, returning empty stats")
            return {}

        # Start with base stats
        effective_stats = dict(member.base_stats)

        # Add stat mods from all equipped gear
        gear_ids = [
            member.weapon_id,
            member.armor_id,
            member.accessory1_id,
        ]

        for gear_id in gear_ids:
            if not gear_id:
                continue

            # Get item data
            item_data = self._repository.get_item(gear_id)
            if not item_data:
                logger.warning(f"Gear {gear_id} not found in data, skipping")
                continue

            # Apply stat mods
            stat_mods = item_data.get("stat_mods", {})
            for stat_name, mod_value in stat_mods.items():
                if stat_name not in effective_stats:
                    effective_stats[stat_name] = 0
                effective_stats[stat_name] += mod_value

        return effective_stats

    def can_equip(self, actor_id: str, item_id: str) -> tuple[bool, str]:
        """Check of een actor een item kan equippen.

        Parameters
        ----------
        actor_id : str
            Actor ID
        item_id : str
            Item ID

        Returns
        -------
        tuple[bool, str]
            (can_equip, reason_if_not)
        """
        # Find party member
        member = self._party.get_member_by_actor_id(actor_id)
        if not member:
            return False, f"Actor {actor_id} not found in party"

        # Get item data
        item_data = self._repository.get_item(item_id)
        if not item_data:
            return False, f"Item {item_id} not found in data"

        # Check if item is gear
        if item_data.get("type") != "gear":
            return False, f"Item {item_id} is not gear"

        # Check if item is in inventory
        if not self._inventory.has_item(item_id, quantity=1):
            return False, f"Item {item_id} not in inventory"

        # Basic validation passed
        return True, "Can equip"

    def get_all_equipped_gear(self, actor_id: str) -> dict[str, str | None]:
        """Get alle equipped gear voor een actor.

        Parameters
        ----------
        actor_id : str
            Actor ID

        Returns
        -------
        dict[str, str | None]
            Dictionary met slot names -> item_id (or None if empty)
        """
        member = self._party.get_member_by_actor_id(actor_id)
        if not member:
            return {"weapon": None, "body": None, "accessory1": None}

        return {
            "weapon": member.weapon_id,
            "body": member.armor_id,
            "accessory1": member.accessory1_id,
        }

    def get_available_gear_for_slot(self, slot: str) -> list[str]:
        """Get alle gear items uit inventory die in een slot passen.

        Parameters
        ----------
        slot : str
            Slot name: "weapon", "body", "accessory1"

        Returns
        -------
        list[str]
            List van item IDs
        """
        available_gear = []

        # Expected item slot mapping
        slot_mapping = {
            "weapon": "weapon",
            "body": "body",
            "accessory1": "accessory1",
        }
        expected_item_slot = slot_mapping.get(slot)

        if not expected_item_slot:
            return []

        # Check all items in inventory
        for item_id in self._inventory.get_available_items():
            item_data = self._repository.get_item(item_id)
            if not item_data:
                continue

            # Check if gear and correct slot
            if item_data.get("type") == "gear" and item_data.get("slot") == expected_item_slot:
                available_gear.append(item_id)

        return available_gear

    def _get_gear_in_slot(self, member: PartyMember, slot: str) -> str | None:
        """Helper: get gear ID in een slot."""
        if slot == "weapon":
            return member.weapon_id
        elif slot == "body":
            return member.armor_id
        elif slot == "accessory1":
            return member.accessory1_id
        else:
            return None

    def _set_gear_in_slot(self, member: PartyMember, slot: str, item_id: str | None) -> None:
        """Helper: set gear ID in een slot."""
        if slot == "weapon":
            member.weapon_id = item_id
        elif slot == "body":
            member.armor_id = item_id
        elif slot == "accessory1":
            member.accessory1_id = item_id


__all__ = ["EquipmentSystem", "EquipResult"]
