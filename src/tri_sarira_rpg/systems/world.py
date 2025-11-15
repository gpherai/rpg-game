"""WorldSystem - zone management, collision, portals, triggers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tri_sarira_rpg.core.entities import Position
from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.utils.tiled_loader import TiledLoader, TiledMap, TiledObject

logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """Speler positie en state in de wereld."""

    zone_id: str
    position: Position
    facing: str = "S"  # N, E, S, W


@dataclass
class Trigger:
    """Een getriggerde event (chest, shrine, cutscene)."""

    trigger_id: str
    trigger_type: str  # "ON_ENTER", "ON_INTERACT", "ON_STEP"
    position: Position
    event_id: str | None = None
    once_per_save: bool = True
    active: bool = True


class WorldSystem:
    """Beheert zones, collision, portals en event triggers."""

    def __init__(
        self,
        data_repository: DataRepository | None = None,
        maps_dir: Path | None = None,
    ) -> None:
        self._data_repository = data_repository or DataRepository()
        self._tiled_loader = TiledLoader(maps_dir=maps_dir)

        # Current world state
        self._current_zone_id: str | None = None
        self._current_map: TiledMap | None = None
        self._player: PlayerState | None = None

        # Triggers (chests, events)
        self._triggers: dict[str, Trigger] = {}
        self._triggered_ids: set[str] = set()  # For once_per_save tracking

    def load_zone(self, zone_id: str, spawn_id: str | None = None) -> None:
        """Laad een nieuwe zone en plaats de speler op een spawn point.

        Parameters
        ----------
        zone_id : str
            Zone ID, bijv. "z_r1_chandrapur_town"
        spawn_id : str | None
            Spawn point ID, of None voor default spawn
        """
        logger.info(f"Loading zone: {zone_id} (spawn: {spawn_id or 'default'})")

        # Load zone data from repository
        zone_data = self._data_repository.get_zone(zone_id)
        if not zone_data:
            raise ValueError(f"Zone not found in data: {zone_id}")

        # Load Tiled map
        try:
            tiled_map = self._tiled_loader.load_map(zone_id)
        except FileNotFoundError:
            logger.warning(
                f"Tiled map not found for {zone_id}, using placeholder map"
            )
            tiled_map = self._create_placeholder_map(zone_id)

        self._current_zone_id = zone_id
        self._current_map = tiled_map

        # Find spawn point
        if spawn_id:
            spawn = tiled_map.get_spawn_by_id(spawn_id)
        else:
            spawn = tiled_map.get_default_spawn()

        if spawn:
            spawn_x, spawn_y = spawn.get_tile_coords(tiled_map.tile_width)
            self._player = PlayerState(
                zone_id=zone_id, position=Position(x=spawn_x, y=spawn_y)
            )
            logger.info(f"Player spawned at ({spawn_x}, {spawn_y})")
        else:
            # Fallback: center of map
            center_x = tiled_map.width // 2
            center_y = tiled_map.height // 2
            self._player = PlayerState(
                zone_id=zone_id, position=Position(x=center_x, y=center_y)
            )
            logger.warning(
                f"No spawn point found, using map center: ({center_x}, {center_y})"
            )

        # Load triggers
        self._load_triggers()

        logger.info(f"✓ Zone loaded: {zone_id}")

    def _create_placeholder_map(self, zone_id: str) -> TiledMap:
        """Maak een lege placeholder map als TMX niet bestaat."""
        logger.warning(f"Creating placeholder map for {zone_id}")
        return TiledMap(
            width=20,
            height=15,
            tile_width=32,
            tile_height=32,
            properties={"zone_id": zone_id},
        )

    def _load_triggers(self) -> None:
        """Laad alle triggers uit de current map."""
        if not self._current_map:
            return

        self._triggers.clear()

        # Load chests
        for chest_obj in self._current_map.get_chests():
            chest_id = chest_obj.properties.get("chest_id", chest_obj.name)
            tile_x, tile_y = chest_obj.get_tile_coords(self._current_map.tile_width)

            trigger = Trigger(
                trigger_id=chest_id,
                trigger_type="ON_INTERACT",
                position=Position(x=tile_x, y=tile_y),
                event_id=chest_id,
                once_per_save=True,
            )
            self._triggers[chest_id] = trigger

        # Load event triggers
        for event_obj in self._current_map.get_events():
            event_id = event_obj.properties.get("event_id", event_obj.name)
            trigger_type = event_obj.properties.get("trigger_type", "ON_ENTER")
            once_per_save = event_obj.properties.get("once_per_save", True)
            tile_x, tile_y = event_obj.get_tile_coords(self._current_map.tile_width)

            trigger = Trigger(
                trigger_id=f"{event_id}_{tile_x}_{tile_y}",
                trigger_type=trigger_type,
                position=Position(x=tile_x, y=tile_y),
                event_id=event_id,
                once_per_save=once_per_save,
            )
            self._triggers[trigger.trigger_id] = trigger

        logger.info(f"Loaded {len(self._triggers)} triggers")

    def can_move_to(self, tile_x: int, tile_y: int) -> bool:
        """Check of de speler naar een tile kan bewegen."""
        if not self._current_map:
            return False

        # Check bounds
        if not (
            0 <= tile_x < self._current_map.width
            and 0 <= tile_y < self._current_map.height
        ):
            return False

        # Check collision
        return not self._current_map.get_collision_at(tile_x, tile_y)

    def move_player(self, dx: int, dy: int) -> bool:
        """Beweeg de speler met een delta.

        Parameters
        ----------
        dx, dy : int
            Delta movement in tiles

        Returns
        -------
        bool
            True als movement gelukt is
        """
        if not self._player:
            return False

        new_x = self._player.position.x + dx
        new_y = self._player.position.y + dy

        # Update facing direction
        if dx > 0:
            self._player.facing = "E"
        elif dx < 0:
            self._player.facing = "W"
        elif dy > 0:
            self._player.facing = "S"
        elif dy < 0:
            self._player.facing = "N"

        # Check collision
        if not self.can_move_to(new_x, new_y):
            return False

        # Move player
        self._player.position.x = new_x
        self._player.position.y = new_y

        # Check for triggers ON_STEP
        self._check_triggers_at_position("ON_STEP")

        # Check for portals
        self._check_portal_transition()

        return True

    def interact(self) -> None:
        """Interactie op de huidige positie of voor de speler."""
        if not self._player:
            return

        # Check current position
        self._check_triggers_at_position("ON_INTERACT")

        # Check position in front of player
        front_x, front_y = self._get_position_in_front()
        self._check_triggers_at_position("ON_INTERACT", Position(x=front_x, y=front_y))

    def _get_position_in_front(self) -> tuple[int, int]:
        """Geef de tile positie voor de speler."""
        if not self._player:
            return (0, 0)

        x, y = self._player.position.x, self._player.position.y
        if self._player.facing == "N":
            y -= 1
        elif self._player.facing == "S":
            y += 1
        elif self._player.facing == "E":
            x += 1
        elif self._player.facing == "W":
            x -= 1

        return (x, y)

    def _check_triggers_at_position(
        self, trigger_type: str, position: Position | None = None
    ) -> None:
        """Check of er triggers zijn op een positie."""
        if not self._player:
            return

        check_pos = position or self._player.position

        for trigger_id, trigger in self._triggers.items():
            if trigger.trigger_type != trigger_type:
                continue

            if not trigger.active:
                continue

            if trigger.position.x != check_pos.x or trigger.position.y != check_pos.y:
                continue

            # Check if already triggered
            if trigger.once_per_save and trigger_id in self._triggered_ids:
                continue

            # Trigger the event
            self._trigger_event(trigger)

    def _trigger_event(self, trigger: Trigger) -> None:
        """Activeer een trigger."""
        logger.info(
            f"Trigger activated: {trigger.trigger_id} "
            f"(type: {trigger.trigger_type}, event: {trigger.event_id})"
        )

        # Mark as triggered
        if trigger.once_per_save:
            self._triggered_ids.add(trigger.trigger_id)
            trigger.active = False

        # For Step 3, we just log the trigger
        # Later: call event system, open chest, start dialogue, etc.

    def _check_portal_transition(self) -> None:
        """Check of de speler op een portal staat en voer transitie uit."""
        if not self._player or not self._current_map:
            return

        portals = self._current_map.get_portals()
        player_x, player_y = self._player.position.x, self._player.position.y

        for portal in portals:
            portal_x, portal_y = portal.get_tile_coords(self._current_map.tile_width)

            # Check if player is on portal (we support multi-tile portals)
            portal_width_tiles = max(1, portal.width // self._current_map.tile_width)
            portal_height_tiles = max(1, portal.height // self._current_map.tile_height)

            if (
                portal_x <= player_x < portal_x + portal_width_tiles
                and portal_y <= player_y < portal_y + portal_height_tiles
            ):
                # Portal found!
                target_zone_id = portal.properties.get("target_zone_id")
                target_spawn_id = portal.properties.get("target_spawn_id")

                if target_zone_id:
                    logger.info(
                        f"Portal transition: {self._current_zone_id} → {target_zone_id} "
                        f"(spawn: {target_spawn_id or 'default'})"
                    )
                    self.load_zone(target_zone_id, target_spawn_id)
                    return

    @property
    def current_zone_id(self) -> str | None:
        """Huidige zone ID."""
        return self._current_zone_id

    @property
    def current_map(self) -> TiledMap | None:
        """Huidige Tiled map."""
        return self._current_map

    @property
    def player(self) -> PlayerState | None:
        """Speler state."""
        return self._player

    def get_zone_name(self) -> str:
        """Geef de naam van de huidige zone."""
        if not self._current_zone_id:
            return "Unknown"

        zone_data = self._data_repository.get_zone(self._current_zone_id)
        if zone_data:
            return zone_data.get("name", self._current_zone_id)

        return self._current_zone_id


__all__ = ["WorldSystem", "PlayerState", "Trigger"]
