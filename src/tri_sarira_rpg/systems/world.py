"""WorldSystem - zone management, collision, portals, triggers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tri_sarira_rpg.core.entities import Position
from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.quest import QuestStatus
from tri_sarira_rpg.utils.tiled_loader import TiledLoader, TiledMap

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
        flags_system: Any | None = None,
        quest_system: Any | None = None,
        inventory_system: Any | None = None,
        combat_system: Any | None = None,
        time_system: Any | None = None,
        on_show_message: Any | None = None,
        on_start_battle: Any | None = None,
        on_start_dialogue: Any | None = None,
    ) -> None:
        self._data_repository = data_repository or DataRepository()
        self._tiled_loader = TiledLoader(maps_dir=maps_dir)
        self._flags = flags_system
        self._quest = quest_system
        self._inventory = inventory_system
        self._combat = combat_system
        self._time = time_system
        self._on_show_message = on_show_message
        self._on_start_battle = on_start_battle
        self._on_start_dialogue = on_start_dialogue

        # Current world state
        self._current_zone_id: str | None = None
        self._current_map: TiledMap | None = None
        self._player: PlayerState | None = None

        # Triggers (chests, events)
        self._triggers: dict[str, Trigger] = {}
        self._triggered_ids: set[str] = set()  # For once_per_save tracking

    def reset_state(self) -> None:
        """Reset runtime state (triggers, current map/player) for new games."""
        self._current_zone_id = None
        self._current_map = None
        self._player = None
        self._triggers.clear()
        self._triggered_ids.clear()

    def load_zone(
        self,
        zone_id: str,
        spawn_id: str | None = None,
        from_portal: bool = False,
        facing: str | None = None,
    ) -> None:
        """Laad een nieuwe zone en plaats de speler op een spawn point.

        Parameters
        ----------
        zone_id : str
            Zone ID, bijv. "z_r1_chandrapur_town"
        spawn_id : str | None
            Spawn point ID, of None voor default spawn
        from_portal : bool
            True als zone load getriggerd is door portal transition.
            Voorkomt infinite loops bij portals op spawn points.
        facing : str | None
            Richting waarin de speler kijkt na spawn (N/E/S/W). Bij None wordt
            een spawn property "facing" gebruikt of fallback "S".
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
            logger.warning(f"Tiled map not found for {zone_id}, using placeholder map")
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
            spawn_facing = facing or spawn.properties.get("facing") or "S"
            self._player = PlayerState(
                zone_id=zone_id, position=Position(x=spawn_x, y=spawn_y), facing=spawn_facing
            )
            logger.info(f"Player spawned at ({spawn_x}, {spawn_y})")
        else:
            # Fallback: center of map
            center_x = tiled_map.width // 2
            center_y = tiled_map.height // 2
            spawn_facing = facing or "S"
            self._player = PlayerState(
                zone_id=zone_id, position=Position(x=center_x, y=center_y), facing=spawn_facing
            )
            logger.warning(f"No spawn point found, using map center: ({center_x}, {center_y})")

        # Load triggers
        self._load_triggers()
        self._deactivate_triggered_triggers()

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

    def _deactivate_triggered_triggers(self) -> None:
        """Zet eerder getriggerde once_per_save triggers direct uit na load."""
        for trigger_id in self._triggered_ids:
            trigger = self._triggers.get(trigger_id)
            if trigger and trigger.once_per_save:
                trigger.active = False

    def can_move_to(self, tile_x: int, tile_y: int) -> bool:
        """Check of de speler naar een tile kan bewegen."""
        if not self._current_map:
            return False

        # Check bounds
        if not (0 <= tile_x < self._current_map.width and 0 <= tile_y < self._current_map.height):
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

        if self._time:
            self._time.on_player_step()

        # Check for triggers ON_ENTER and ON_STEP
        self._check_triggers_at_position("ON_ENTER")
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

    def attach_systems(
        self,
        *,
        flags_system: Any | None = None,
        quest_system: Any | None = None,
        inventory_system: Any | None = None,
        combat_system: Any | None = None,
        on_show_message: Any | None = None,
        on_start_battle: Any | None = None,
        on_start_dialogue: Any | None = None,
        time_system: Any | None = None,
    ) -> None:
        """Koppel optionele systems voor triggers/collectables."""
        if flags_system:
            self._flags = flags_system
        if quest_system:
            self._quest = quest_system
        if inventory_system:
            self._inventory = inventory_system
        if combat_system:
            self._combat = combat_system
        if time_system:
            self._time = time_system
        if on_show_message:
            self._on_show_message = on_show_message
        if on_start_battle:
            self._on_start_battle = on_start_battle
        if on_start_dialogue:
            self._on_start_dialogue = on_start_dialogue

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

        # Chest trigger (chest_id == event_id)
        if trigger.event_id:
            chest = self._data_repository.get_chest(trigger.event_id)
            if chest:
                self._open_chest(chest)
                return

            # Regular event trigger
            event_def = self._data_repository.get_event(trigger.event_id)
            if event_def:
                self._execute_event_actions(event_def.get("actions", []))
                return

        logger.warning(f"No event/chest found for trigger {trigger.event_id}")

    def _open_chest(self, chest: dict[str, Any]) -> None:
        """Verwerk chest contents en flags."""
        chest_id = chest.get("chest_id", "<unknown>")

        # Already opened?
        opened_flag = f"chest_opened_{chest_id}"
        if self._flags and self._flags.has_flag(opened_flag):
            logger.info(f"Chest {chest_id} already opened")
            return

        # Give items
        contents = chest.get("contents", [])
        if self._inventory:
            for entry in contents:
                item_id = entry.get("item_id")
                qty = entry.get("quantity", 1)
                if item_id:
                    self._inventory.add_item(item_id, qty)
                    logger.info(f"Received {qty}x {item_id} from chest {chest_id}")
        else:
            logger.warning("No inventory system attached; cannot grant chest items")

        # Set flag
        if self._flags:
            self._flags.set_flag(opened_flag)

        # Feedback message
        if self._on_show_message:
            if not contents:
                loot_text = "It was empty."
            else:
                loot_items = []
                for entry in contents:
                    item_id = entry.get("item_id")
                    qty = entry.get("quantity", 1)
                    if item_id and self._data_repository:
                        item_def = self._data_repository.get_item(item_id)
                        item_name = item_def.get("name", item_id) if item_def else item_id
                        loot_items.append(f"{item_name} (x{qty})")
                loot_text = f"You found: {', '.join(loot_items)}"
            self._on_show_message(loot_text)

    def _execute_event_actions(self, actions: list[dict[str, Any]]) -> None:
        """Voer event acties uit."""
        for action in actions:
            action_type = action.get("action_type")
            if not action_type:
                logger.warning("Event action missing action_type")
                continue

            if action_type == "SHOW_MESSAGE":
                message = action.get("message", "")
                if self._on_show_message:
                    self._on_show_message(message)
                logger.info(f"[EVENT] {message}")

            elif action_type == "SET_FLAG":
                flag_id = action.get("flag_id")
                if flag_id and self._flags:
                    self._flags.set_flag(flag_id)
                    logger.info(f"[EVENT] Flag set: {flag_id}")

            elif action_type == "CLEAR_FLAG":
                flag_id = action.get("flag_id")
                if flag_id and self._flags:
                    self._flags.clear_flag(flag_id)
                    logger.info(f"[EVENT] Flag cleared: {flag_id}")

            elif action_type in ("GIVE_ITEM", "GRANT_REWARDS"):
                item_id = action.get("item_id")
                qty = action.get("quantity", 1)
                if item_id and self._inventory:
                    self._inventory.add_item(item_id, qty)
                    logger.info(f"[EVENT] Received {qty}x {item_id}")

            elif action_type == "CHEST_OPEN":
                chest_id = action.get("chest_id")
                if chest_id:
                    chest_def = self._data_repository.get_chest(chest_id)
                    if chest_def:
                        self._open_chest(chest_def)
                    else:
                        logger.warning(f"[EVENT] Chest {chest_id} not found")

            elif action_type == "START_BATTLE":
                group_id = action.get("enemy_group_id")
                if group_id:
                    group = self._data_repository.get_enemy_group(group_id)
                    if not group:
                        logger.warning(f"[EVENT] Enemy group {group_id} not found")
                        continue
                    enemy_ids = group.get("enemies", [])
                    if self._on_start_battle:
                        self._on_start_battle(enemy_ids)
                    elif self._combat:
                        self._combat.start_battle(enemy_ids)
                    logger.info(f"[EVENT] Battle started with group {group_id} ({enemy_ids})")
                else:
                    logger.warning("[EVENT] Cannot start battle; missing combat system or group_id")

            elif action_type == "QUEST_START":
                quest_id = action.get("quest_id")
                if quest_id and self._quest and self._data_repository:
                    try:
                        self._quest.start_quest(quest_id)
                        logger.info(f"[EVENT] Quest started: {quest_id}")
                        if self._on_show_message:
                            q_def = self._data_repository.get_quest(quest_id)
                            q_title = q_def.get("title", quest_id) if q_def else quest_id
                            self._on_show_message(f"Quest Started: {q_title}")
                    except Exception as e:
                        logger.warning(f"[EVENT] Failed to start quest {quest_id}: {e}")

            elif action_type == "QUEST_ADVANCE":
                quest_id = action.get("quest_id")
                stage_id = action.get("stage_id") or action.get("next_stage_id")
                if quest_id and self._quest and self._data_repository:
                    try:
                        state = self._quest.get_state(quest_id)
                        if getattr(state, "status", None) != QuestStatus.ACTIVE:
                            logger.info(
                                f"[EVENT] Quest {quest_id} not active, skipping advance to {stage_id}"
                            )
                        else:
                            self._quest.advance_quest(quest_id, stage_id)
                            logger.info(f"[EVENT] Quest advanced: {quest_id} -> {stage_id}")
                            if self._on_show_message:
                                q_def = self._data_repository.get_quest(quest_id)
                                q_title = q_def.get("title", quest_id) if q_def else quest_id
                                self._on_show_message(f"Quest Updated: {q_title}")
                    except Exception as e:
                        logger.warning(f"[EVENT] Failed to advance quest {quest_id}: {e}")

            elif action_type == "COMPLETE_QUEST_STAGE":
                quest_id = action.get("quest_id")
                stage_id = action.get("stage_id")
                if quest_id and self._quest:
                    try:
                        state = self._quest.get_state(quest_id)
                        if getattr(state, "status", None) != QuestStatus.ACTIVE:
                            logger.info(f"[EVENT] Quest {quest_id} not active, skipping complete")
                        else:
                            self._quest.advance_quest(quest_id, stage_id)
                            logger.info(f"[EVENT] Quest stage completed: {quest_id} {stage_id}")
                    except Exception as e:
                        logger.warning(f"[EVENT] Failed to complete quest stage {quest_id}: {e}")

            elif action_type == "QUEST_COMPLETE":
                quest_id = action.get("quest_id")
                if quest_id and self._quest and self._data_repository:
                    try:
                        state = self._quest.get_state(quest_id)
                        if getattr(state, "status", None) != QuestStatus.ACTIVE:
                            logger.info(f"[EVENT] Quest {quest_id} not active, skipping complete")
                        else:
                            self._quest.complete_quest(quest_id)
                            logger.info(f"[EVENT] Quest completed: {quest_id}")
                            if self._on_show_message:
                                q_def = self._data_repository.get_quest(quest_id)
                                q_title = q_def.get("title", quest_id) if q_def else quest_id
                                self._on_show_message(f"Quest Completed: {q_title}")
                    except Exception as e:
                        logger.warning(f"[EVENT] Failed to complete quest {quest_id}: {e}")

            elif action_type == "START_DIALOGUE":
                dialogue_id = action.get("dialogue_id")
                if dialogue_id:
                    if self._on_start_dialogue:
                        self._on_start_dialogue(dialogue_id)
                    else:
                        logger.warning("[EVENT] START_DIALOGUE has no handler attached")

            elif action_type == "PLAY_CUTSCENE":
                cutscene_id = action.get("cutscene_id", "<unknown>")
                logger.info(f"[EVENT] Play cutscene: {cutscene_id} (stub)")
                # Optional inline message for feedback
                msg = action.get("message")
                if msg and self._on_show_message:
                    self._on_show_message(msg)

            else:
                logger.warning(f"[EVENT] Unsupported action_type: {action_type}")

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
                    current_facing = self._player.facing if self._player else None
                    self.load_zone(
                        target_zone_id, target_spawn_id, from_portal=True, facing=current_facing
                    )
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

    def get_save_state(self) -> dict[str, Any]:
        """Get serializable world state for saving.

        Returns
        -------
        dict[str, Any]
            World state as dict
        """
        player_state = {}
        if self._player:
            player_state = {
                "zone_id": self._player.zone_id,
                "position": {"x": self._player.position.x, "y": self._player.position.y},
                "facing": self._player.facing,
            }

        return {
            "current_zone_id": self._current_zone_id,
            "player_state": player_state,
            "triggered_ids": list(self._triggered_ids),
        }

    def restore_from_save(self, state_dict: dict[str, Any]) -> None:
        """Restore world state from save data.

        Parameters
        ----------
        state_dict : dict[str, Any]
            World state dict from save file
        """
        # Restore triggered IDs
        self._triggered_ids = set(state_dict.get("triggered_ids", []))

        # Restore player and zone
        zone_id = state_dict.get("current_zone_id")
        player_state = state_dict.get("player_state", {})

        if zone_id:
            # Load the zone (this will load the map and triggers)
            self.load_zone(zone_id)
            self._deactivate_triggered_triggers()

            # Override player position with saved position
            if player_state and self._player:
                pos = player_state.get("position", {})
                self._player.position.x = pos.get("x", 0)
                self._player.position.y = pos.get("y", 0)
                self._player.facing = player_state.get("facing", "S")
                logger.info(
                    f"Player restored at ({self._player.position.x}, {self._player.position.y})"
                )

        logger.info(f"World restored: zone={zone_id}, triggered_events={len(self._triggered_ids)}")


__all__ = ["WorldSystem", "PlayerState", "Trigger"]
