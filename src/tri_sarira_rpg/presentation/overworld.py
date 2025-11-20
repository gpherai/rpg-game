"""OverworldScene - map rendering, player movement, overworld gameplay."""

from __future__ import annotations

import logging
from typing import Any

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager
from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.combat import CombatSystem
from tri_sarira_rpg.systems.dialogue import (
    DialogueContext,
    DialogueSession,
    DialogueSystem,
)
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.party import PartySystem
from tri_sarira_rpg.systems.quest import QuestSystem
from tri_sarira_rpg.systems.state import GameStateFlags
from tri_sarira_rpg.systems.time import TimeSystem
from tri_sarira_rpg.systems.world import WorldSystem
from tri_sarira_rpg.presentation.ui.dialogue_box import DialogueBox
from tri_sarira_rpg.presentation.ui.quest_log import QuestLogUI

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
        game_instance: Any = None,
    ) -> None:
        super().__init__(manager)
        self._world = world_system
        self._time = time_system
        self._party = party_system
        self._combat = combat_system
        self._inventory = inventory_system
        self._data_repository = data_repository
        self._flags = flags_system or GameStateFlags()
        self._quest = quest_system
        self._game = game_instance

        # Dialogue system and UI
        self._dialogue_system = DialogueSystem(data_repository)
        self._dialogue_session: DialogueSession | None = None
        self._dialogue_box: DialogueBox | None = None

        # Quest log UI
        self._quest_log_visible: bool = False
        self._quest_log_ui: QuestLogUI | None = None

        # Feedback message for save/load
        self._feedback_message: str = ""
        self._feedback_timer: float = 0.0

        # Get screen resolution dynamically
        screen = pygame.display.get_surface()
        if screen:
            self._screen_width, self._screen_height = screen.get_size()
        else:
            # Fallback to default resolution if no surface exists yet
            self._screen_width, self._screen_height = 1280, 720

        # Movement timing (tile-based)
        self._move_cooldown: float = 0.0
        self._move_delay: float = 0.15  # Seconds between moves

        # Camera (simple follow)
        self._camera_x: int = 0
        self._camera_y: int = 0

        # Fonts for HUD
        pygame.font.init()
        self._font = pygame.font.SysFont("monospace", 16)
        self._font_large = pygame.font.SysFont("monospace", 24)

        # Initialize DialogueBox (at bottom of screen)
        dialogue_height = 250
        dialogue_y = self._screen_height - dialogue_height - 20
        dialogue_rect = pygame.Rect(20, dialogue_y, self._screen_width - 40, dialogue_height)
        self._dialogue_box = DialogueBox(dialogue_rect)

        # Initialize QuestLogUI (centered on screen)
        quest_log_width = 600
        quest_log_height = 500
        quest_log_x = (self._screen_width - quest_log_width) // 2
        quest_log_y = (self._screen_height - quest_log_height) // 2
        quest_log_rect = pygame.Rect(quest_log_x, quest_log_y, quest_log_width, quest_log_height)
        self._quest_log_ui = QuestLogUI(quest_log_rect)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Verwerk input events."""
        if event.type == pygame.KEYDOWN:
            # If quest log is visible, route to quest log UI
            if self._quest_log_visible:
                if event.key == pygame.K_q:
                    # Toggle quest log off
                    self._quest_log_visible = False
                elif self._quest_log_ui:
                    # Route other events to quest log for navigation
                    self._quest_log_ui.handle_event(event)
                return

            # If in dialogue mode, route to dialogue box
            if self._dialogue_session:
                self._handle_dialogue_input(event)
                return

            # Quest log toggle (Q key)
            if event.key == pygame.K_q:
                self._toggle_quest_log()

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

    def update(self, dt: float) -> None:
        """Update overworld logic."""
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
        surface.fill((20, 20, 30))  # Dark blue background

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
            text = self._font_large.render("No map loaded", True, (255, 255, 255))
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
                    color = (60, 60, 60)
                else:
                    # Walkable tile: light green
                    color = (100, 150, 100)

                pygame.draw.rect(
                    surface, color, (screen_x, screen_y, tile_size, tile_size)
                )

                # Draw grid lines
                pygame.draw.rect(
                    surface,
                    (40, 40, 40),
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
                (255, 255, 0),
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
                (150, 100, 50),
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
            "N": (0, 1),   # If player faces North, follower is South
            "S": (0, -1),  # If player faces South, follower is North
            "E": (-1, 0),  # If player faces East, follower is West
            "W": (1, 0),   # If player faces West, follower is East
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
                color = (150, 255, 150)  # Light green for first follower
            else:
                color = (100, 200, 100)  # Darker green for additional followers

            pygame.draw.circle(surface, color, (center_x, center_y), radius)

            # Draw small indicator showing this is a follower
            pygame.draw.circle(
                surface, (255, 255, 200), (center_x, center_y - radius // 2), radius // 4
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

        pygame.draw.circle(surface, (100, 150, 255), (center_x, center_y), radius)

        # Draw direction indicator
        facing_offset = {
            "N": (0, -radius),
            "S": (0, radius),
            "E": (radius, 0),
            "W": (-radius, 0),
        }
        dx, dy = facing_offset.get(player.facing, (0, 0))
        pygame.draw.circle(
            surface, (255, 255, 255), (center_x + dx, center_y + dy), radius // 3
        )

    def _render_hud(self, surface: pygame.Surface) -> None:
        """Render HUD met zone info en tijd."""
        # Draw semi-transparent background for HUD
        hud_bg = pygame.Surface((self._screen_width, 60), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 180))
        surface.blit(hud_bg, (0, 0))

        # Zone name
        zone_name = self._world.get_zone_name()
        zone_text = self._font_large.render(zone_name, True, (255, 255, 255))
        surface.blit(zone_text, (20, 15))

        # Time display
        time_display = self._time.get_time_display()
        time_text = self._font.render(time_display, True, (200, 200, 200))
        surface.blit(time_text, (20, 40))

        # === TOP-RIGHT HUD: Party Info ===
        # Clean layout with clear vertical spacing to prevent overlap
        HUD_RIGHT_X = self._screen_width - 280
        HUD_PARTY_START_Y = 15
        PARTY_LINE_HEIGHT = 22  # Increased from 20 for better readability
        HEADER_LINE_HEIGHT = PARTY_LINE_HEIGHT  # Houd spacing consistent met partyregels

        active_party = self._party.get_active_party()

        # Party header
        party_text = f"Party ({len(active_party)}/{self._party.party_max_size}):"
        party_label = self._font.render(party_text, True, (200, 200, 200))
        surface.blit(party_label, (HUD_RIGHT_X, HUD_PARTY_START_Y))

        # Position header direct onder Party
        position_y = HUD_PARTY_START_Y + HEADER_LINE_HEIGHT
        player = self._world.player
        pos_display = (
            f"Position: ({player.position.x}, {player.position.y})"
            if player
            else "Position: -"
        )
        pos_text = self._font.render(pos_display, True, (200, 200, 200))
        surface.blit(pos_text, (HUD_RIGHT_X, position_y))

        # Party members - each on their own line with runtime levels, onder de headers
        y_offset = position_y + HEADER_LINE_HEIGHT
        for member in active_party:
            # Use runtime level from PartyMember (already updated after battles)
            actor_name = member.actor_id.replace("mc_", "").replace("comp_", "").capitalize()
            member_text = f"  {actor_name} Lv {member.level}"
            if member.is_main_character:
                member_text += " (MC)"

            text = self._font.render(member_text, True, (150, 200, 150))
            surface.blit(text, (HUD_RIGHT_X, y_offset))
            y_offset += PARTY_LINE_HEIGHT

        # Controls hint
        controls_bg = pygame.Surface((300, 100), pygame.SRCALPHA)
        controls_bg.fill((0, 0, 0, 180))
        surface.blit(controls_bg, (self._screen_width - 300, self._screen_height - 100))

        controls_lines = [
            "Controls:",
            "Arrows: Move",
            "Space/E: Interact",
            "F5: Save  |  F9: Load",
            "J: Toggle Rajani (debug)",
            "B: Start Battle (debug)",
        ]
        for i, line in enumerate(controls_lines):
            text = self._font.render(line, True, (200, 200, 200))
            surface.blit(text, (self._screen_width - 290, self._screen_height - 115 + i * 20))

        # Feedback message (save/load notifications)
        if self._feedback_timer > 0:
            feedback_text = self._font_large.render(
                self._feedback_message, True, (255, 255, 100)
            )
            text_rect = feedback_text.get_rect(
                center=(self._screen_width // 2, self._screen_height // 2 - 100)
            )

            # Draw semi-transparent background
            padding = 20
            bg_rect = pygame.Rect(
                text_rect.x - padding,
                text_rect.y - padding,
                text_rect.width + 2 * padding,
                text_rect.height + 2 * padding,
            )
            bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 200))
            surface.blit(bg, bg_rect.topleft)

            # Draw text
            surface.blit(feedback_text, text_rect)

    def _quick_save(self) -> None:
        """Quick save to slot 1 (S key)."""
        if not self._game:
            logger.warning("Cannot save: no game instance available")
            return

        success = self._game.save_game(slot_id=1)

        if success:
            self._feedback_message = "Game saved!"
            self._feedback_timer = 2.0
        else:
            self._feedback_message = "Save failed!"
            self._feedback_timer = 2.0

    def _quick_load(self) -> None:
        """Quick load from slot 1 (L key)."""
        if not self._game:
            logger.warning("Cannot load: no game instance available")
            return

        success = self._game.load_game(slot_id=1)

        if success:
            self._feedback_message = "Game loaded!"
            self._feedback_timer = 2.0
        else:
            self._feedback_message = "Load failed - no save found!"
            self._feedback_timer = 2.0

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
            self.manager, self._combat, self._inventory, self._data_repository
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
            logger.info(f"Quest log opened")
        else:
            logger.info("Quest log closed")

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

            # Refresh quest log if open
            if self._quest_log_visible:
                self._refresh_quest_log()

            # Toon feedback message
            self._feedback_message = f"Quest gestart: {state.current_stage_id}"
            self._feedback_timer = 3.0
        except ValueError as e:
            logger.warning(f"[DEBUG] Failed to start quest: {e}")
            # Check welke error het is
            if "already completed" in str(e):
                self._feedback_message = "Quest al voltooid! (zie quest log)"
            elif "already active" in str(e):
                self._feedback_message = "Quest al actief! Druk Y om te advancen"
            else:
                self._feedback_message = f"Error: {e}"
            self._feedback_timer = 3.0

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

            # Refresh quest log if open
            if self._quest_log_visible:
                self._refresh_quest_log()

            # Toon feedback message
            self._feedback_message = f"Quest advanced naar: {state.current_stage_id}"
            self._feedback_timer = 3.0
        except ValueError as e:
            logger.warning(f"[DEBUG] Failed to advance quest: {e}")
            self._feedback_message = f"Kan niet advancen: quest niet actief"
            self._feedback_timer = 3.0

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
            self._feedback_message = f"Quest voltooid! Beloningen ontvangen"
            self._feedback_timer = 3.0
        except ValueError as e:
            logger.warning(f"[DEBUG] Failed to complete quest: {e}")
            self._feedback_message = f"Kan niet voltooien: quest niet actief"
            self._feedback_timer = 3.0

    def _render_dialogue(self, surface: pygame.Surface) -> None:
        """Render dialogue box."""
        if self._dialogue_box:
            self._dialogue_box.draw(surface)


__all__ = ["OverworldScene"]
