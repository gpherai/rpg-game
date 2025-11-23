"""Save- en loadfunctionaliteit."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import (
        FlagsSystemProtocol,
        InventorySystemProtocol,
        PartySystemProtocol,
        QuestSystemProtocol,
        ShopSystemProtocol,
        TimeSystemProtocol,
        WorldSystemProtocol,
    )

logger = logging.getLogger(__name__)


class SaveSystem:
    """Bouwt save-structuren op vanuit actieve systems."""

    def __init__(
        self,
        party_system: PartySystemProtocol | None = None,
        world_system: WorldSystemProtocol | None = None,
        time_system: TimeSystemProtocol | None = None,
        inventory_system: InventorySystemProtocol | None = None,
        flags_system: FlagsSystemProtocol | None = None,
        quest_system: QuestSystemProtocol | None = None,
        shop_system: ShopSystemProtocol | None = None,
    ) -> None:
        """Initialize SaveSystem with references to game systems.

        Parameters
        ----------
        party_system : PartySystemProtocol | None
            PartySystem reference
        world_system : WorldSystemProtocol | None
            WorldSystem reference
        time_system : TimeSystemProtocol | None
            TimeSystem reference
        inventory_system : InventorySystemProtocol | None
            InventorySystem reference
        flags_system : FlagsSystemProtocol | None
            GameStateFlags reference
        quest_system : QuestSystemProtocol | None
            QuestSystem reference
        shop_system : ShopSystemProtocol | None
            ShopSystem reference
        """
        self._party = party_system
        self._world = world_system
        self._time = time_system
        self._inventory = inventory_system
        self._flags = flags_system
        self._quest = quest_system
        self._shop = shop_system

        # Save directory
        self._save_dir = Path("saves")

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------
    def _metadata_path(self, slot_id: int) -> Path:
        """Pad naar metadata-bestand voor een slot."""
        return self._save_dir / f"save_slot_{slot_id}_meta.json"

    def _build_metadata(self, slot_id: int, save_data: dict[str, Any]) -> dict[str, Any]:
        """Maak compacte metadata voor load-previews."""
        meta = save_data.get("meta", {})
        time_state = save_data.get("time_state", {})
        world_state = save_data.get("world_state", {})

        zone_id = world_state.get("current_zone_id")
        zone_name: str | None = None

        # Probeer de user-facing zonenaam via WorldSystem (optioneel)
        if self._world and self._world.current_zone_id == zone_id:
            try:
                zone_name = self._world.get_zone_name()
            except Exception:
                zone_name = None

        return {
            "slot_id": slot_id,
            "saved_at": datetime.now().isoformat(),
            "play_time": meta.get("play_time", 0.0),
            "day_index": time_state.get("day_index"),
            "time_of_day": time_state.get("time_of_day"),
            "zone_id": zone_id,
            "zone_name": zone_name or zone_id,
        }

    def _write_metadata(self, slot_id: int, save_data: dict[str, Any]) -> None:
        """Schrijf metadata naar schijf (best effort)."""
        try:
            metadata = self._build_metadata(slot_id, save_data)
            meta_path = self._metadata_path(slot_id)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            # Metadata is nice-to-have; log en ga verder
            logger.warning(f"Kon metadata voor slot {slot_id} niet schrijven: {exc}")

    def build_save(self, play_time: float = 0.0) -> dict[str, Any]:
        """Verzamel data uit systemen en maak een SaveData-dict.

        Parameters
        ----------
        play_time : float
            Total play time in seconds

        Returns
        -------
        dict[str, Any]
            Complete save data structure
        """
        save_data: dict[str, Any] = {
            "meta": {
                "schema_version": 1,
                "created_at": datetime.now().isoformat(),
                "play_time": play_time,
            },
            "time_state": {},
            "world_state": {},
            "party_state": {},
            "inventory_state": {},
            "economy_state": {},
            "flags_state": {},
            "quest_state": [],
        }

        # Collect state from each system
        if self._time:
            save_data["time_state"] = self._time.get_save_state()

        if self._world:
            save_data["world_state"] = self._world.get_save_state()

        if self._party:
            save_data["party_state"] = self._party.get_save_state()

        if self._inventory:
            save_data["inventory_state"] = self._inventory.get_save_state()

        if self._shop:
            save_data["economy_state"] = self._shop.get_save_state()

        if self._flags:
            save_data["flags_state"] = self._flags.get_save_state()

        if self._quest:
            save_data["quest_state"] = self._quest.get_save_state()

        logger.info("Save data built successfully")
        return save_data

    def save_to_file(self, slot_id: int, save_data: dict[str, Any]) -> bool:
        """Write save data to JSON file.

        Parameters
        ----------
        slot_id : int
            Save slot number (1-5)
        save_data : dict[str, Any]
            Save data to write

        Returns
        -------
        bool
            True if save succeeded, False otherwise
        """
        try:
            # Create saves directory if it doesn't exist
            self._save_dir.mkdir(exist_ok=True)

            # Write to file
            save_file = self._save_dir / f"save_slot_{slot_id}.json"
            with open(save_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            # Schrijf compacte metadata (best effort, geen invloed op hoofdresultaat)
            self._write_metadata(slot_id, save_data)

            logger.info(f"Game saved to {save_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return False

    def load_from_file(self, slot_id: int) -> dict[str, Any] | None:
        """Load save data from JSON file.

        Parameters
        ----------
        slot_id : int
            Save slot number (1-5)

        Returns
        -------
        dict[str, Any] | None
            Save data if successful, None if failed
        """
        try:
            save_file = self._save_dir / f"save_slot_{slot_id}.json"

            if not save_file.exists():
                logger.warning(f"Save file not found: {save_file}")
                return None

            with open(save_file, encoding="utf-8") as f:
                save_data = json.load(f)

            logger.info(f"Save data loaded from {save_file}")
            return save_data

        except Exception as e:
            logger.error(f"Failed to load save: {e}")
            return None

    def load_metadata(self, slot_id: int) -> dict[str, Any] | None:
        """Laad compacte metadata voor een save slot.

        Als het metadata-bestand ontbreekt maar de save wel bestaat,
        wordt een fallback-meta opgebouwd uit het hoofd-savebestand.
        """
        meta_path = self._metadata_path(slot_id)
        try:
            if meta_path.exists():
                with open(meta_path, encoding="utf-8") as f:
                    return json.load(f)

            # Fallback: probeer metadata te reconstrueren uit het save-bestand
            save_data = self.load_from_file(slot_id)
            if save_data:
                return self._build_metadata(slot_id, save_data)
        except Exception as exc:
            logger.warning(f"Kon metadata voor slot {slot_id} niet laden: {exc}")

        return None

    def load_save(self, payload: dict[str, Any]) -> bool:
        """Herstel systemen vanuit een SaveData-dict.

        Parameters
        ----------
        payload : dict[str, Any]
            Save data to restore

        Returns
        -------
        bool
            True if load succeeded, False otherwise
        """
        try:
            # Restore each system's state
            if self._time and "time_state" in payload:
                self._time.restore_from_save(payload["time_state"])

            if self._world and "world_state" in payload:
                self._world.restore_from_save(payload["world_state"])

            if self._party and "party_state" in payload:
                self._party.restore_from_save(payload["party_state"])

            if self._inventory and "inventory_state" in payload:
                self._inventory.restore_from_save(payload["inventory_state"])

            if self._shop and "economy_state" in payload:
                self._shop.restore_from_save(payload["economy_state"])

            if self._flags and "flags_state" in payload:
                self._flags.restore_from_save(payload["flags_state"])

            if self._quest and "quest_state" in payload:
                self._quest.restore_from_save(payload["quest_state"])

            logger.info("Game state restored successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to restore game state: {e}")
            return False

    def export_trilogy_profile(self) -> dict[str, Any]:
        """Maak een compacte export voor vervolgspellen.

        Returns
        -------
        dict[str, Any]
            Trilogy profile data (not implemented in v0)
        """
        # Placeholder for trilogy continuity feature
        return {}

    def slot_exists(self, slot_id: int) -> bool:
        """Check if a save slot exists.

        Parameters
        ----------
        slot_id : int
            Save slot number

        Returns
        -------
        bool
            True if save file exists
        """
        save_file = self._save_dir / f"save_slot_{slot_id}.json"
        return save_file.exists()


__all__ = ["SaveSystem"]
