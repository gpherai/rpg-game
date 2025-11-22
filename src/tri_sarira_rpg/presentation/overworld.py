"""OverworldScene - map rendering, player movement, overworld gameplay."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import GameProtocol

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.presentation.theme import (
    Colors,
    FontSizes,
    Sizes,
    Spacing,
    Timing,
    FONT_FAMILY,
)
from tri_sarira_rpg.presentation.ui.dialogue_box import DialogueBox
from tri_sarira_rpg.presentation.ui.equipment_menu import EquipmentMenuUI
from tri_sarira_rpg.presentation.ui.hud import HUD, HUDData, PartyMemberInfo
from tri_sarira_rpg.presentation.ui.pause_menu import PauseMenu
from tri_sarira_rpg.presentation.ui.quest_log import QuestLogUI
from tri_sarira_rpg.presentation.ui.shop_menu import ShopMenuUI
from tri_sarira_rpg.services.game_data import GameDataService
from tri_sarira_rpg.systems.combat import CombatSystem
from tri_sarira_rpg.systems.dialogue import (
    DialogueContext,
    DialogueSession,
    DialogueSystem,
)
from tri_sarira_rpg.systems.equipment import EquipmentSystem
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.quest import QuestSystem
from tri_sarira_rpg.systems.shop import ShopSystem
from tri_sarira_rpg.systems.state import GameStateFlags
from tri_sarira_rpg.systems.time import TimeSystem
from tri_sarira_rpg.systems.world import WorldSystem

logger = logging.getLogger(__name__)


class OverworldScene(Scene):
    """Overworld scene met map rendering en player movement."""

    def __init__(
        self,
        manager: SceneManager,
        world_system: WorldSystem,
        time_system: TimeSystem,
        party_system: PartySystem,
        combat_system: CombatSystem,
        inventory_system: InventorySystem,
        data_repository: DataRepository,
        flags_system: GameStateFlags | None = None,
        quest_system: QuestSystem | None = None,
        shop_system: ShopSystem | None = None,
        equipment_system: EquipmentSystem | None = None,
        game_instance: GameProtocol | None = None,
    ) -> None:
        super().__init__(manager)
        self._world = world_system
        self._time = time_system
        self._party = party_system
        self._combat = combat_system
        self._inventory = inventory_system
        self._data_repository = data_repository
        self._data_service = GameDataService(data_repository)
        self._flags = flags_system or GameStateFlags()
        self._quest = quest_system
        self._shop = shop_system
        self._equipment = equipment_system
        self._game = game_instance

        # Dialogue system and UI
        self._dialogue_system = DialogueSystem(data_repository)
        self._dialogue_session: DialogueSession | None = None
        self._dialogue_box: DialogueBox | None = None

        # Quest log UI
        self._quest_log_visible: bool = False
        self._quest_log_ui: QuestLogUI | None = None

        # Shop UI (Step 8: Shop System v0)
        self._shop_menu_visible: bool = False
        self._shop_menu_ui: ShopMenuUI | None = None

        # Equipment UI (Step 9: Gear System v0)
        self._equipment_menu_visible: bool = False
        self._equipment_menu_ui: EquipmentMenuUI | None = None

        # Feedback message for save/load
        self._feedback_message: str = ""
        self._feedback_timer: float = 0.0

        # Get screen resolution dynamically
        screen = pygame.display.get_surface()
        if screen:
            self._screen_width, self._screen_height = screen.get_size()
        else:
            # Fallback to default resolution if no surface exists yet
            self._screen_width, self._screen_height = Sizes.SCREEN_DEFAULT

        # Movement timing (tile-based)
        self._move_cooldown: float = 0.0
        self._move_delay: float = Timing.MOVE_DELAY

        # Camera (simple follow)
        self._camera_x: int = 0
        self._camera_y: int = 0

        # Fonts for HUD
        pygame.font.init()
        self._font = pygame.font.SysFont(FONT_FAMILY, FontSizes.NORMAL)
        self._font_large = pygame.font.SysFont(FONT_FAMILY, FontSizes.XLARGE)

        # Initialize DialogueBox (at bottom of screen)
        dialogue_height = Sizes.DIALOGUE_HEIGHT
        dialogue_y = self._screen_height - dialogue_height - Sizes.DIALOGUE_MARGIN
        dialogue_rect = pygame.Rect(
            Sizes.DIALOGUE_MARGIN,
            dialogue_y,
            self._screen_width - Sizes.DIALOGUE_MARGIN * 2,
            dialogue_height,
        )
        self._dialogue_box = DialogueBox(dialogue_rect)

        # Initialize QuestLogUI (centered on screen)
        quest_log_width, quest_log_height = Sizes.QUEST_LOG
        quest_log_x = (self._screen_width - quest_log_width) // 2
        quest_log_y = (self._screen_height - quest_log_height) // 2
        quest_log_rect = pygame.Rect(quest_log_x, quest_log_y, quest_log_width, quest_log_height)
        self._quest_log_ui = QuestLogUI(quest_log_rect)

        # Initialize PauseMenu (centered on screen)
        self._paused: bool = False
        pause_width, pause_height = Sizes.PAUSE_MENU
        pause_x = (self._screen_width - pause_width) // 2
        pause_y = (self._screen_height - pause_height) // 2
        pause_rect = pygame.Rect(pause_x, pause_y, pause_width, pause_height)
        self._pause_menu = PauseMenu(pause_rect, game_instance=game_instance, allow_load=True)
        # Set callback for returning to main menu
        if game_instance:
            self._pause_menu.set_main_menu_callback(game_instance.return_to_main_menu)

        # Initialize HUD (decoupled component that receives data via update_stats)
        hud_rect = pygame.Rect(0, 0, self._screen_width, self._screen_height)
        self._hud = HUD(hud_rect)

        # Initialize ShopMenuUI (will be created when needed)
        # This gets initialized when opening shop for first time

    def handle_event(self, event: pygame.event.Event) -> None:
        """Verwerk input events."""
        if event.type == pygame.KEYDOWN:
            # Priority 1: If shop menu is visible, route to shop menu UI first
            # (so ESC closes shop instead of opening pause menu)
            if self._shop_menu_visible:
                if self._shop_menu_ui:
                    should_close = self._shop_menu_ui.handle_event(event)
                    if should_close:
                        self._shop_menu_visible = False
                        logger.debug("Closing shop menu")
                return

            # Priority 1.5: If equipment menu is visible, route to equipment menu UI
            if self._equipment_menu_visible:
                if self._equipment_menu_ui:
                    should_close = self._equipment_menu_ui.handle_event(event)
                    if should_close:
                        self._equipment_menu_visible = False
                        logger.debug("Closing equipment menu")
                return

            # Priority 2: If quest log is visible, route to quest log UI
            if self._quest_log_visible:
                if event.key == pygame.K_q:
                    # Toggle quest log off
                    self._quest_log_visible = False
                elif self._quest_log_ui:
                    # Route other events to quest log for navigation
                    self._quest_log_ui.handle_event(event)
                return

            # Priority 3: If in dialogue mode, route to dialogue box
            if self._dialogue_session:
                self._handle_dialogue_input(event)
                return

            # Priority 4: Pause menu toggle (Esc key)
            # Only handles ESC if no other overlay is active
            if event.key == pygame.K_ESCAPE:
                if self._paused:
                    # Already paused, let pause menu handle it
                    should_close = self._pause_menu.handle_input(event.key)
                    if should_close:
                        self._paused = False
                        logger.debug("Resuming from pause menu")
                else:
                    # Not paused, open pause menu
                    self._paused = True
                    logger.debug("Opening pause menu")
                return

            # If paused, route all input to pause menu
            if self._paused:
                should_close = self._pause_menu.handle_input(event.key)
                if should_close:
                    self._paused = False
                    logger.debug("Resuming from pause menu")
                return

            # Quest log toggle (Q key)
            if event.key == pygame.K_q:
                self._toggle_quest_log()

            # Equipment menu toggle (I key for Inventory/Equipment)
            elif event.key == pygame.K_i:
                self._toggle_equipment_menu()

            # Interact key
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                self._world.interact()

            # Save game (F5 key - industry standard)
            elif event.key == pygame.K_F5:
                self._quick_save()

            # Load game (F9 key - industry standard)
            elif event.key == pygame.K_F9:
                self._quick_load()

            # Debug key: Start dialogue (Step 6 Dialogue v0)
            elif event.key == pygame.K_n:
                self._debug_start_dialogue()

            # Debug key: Toggle Rajani in/out of party (Step 4 v0)
            elif event.key == pygame.K_j:
                self._debug_toggle_rajani()

            # Debug key: Start battle (Step 5 Combat v0)
            elif event.key == pygame.K_b:
                self._debug_start_battle()

            # Debug key: Start test quest (Step 7 Quest v0)
            elif event.key == pygame.K_t:
                self._debug_start_quest()

            # Debug key: Advance test quest (Step 7 Quest v0)
            elif event.key == pygame.K_y:
                self._debug_advance_quest()

            # Debug key: Complete test quest (Step 7 Quest v0)
            elif event.key == pygame.K_u:
                self._debug_complete_quest()

            # Debug key: Open shop (Step 8 Shop v0)
            elif event.key == pygame.K_g:
                self._debug_open_shop()

    def update(self, dt: float) -> None:
        """Update overworld logic."""
        # If paused, only update pause menu
        if self._paused:
            self._pause_menu.update(dt)
            return

        # If shop menu is visible, only update shop menu
        if self._shop_menu_visible:
            if self._shop_menu_ui:
                self._shop_menu_ui.update(dt)
            return

        # If equipment menu is visible, only update equipment menu
        if self._equipment_menu_visible:
            if self._equipment_menu_ui:
                self._equipment_menu_ui.update(dt)
            return

        # Update time system
        self._time.update(dt)

        # Update feedback timer
        if self._feedback_timer > 0:
            self._feedback_timer -= dt

        # Skip movement if in dialogue or quest log is open
        if self._dialogue_session or self._quest_log_visible:
            return

        # Update move cooldown
        if self._move_cooldown > 0:
            self._move_cooldown -= dt

        # Handle movement input
        if self._move_cooldown <= 0:
            keys = pygame.key.get_pressed()

            dx, dy = 0, 0

            # WASD / Arrow keys
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy = -1
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy = 1
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -1
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = 1

            if dx != 0 or dy != 0:
                # Try to move
                moved = self._world.move_player(dx, dy)
                if moved:
                    self._move_cooldown = self._move_delay
                    # Advance time on movement
                    self._time.on_player_step()

        # Update camera to follow player
        self._update_camera()

    def render(self, surface: pygame.Surface) -> None:
        """Render de overworld."""
        # Clear screen
        surface.fill(Colors.BG_DARK)

        # Render map
        self._render_map(surface)

        # Render followers (before player so player is on top)
        self._render_followers(surface)

        # Render player
        self._render_player(surface)

        # Render HUD
        self._render_hud(surface)

        # Render dialogue box if active
        if self._dialogue_session and self._dialogue_box:
            self._render_dialogue(surface)

        # Render quest log if visible
        if self._quest_log_visible and self._quest_log_ui:
            self._quest_log_ui.draw(surface)

        # Render shop menu if visible
        if self._shop_menu_visible and self._shop_menu_ui:
            self._shop_menu_ui.draw(surface)

        # Render equipment menu if visible
        if self._equipment_menu_visible and self._equipment_menu_ui:
            self._equipment_menu_ui.render(surface)

        # Render pause menu if paused
        if self._paused:
            self._pause_menu.render(surface)

    def _update_camera(self) -> None:
        """Update camera om player te volgen."""
        if not self._world.player or not self._world.current_map:
            return

        player = self._world.player
        tiled_map = self._world.current_map

        # Center camera on player
        screen_center_x = self._screen_width // 2
        screen_center_y = self._screen_height // 2

        tile_size = tiled_map.tile_width

        # Calculate camera position (top-left corner in pixels)
        self._camera_x = (player.position.x * tile_size) - screen_center_x
        self._camera_y = (player.position.y * tile_size) - screen_center_y

        # Clamp camera to map bounds
        max_camera_x = (tiled_map.width * tile_size) - self._screen_width
        max_camera_y = (tiled_map.height * tile_size) - self._screen_height

        self._camera_x = max(0, min(self._camera_x, max(0, max_camera_x)))
        self._camera_y = max(0, min(self._camera_y, max(0, max_camera_y)))

    def _render_map(self, surface: pygame.Surface) -> None:
        """Render de Tiled map."""
        tiled_map = self._world.current_map
        if not tiled_map:
            # No map loaded, show placeholder
            text = self._font_large.render("No map loaded", True, Colors.TEXT_WHITE)
            surface.blit(text, (400, 300))
            return

        tile_size = tiled_map.tile_width

        # Calculate visible tile range
        start_tile_x = max(0, self._camera_x // tile_size)
        start_tile_y = max(0, self._camera_y // tile_size)
        end_tile_x = min(tiled_map.width, (self._camera_x + self._screen_width) // tile_size + 1)
        end_tile_y = min(tiled_map.height, (self._camera_y + self._screen_height) // tile_size + 1)

        # Render tile layers (simplified placeholder rendering)
        # In a real implementation, we'd load tilesets and render actual tiles
        # For Step 3, we'll render colored rectangles based on collision

        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                screen_x = (x * tile_size) - self._camera_x
                screen_y = (y * tile_size) - self._camera_y

                # Check collision for color
                is_blocked = tiled_map.get_collision_at(x, y)

                if is_blocked:
                    # Blocked tile: dark gray
                    color = Colors.TILE_BLOCKED
                else:
                    # Walkable tile: light green
                    color = Colors.TILE_WALKABLE

                pygame.draw.rect(surface, color, (screen_x, screen_y, tile_size, tile_size))

                # Draw grid lines
                pygame.draw.rect(
                    surface,
                    Colors.TILE_GRID,
                    (screen_x, screen_y, tile_size, tile_size),
                    1,
                )

        # Render portals (for debugging)
        for portal in tiled_map.get_portals():
            portal_x, portal_y = portal.get_tile_coords(tile_size)
            screen_x = (portal_x * tile_size) - self._camera_x
            screen_y = (portal_y * tile_size) - self._camera_y

            # Draw portal as yellow rectangle
            pygame.draw.rect(
                surface,
                Colors.PORTAL,
                (screen_x, screen_y, tile_size, tile_size),
                3,
            )

        # Render chests (for debugging)
        for chest in tiled_map.get_chests():
            chest_x, chest_y = chest.get_tile_coords(tile_size)
            screen_x = (chest_x * tile_size) - self._camera_x
            screen_y = (chest_y * tile_size) - self._camera_y

            # Draw chest as brown rectangle
            pygame.draw.rect(
                surface,
                Colors.CHEST,
                (screen_x + 4, screen_y + 4, tile_size - 8, tile_size - 8),
            )

    def _render_followers(self, surface: pygame.Surface) -> None:
        """Render party followers (Step 4 v0)."""
        player = self._world.player
        if not player or not self._world.current_map:
            return

        tile_size = self._world.current_map.tile_width
        active_party = self._party.get_active_party()

        # Skip first member (MC/player)
        followers = active_party[1:]
        if not followers:
            return

        # Calculate follower positions (1 tile behind player, then chain)
        # Start with player position
        current_x, current_y = player.position.x, player.position.y
        current_facing = player.facing

        # Facing offset (opposite direction for followers)
        facing_offset = {
            "N": (0, 1),  # If player faces North, follower is South
            "S": (0, -1),  # If player faces South, follower is North
            "E": (-1, 0),  # If player faces East, follower is West
            "W": (1, 0),  # If player faces West, follower is East
        }

        for i, follower in enumerate(followers):
            # Calculate follower tile position (1 tile behind previous)
            dx, dy = facing_offset.get(current_facing, (0, 1))
            follower_tile_x = current_x + dx
            follower_tile_y = current_y + dy

            # Convert to screen coords
            screen_x = (follower_tile_x * tile_size) - self._camera_x
            screen_y = (follower_tile_y * tile_size) - self._camera_y

            # Draw follower as green circle (different color from player)
            center_x = screen_x + tile_size // 2
            center_y = screen_y + tile_size // 2
            radius = tile_size // 3

            # Color variation for different followers
            if i == 0:
                color = Colors.FOLLOWER  # Light green for first follower
            else:
                color = Colors.FOLLOWER_DARK  # Darker green for additional followers

            pygame.draw.circle(surface, color, (center_x, center_y), radius)

            # Draw small indicator showing this is a follower
            pygame.draw.circle(
                surface, Colors.FOLLOWER_INDICATOR, (center_x, center_y - radius // 2), radius // 4
            )

            # Update position for next follower
            current_x, current_y = follower_tile_x, follower_tile_y
            # Keep same facing for chain

    def _render_player(self, surface: pygame.Surface) -> None:
        """Render de speler."""
        player = self._world.player
        if not player or not self._world.current_map:
            return

        tile_size = self._world.current_map.tile_width

        screen_x = (player.position.x * tile_size) - self._camera_x
        screen_y = (player.position.y * tile_size) - self._camera_y

        # Draw player as blue circle
        center_x = screen_x + tile_size // 2
        center_y = screen_y + tile_size // 2
        radius = tile_size // 3

        pygame.draw.circle(surface, Colors.PLAYER, (center_x, center_y), radius)

        # Draw direction indicator
        facing_offset = {
            "N": (0, -radius),
            "S": (0, radius),
            "E": (radius, 0),
            "W": (-radius, 0),
        }
        dx, dy = facing_offset.get(player.facing, (0, 0))
        pygame.draw.circle(surface, Colors.TEXT_WHITE, (center_x + dx, center_y + dy), radius // 3)

    def _build_hud_data(self) -> HUDData:
        """Bouw HUDData view model voor de HUD component.

        Dit zorgt voor decoupling: OverworldScene verzamelt data uit systems
        en geeft die door aan de HUD component via een view model.

        Returns
        -------
        HUDData
            View model met alle data die de HUD nodig heeft
        """
        # Build party member info list
        active_party = self._party.get_active_party()
        party_members = [
            PartyMemberInfo(
                name=member.actor_id.replace("mc_", "").replace("comp_", "").capitalize(),
                level=member.level,
                is_main_character=member.is_main_character,
            )
            for member in active_party
        ]

        # Get player position
        player = self._world.player
        player_x = player.position.x if player else 0
        player_y = player.position.y if player else 0

        return HUDData(
            zone_name=self._world.get_zone_name(),
            time_display=self._time.get_time_display(),
            party_members=party_members,
            party_max_size=self._party.party_max_size,
            player_x=player_x,
            player_y=player_y,
            feedback_message=self._feedback_message,
            feedback_visible=self._feedback_timer > 0,
            screen_width=self._screen_width,
            screen_height=self._screen_height,
        )

    def _render_hud(self, surface: pygame.Surface) -> None:
        """Render HUD via de gedecoupelde HUD component."""
        hud_data = self._build_hud_data()
        self._hud.update_stats(hud_data)
        self._hud.draw(surface)

    def _quick_save(self) -> None:
        """Quick save to slot 1 (S key)."""
        if not self._game:
            logger.warning("Cannot save: no game instance available")
            return

        success = self._game.save_game(slot_id=1)

        if success:
            self._feedback_message = "Game saved!"
            self._feedback_timer = Timing.FEEDBACK_DURATION
        else:
            self._feedback_message = "Save failed!"
            self._feedback_timer = Timing.FEEDBACK_DURATION

    def _quick_load(self) -> None:
        """Quick load from slot 1 (L key)."""
        if not self._game:
            logger.warning("Cannot load: no game instance available")
            return

        success = self._game.load_game(slot_id=1)

        if success:
            self._feedback_message = "Game loaded!"
            self._feedback_timer = Timing.FEEDBACK_DURATION
        else:
            self._feedback_message = "Load failed - no save found!"
            self._feedback_timer = Timing.FEEDBACK_DURATION

    def _debug_toggle_rajani(self) -> None:
        """Debug functie: toggle Rajani in/uit active party (Step 4 v0)."""
        rajani_npc_id = "npc_comp_rajani"
        rajani_actor_id = "comp_rajani"

        # Check if Rajani is in active party
        if self._party.is_in_party(rajani_npc_id):
            # Move to reserve
            success = self._party.move_to_reserve(rajani_npc_id)
            if success:
                logger.info("[DEBUG] Rajani moved to reserve pool")
            else:
                logger.warning("[DEBUG] Failed to move Rajani to reserve (is she MC?)")
        elif self._party.is_in_reserve(rajani_npc_id):
            # Move to active party
            success = self._party.add_to_active_party(rajani_npc_id)
            if success:
                logger.info("[DEBUG] Rajani added to active party")
            else:
                logger.warning("[DEBUG] Party full, cannot add Rajani")
        else:
            # Not recruited yet, recruit her and add to party
            logger.info("[DEBUG] Rajani not recruited, recruiting now...")
            self._party.add_to_reserve_pool(rajani_npc_id, rajani_actor_id, tier="A")
            success = self._party.add_to_active_party(rajani_npc_id)
            if success:
                logger.info("[DEBUG] Rajani recruited and added to active party")
            else:
                logger.warning("[DEBUG] Party full, Rajani recruited but in reserve")

    def _debug_start_battle(self) -> None:
        """Debug functie: start een test battle (Step 5 Combat v0)."""
        from tri_sarira_rpg.presentation.battle import BattleScene

        logger.info("[DEBUG] Starting test battle...")

        # Start battle with Forest Sprout enemy
        enemy_ids = ["en_forest_sprout"]
        self._combat.start_battle(enemy_ids)

        # Push BattleScene onto scene stack
        battle_scene = BattleScene(
            self.manager,
            self._combat,
            self._inventory,
            self._data_repository,
            game_instance=self._game,
        )
        self.manager.push_scene(battle_scene)

    def _debug_start_dialogue(self) -> None:
        """Debug functie: start test dialogue (Step 6 Dialogue v0)."""
        logger.info("[DEBUG] Starting test dialogue...")

        # Create dialogue context with system references
        context = DialogueContext(
            flags_system=self._flags,
            party_system=self._party,
            inventory_system=self._inventory,
            economy_system=None,  # Not implemented yet
            quest_system=self._quest,
        )

        # Start dialogue session
        dialogue_id = "dbg_adhira_rajani_intro"
        session = self._dialogue_system.start_dialogue(dialogue_id, context)

        if session:
            self._dialogue_session = session
            self._update_dialogue_view()
            logger.info(f"[DEBUG] Started dialogue: {dialogue_id}")
        else:
            logger.error(f"[DEBUG] Failed to start dialogue: {dialogue_id}")

    def _handle_dialogue_input(self, event: pygame.event.Event) -> None:
        """Handle input tijdens dialogue."""
        if not self._dialogue_session or not self._dialogue_box:
            return

        # Pass event to dialogue box and get selected choice_id
        choice_id = self._dialogue_box.handle_event(event)

        if choice_id:
            # Player made a choice
            logger.debug(f"Player chose: {choice_id}")
            result = self._dialogue_system.choose_option(self._dialogue_session, choice_id)

            if result.conversation_ended:
                logger.info("Dialogue ended")
                self._dialogue_session = None
            else:
                # Update dialogue view for next node
                self._update_dialogue_view()
        else:
            # Check for continue/advance (Space/Enter when no choices)
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                view = self._dialogue_system.get_current_view(self._dialogue_session)
                if not view:
                    # No view means conversation ended
                    self._dialogue_session = None
                    return

                # If no choices, allow advancing/ending
                if len(view.choices) == 0:
                    if view.can_auto_advance:
                        # Auto-advance to next node
                        result = self._dialogue_system.auto_advance(self._dialogue_session)
                        if result.conversation_ended:
                            logger.info("Dialogue ended (auto-advance)")
                            self._dialogue_session = None
                        else:
                            self._update_dialogue_view()
                    else:
                        # No auto_advance and no choices = end conversation
                        # (this handles end_conversation=true nodes)
                        logger.info("Dialogue ended (no choices, player continued)")
                        self._dialogue_session = None

    def _update_dialogue_view(self) -> None:
        """Update dialogue box met huidige node view."""
        if not self._dialogue_session or not self._dialogue_box:
            return

        view = self._dialogue_system.get_current_view(self._dialogue_session)
        if not view:
            # Conversation ended
            self._dialogue_session = None
            return

        # Convert ChoiceView list to (choice_id, text) tuples
        choices = [(c.choice_id, c.text) for c in view.choices]

        # Update dialogue box
        self._dialogue_box.set_content(view.speaker_id, view.lines, choices)

    def _refresh_quest_log(self) -> None:
        """Refresh quest log UI with current quest data."""
        if not self._quest or not self._quest_log_ui:
            return

        quest_log_entries = self._quest.build_quest_log_view()
        # Convert QuestLogEntry objects to dicts for UI
        entries_dict = [
            {
                "quest_id": entry.quest_id,
                "title": entry.title,
                "status": entry.status.value,
                "current_stage_description": entry.current_stage_description,
                "is_tracked": entry.is_tracked,
            }
            for entry in quest_log_entries
        ]
        self._quest_log_ui.set_quests(entries_dict)
        logger.debug(f"Quest log refreshed with {len(entries_dict)} quests")

    def _toggle_quest_log(self) -> None:
        """Toggle quest log visibility."""
        if not self._quest:
            logger.warning("No quest system available")
            return

        self._quest_log_visible = not self._quest_log_visible

        if self._quest_log_visible:
            # Refresh quest log when opening
            self._refresh_quest_log()
            logger.info("Quest log opened")
        else:
            logger.info("Quest log closed")

    def _toggle_equipment_menu(self) -> None:
        """Toggle equipment menu visibility."""
        if not self._equipment:
            logger.warning("No equipment system available")
            return

        self._equipment_menu_visible = not self._equipment_menu_visible

        if self._equipment_menu_visible:
            # Create equipment menu UI when opening
            main_char = self._party.get_main_character()
            if not main_char:
                logger.error("No main character found in party")
                self._equipment_menu_visible = False
                return

            # Create equipment menu rect (centered, similar to shop menu)
            menu_width, menu_height = Sizes.EQUIPMENT_MENU
            menu_x = (self._screen_width - menu_width) // 2
            menu_y = (self._screen_height - menu_height) // 2
            menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)

            self._equipment_menu_ui = EquipmentMenuUI(
                rect=menu_rect,
                equipment_system=self._equipment,
                data_service=self._data_service,
                actor_id=main_char.actor_id,
                party_member=main_char,
            )
            logger.info("Equipment menu opened")
        else:
            logger.info("Equipment menu closed")

    def _debug_start_quest(self) -> None:
        """Debug functie: start een test quest (Step 7 Quest v0)."""
        if not self._quest:
            logger.warning("[DEBUG] No quest system available")
            return

        # Probeer de r1_shrine_intro quest te starten
        quest_id = "q_r1_shrine_intro"
        logger.info(f"[DEBUG] Starting quest: {quest_id}")

        try:
            state = self._quest.start_quest(quest_id)
            logger.info(f"[DEBUG] Quest started: {quest_id} (stage: {state.current_stage_id})")

            # Get stage description for feedback
            definition = self._quest.get_definition(quest_id)
            stage_desc = "Quest gestart"
            if definition and state.current_stage_id:
                for stage in definition.stages:
                    if stage.stage_id == state.current_stage_id:
                        stage_desc = stage.description
                        break

            # Refresh quest log if open
            if self._quest_log_visible:
                self._refresh_quest_log()

            # Toon feedback message
            self._feedback_message = f"Quest gestart: {stage_desc}"
            self._feedback_timer = Timing.FEEDBACK_LONG
        except ValueError as e:
            logger.warning(f"[DEBUG] Failed to start quest: {e}")
            # Check welke error het is
            if "already completed" in str(e):
                self._feedback_message = "Quest al voltooid! (zie quest log)"
            elif "already active" in str(e):
                self._feedback_message = "Quest al actief! Druk Y om te advancen"
            else:
                self._feedback_message = f"Error: {e}"
            self._feedback_timer = Timing.FEEDBACK_LONG

    def _debug_advance_quest(self) -> None:
        """Debug functie: advance een actieve quest (Step 7 Quest v0)."""
        if not self._quest:
            logger.warning("[DEBUG] No quest system available")
            return

        quest_id = "q_r1_shrine_intro"
        logger.info(f"[DEBUG] Advancing quest: {quest_id}")

        try:
            state = self._quest.advance_quest(quest_id)
            logger.info(f"[DEBUG] Quest advanced: {quest_id} (stage: {state.current_stage_id})")

            # Get stage description for feedback
            definition = self._quest.get_definition(quest_id)
            stage_desc = state.current_stage_id
            if definition and state.current_stage_id:
                for stage in definition.stages:
                    if stage.stage_id == state.current_stage_id:
                        stage_desc = stage.description
                        break

            # Refresh quest log if open
            if self._quest_log_visible:
                self._refresh_quest_log()

            # Toon feedback message
            self._feedback_message = f"Quest: {stage_desc}"
            self._feedback_timer = Timing.FEEDBACK_LONG
        except ValueError as e:
            logger.warning(f"[DEBUG] Failed to advance quest: {e}")
            self._feedback_message = "Kan niet advancen: quest niet actief"
            self._feedback_timer = Timing.FEEDBACK_LONG

    def _debug_complete_quest(self) -> None:
        """Debug functie: complete een actieve quest (Step 7 Quest v0)."""
        if not self._quest:
            logger.warning("[DEBUG] No quest system available")
            return

        quest_id = "q_r1_shrine_intro"
        logger.info(f"[DEBUG] Completing quest: {quest_id}")

        try:
            state = self._quest.complete_quest(quest_id)
            logger.info(f"[DEBUG] Quest completed: {quest_id}")

            # Refresh quest log if open
            if self._quest_log_visible:
                self._refresh_quest_log()

            # Toon feedback message
            self._feedback_message = "Quest voltooid! Beloningen ontvangen"
            self._feedback_timer = Timing.FEEDBACK_LONG
        except ValueError as e:
            logger.warning(f"[DEBUG] Failed to complete quest: {e}")
            self._feedback_message = "Kan niet voltooien: quest niet actief"
            self._feedback_timer = Timing.FEEDBACK_LONG

    def _render_dialogue(self, surface: pygame.Surface) -> None:
        """Render dialogue box."""
        if self._dialogue_box:
            self._dialogue_box.draw(surface)

    def _debug_open_shop(self) -> None:
        """Debug functie: open shop menu (Step 8 Shop v0)."""
        if not self._shop:
            logger.warning("[DEBUG] No shop system available")
            return

        # Check if in Chandrapur town
        current_zone_id = self._world.current_zone_id
        if current_zone_id != "z_r1_chandrapur_town":
            logger.info(f"[DEBUG] Shop only available in Chandrapur (current: {current_zone_id})")
            self._feedback_message = "Geen shop hier (debug: gebruik alleen in Chandrapur)"
            self._feedback_timer = Timing.FEEDBACK_DURATION
            return

        # Shop ID and chapter
        shop_id = "shop_r1_town_general"
        chapter_id = 1  # v0: hardcoded to chapter 1

        # Initialize shop menu UI if not done yet
        if not self._shop_menu_ui:
            shop_width, shop_height = Sizes.SHOP_MENU
            shop_x = (self._screen_width - shop_width) // 2
            shop_y = (self._screen_height - shop_height) // 2
            shop_rect = pygame.Rect(shop_x, shop_y, shop_width, shop_height)

            self._shop_menu_ui = ShopMenuUI(
                rect=shop_rect,
                shop_system=self._shop,
                inventory_system=self._inventory,
                data_service=self._data_service,
                shop_id=shop_id,
                chapter_id=chapter_id,
            )

        # Open shop menu
        self._shop_menu_visible = True
        logger.info(f"[DEBUG] Opened shop: {shop_id}")



__all__ = ["OverworldScene"]
