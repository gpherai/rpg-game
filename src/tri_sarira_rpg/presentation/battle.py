"""Battle-presentatie (Combat v0)."""

from __future__ import annotations

import logging
import random
from enum import Enum
from typing import TYPE_CHECKING

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager
from tri_sarira_rpg.presentation.theme import (
    Colors,
    FontCache,
    FontSizes,
    Sizes,
    Spacing,
    Timing,
)
from tri_sarira_rpg.presentation.ui.pause_menu import PauseMenu
from tri_sarira_rpg.systems.combat import BattleResult
from tri_sarira_rpg.systems.combat_viewmodels import (
    ActionType,
    BattleAction,
    BattleOutcome,
    BattleStateView,
    CombatantView,
)
from tri_sarira_rpg.systems.inventory import InventorySystem

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import (
        CombatSystemProtocol,
        DataRepositoryProtocol,
        GameProtocol,
        PartySystemProtocol,
    )

logger = logging.getLogger(__name__)


class BattlePhase(Enum):
    """Fasen van de battle flow."""

    START = "start"  # Battle start animatie/intro
    PLAYER_TURN = "player_turn"  # Speler kiest actie
    ENEMY_TURN = "enemy_turn"  # Enemy AI kiest actie
    EXECUTING_ACTION = "executing_action"  # Actie wordt uitgevoerd
    BATTLE_END = "battle_end"  # Battle is afgelopen (WIN/LOSE)


class MenuState(Enum):
    """States voor het action menu."""

    MAIN_MENU = "main"  # Attack/Skill/Defend/Item
    SKILL_SELECT = "skill"  # Kies skill
    TARGET_SELECT = "target"  # Kies target
    ITEM_SELECT = "item"  # Kies item


class BattleScene(Scene):
    """Visualiseert turn-based gevechten."""

    def __init__(
        self,
        manager: SceneManager,
        combat_system: CombatSystemProtocol,
        inventory_system: InventorySystem,
        data_repository: DataRepositoryProtocol,
        party_system: PartySystemProtocol,
        game_instance: GameProtocol | None = None,
    ) -> None:
        super().__init__(manager)
        self._combat = combat_system
        self._inventory = inventory_system
        self._data_repository = data_repository
        self._party = party_system
        self._game = game_instance
        self._phase = BattlePhase.START
        self._menu_state = MenuState.MAIN_MENU
        self._battle_result: BattleResult | None = None  # Stored for rendering

        # UI state
        self._selected_menu_index = 0
        self._selected_skill_index = 0
        self._selected_target_index = 0
        self._selected_item_index = 0

        # Action log
        self._action_log: list[str] = []
        self._log_display_time = 0.0

        # Fonts (via FontCache)
        self._font = FontCache.get(FontSizes.NORMAL)
        self._font_large = FontCache.get(FontSizes.XLARGE)
        self._font_small = FontCache.get(FontSizes.SMALL)

        # Colors
        self._color_bg = Colors.BG_DARK
        self._color_text = Colors.TEXT
        self._color_highlight = Colors.HIGHLIGHT
        self._color_hp = Colors.HP
        self._color_hp_low = Colors.HP_LOW
        self._color_enemy = Colors.ENEMY
        self._color_party = Colors.PARTY

        # Screen size
        screen = pygame.display.get_surface()
        if screen:
            self._screen_width, self._screen_height = screen.get_size()
        else:
            self._screen_width, self._screen_height = Sizes.SCREEN_DEFAULT

        # Initialize PauseMenu (centered on screen)
        # Note: Load is disabled during battle
        self._paused: bool = False
        pause_width, pause_height = Sizes.PAUSE_MENU
        pause_x = (self._screen_width - pause_width) // 2
        pause_y = (self._screen_height - pause_height) // 2
        pause_rect = pygame.Rect(pause_x, pause_y, pause_width, pause_height)
        self._pause_menu = PauseMenu(pause_rect, game_instance=game_instance, allow_load=False)
        # Set callback for returning to main menu
        if game_instance:
            self._pause_menu.set_main_menu_callback(game_instance.return_to_main_menu)

        logger.info("BattleScene initialized")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Verwerk skillselecties en menu-input."""
        if event.type == pygame.KEYDOWN:
            # Pause menu toggle (Esc key) - only during player turn
            if event.key == pygame.K_ESCAPE:
                if self._paused:
                    # Already paused, let pause menu handle it
                    should_close = self._pause_menu.handle_input(event.key)
                    if should_close:
                        self._paused = False
                        logger.debug("Resuming from pause menu")
                else:
                    # Not paused, open pause menu (only during player turn or battle end)
                    if self._phase in (BattlePhase.PLAYER_TURN, BattlePhase.BATTLE_END):
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

            if self._phase == BattlePhase.PLAYER_TURN:
                self._handle_player_input(event.key)
            elif self._phase == BattlePhase.BATTLE_END:
                # Any key to exit battle
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._exit_battle()

    def _handle_player_input(self, key: int) -> None:
        """Handle player input during their turn."""
        if self._menu_state == MenuState.MAIN_MENU:
            if key == pygame.K_UP or key == pygame.K_w:
                self._selected_menu_index = max(0, self._selected_menu_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self._selected_menu_index = min(3, self._selected_menu_index + 1)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm_main_menu_selection()

        elif self._menu_state == MenuState.SKILL_SELECT:
            current_actor = self._combat.get_current_actor()
            if not current_actor:
                return

            max_index = len(current_actor.skills) - 1
            if key == pygame.K_UP or key == pygame.K_w:
                self._selected_skill_index = max(0, self._selected_skill_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self._selected_skill_index = min(max_index, self._selected_skill_index + 1)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm_skill_selection()
            elif key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
                self._menu_state = MenuState.MAIN_MENU
                self._selected_skill_index = 0

        elif self._menu_state == MenuState.TARGET_SELECT:
            state = self._combat.get_battle_state_view()
            if not state:
                return

            alive_enemies = [e for e in state.enemies if e.is_alive]
            max_index = max(0, len(alive_enemies) - 1)
            self._selected_target_index = min(self._selected_target_index, max_index)

            # Vertical navigation (enemies staan onder elkaar)
            if key in (pygame.K_UP, pygame.K_w):
                self._selected_target_index = max(0, self._selected_target_index - 1)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self._selected_target_index = min(max_index, self._selected_target_index + 1)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm_target_selection()
            elif key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
                self._menu_state = MenuState.MAIN_MENU
                self._selected_target_index = 0

        elif self._menu_state == MenuState.ITEM_SELECT:
            available_items = self._inventory.get_available_items()
            max_index = max(0, len(available_items) - 1) if available_items else 0

            if key == pygame.K_UP or key == pygame.K_w:
                self._selected_item_index = max(0, self._selected_item_index - 1)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                self._selected_item_index = min(max_index, self._selected_item_index + 1)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm_item_selection()
            elif key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_q):
                self._menu_state = MenuState.MAIN_MENU
                self._selected_item_index = 0

    def _confirm_main_menu_selection(self) -> None:
        """Confirm main menu choice."""
        if self._selected_menu_index == 0:  # Attack
            self._menu_state = MenuState.TARGET_SELECT
            self._selected_target_index = 0
        elif self._selected_menu_index == 1:  # Skill
            self._menu_state = MenuState.SKILL_SELECT
            self._selected_skill_index = 0
        elif self._selected_menu_index == 2:  # Defend
            self._execute_defend_action()
        elif self._selected_menu_index == 3:  # Item
            self._menu_state = MenuState.ITEM_SELECT
            self._selected_item_index = 0

    def _confirm_skill_selection(self) -> None:
        """Confirm skill selection."""
        current_actor = self._combat.get_current_actor()
        if not current_actor or not current_actor.skills:
            return

        # Check if actor has selected skill
        if self._selected_skill_index >= len(current_actor.skills):
            return

        # Move to target selection
        self._menu_state = MenuState.TARGET_SELECT
        self._selected_target_index = 0

    def _confirm_target_selection(self) -> None:
        """Confirm target and execute action."""
        state = self._combat.get_battle_state_view()
        if not state:
            return

        current_actor = self._combat.get_current_actor()
        if not current_actor:
            return

        # Get alive enemies (is_alive is a property on CombatantView)
        alive_enemies = [e for e in state.enemies if e.is_alive]
        if not alive_enemies or self._selected_target_index >= len(alive_enemies):
            return

        target = alive_enemies[self._selected_target_index]
        target_token = target.battle_id

        # Determine action type based on previous menu state
        if self._menu_state == MenuState.TARGET_SELECT:
            if self._selected_menu_index == 0:  # Was in Attack menu
                self._execute_attack_action(current_actor, target_token)
            elif self._selected_menu_index == 1:  # Was in Skill menu
                skill_id = current_actor.skills[self._selected_skill_index]
                self._execute_skill_action(current_actor, target_token, skill_id)

    def _confirm_item_selection(self) -> None:
        """Confirm item selection and use it."""
        available_items = self._inventory.get_available_items()
        if not available_items or self._selected_item_index >= len(available_items):
            return

        item_id = available_items[self._selected_item_index]
        current_actor = self._combat.get_current_actor()
        if not current_actor:
            return

        # For v0: items always target self
        self._execute_item_action(current_actor, current_actor, item_id)

    def _execute_attack_action(self, actor: CombatantView, target_id: str) -> None:
        """Execute basic attack."""
        action = BattleAction(
            actor_id=actor.battle_id, action_type=ActionType.ATTACK, target_id=target_id
        )
        messages = self._combat.execute_action(action)
        self._add_to_log(messages)
        self._advance_turn()

    def _execute_skill_action(
        self, actor: CombatantView, target_id: str, skill_id: str
    ) -> None:
        """Execute skill."""
        action = BattleAction(
            actor_id=actor.battle_id,
            action_type=ActionType.SKILL,
            target_id=target_id,
            skill_id=skill_id,
        )
        messages = self._combat.execute_action(action)
        self._add_to_log(messages)
        self._advance_turn()

    def _execute_defend_action(self) -> None:
        """Execute defend."""
        current_actor = self._combat.get_current_actor()
        if not current_actor:
            return

        action = BattleAction(actor_id=current_actor.battle_id, action_type=ActionType.DEFEND)
        messages = self._combat.execute_action(action)
        self._add_to_log(messages)
        self._advance_turn()

    def _execute_item_action(
        self, actor: CombatantView, target: CombatantView, item_id: str
    ) -> None:
        """Execute item use."""
        # Consume item from inventory
        if self._inventory.has_item(item_id):
            self._inventory.remove_item(item_id, 1)
        else:
            logger.warning(f"Cannot use {item_id}: not in inventory")
            return

        action = BattleAction(
            actor_id=actor.battle_id,
            action_type=ActionType.ITEM,
            target_id=target.battle_id,
            item_id=item_id,
        )
        messages = self._combat.execute_action(action)
        self._add_to_log(messages)
        self._advance_turn()

    def _advance_turn(self) -> None:
        """Advance to next turn and check battle end."""
        self._combat.advance_turn()
        self._menu_state = MenuState.MAIN_MENU
        self._selected_menu_index = 0

        # Check if battle is over
        outcome = self._combat.check_battle_end()
        if outcome != BattleOutcome.ONGOING:
            self._phase = BattlePhase.BATTLE_END
            result = self._combat.get_battle_result(outcome)
            self._battle_result = result  # Store for rendering
            if outcome == BattleOutcome.WIN:
                self._add_to_log([f"Victory! Earned {result.earned_money} money"])
                for actor_id, xp in result.earned_xp.items():
                    self._add_to_log([f"{actor_id} earned {xp} XP!"])
            elif outcome == BattleOutcome.LOSE:
                self._add_to_log(["Defeat..."])
            return

        # Determine next phase
        next_actor = self._combat.get_current_actor()
        if next_actor and next_actor.is_enemy:
            self._phase = BattlePhase.ENEMY_TURN
        else:
            self._phase = BattlePhase.PLAYER_TURN

    def _execute_enemy_turn(self) -> None:
        """Simple enemy AI: just attack a random party member."""
        current_enemy = self._combat.get_current_actor()
        if not current_enemy or not current_enemy.is_enemy:
            return

        state = self._combat.get_battle_state_view()
        if not state:
            return

        # Pick a random alive party member as target (is_alive is property)
        alive_party = [p for p in state.party if p.is_alive]
        if not alive_party:
            return

        target = random.choice(alive_party)

        # For v0: enemies just use basic attack or first skill
        if current_enemy.skills:
            # Use first skill
            skill_id = current_enemy.skills[0]
            action = BattleAction(
                actor_id=current_enemy.actor_id,
                action_type=ActionType.SKILL,
                target_id=target.actor_id,
                skill_id=skill_id,
            )
        else:
            # Basic attack
            action = BattleAction(
                actor_id=current_enemy.actor_id,
                action_type=ActionType.ATTACK,
                target_id=target.actor_id,
            )

        messages = self._combat.execute_action(action)
        self._add_to_log(messages)
        self._advance_turn()

    def _add_to_log(self, messages: list[str]) -> None:
        """Add messages to action log."""
        self._action_log.extend(messages)
        # Keep only last 10 messages
        if len(self._action_log) > 10:
            self._action_log = self._action_log[-10:]
        self._log_display_time = Timing.LOG_DISPLAY

    def _exit_battle(self) -> None:
        """Exit battle and return to overworld."""
        logger.info("Exiting battle")
        # For now, just pop scene (return to previous scene)
        self.manager.pop_scene()

    def update(self, dt: float) -> None:
        """Laat het combatsysteem vooruitgaan."""
        # If paused, only update pause menu
        if self._paused:
            self._pause_menu.update(dt)
            return

        # Update log display timer
        if self._log_display_time > 0:
            self._log_display_time -= dt

        # Handle phase transitions
        if self._phase == BattlePhase.START:
            # Auto-transition to first turn
            self._phase = BattlePhase.PLAYER_TURN

        elif self._phase == BattlePhase.ENEMY_TURN:
            # Auto-execute enemy turn after brief delay
            self._execute_enemy_turn()

    def render(self, surface: pygame.Surface) -> None:
        """Teken units, UI en feedback."""
        # Clear screen
        surface.fill(self._color_bg)

        # Render battle state
        state = self._combat.get_battle_state_view()
        if state:
            self._render_party(surface, state)
            self._render_enemies(surface, state)
            self._render_action_log(surface)

            if self._phase == BattlePhase.PLAYER_TURN:
                self._render_action_menu(surface)
            elif self._phase == BattlePhase.BATTLE_END:
                self._render_battle_end(surface)

        # Render pause menu if paused
        if self._paused:
            self._pause_menu.render(surface)

    def _render_party(self, surface: pygame.Surface, state: BattleStateView) -> None:
        """Render party members."""
        y_offset = 100
        for i, member in enumerate(state.party):
            x = 50
            y = y_offset + i * 120

            # Draw name
            name_text = self._font_large.render(member.name, True, self._color_party)
            surface.blit(name_text, (x, y))

            # Draw HP bar
            hp_text = self._font.render(
                f"HP: {member.current_hp}/{member.max_hp}", True, self._color_text
            )
            surface.blit(hp_text, (x, y + 30))

            # HP bar visual
            bar_width, bar_height = Sizes.HP_BAR
            hp_ratio = member.current_hp / member.max_hp if member.max_hp > 0 else 0
            bar_color = self._color_hp if hp_ratio > 0.3 else self._color_hp_low

            pygame.draw.rect(surface, (50, 50, 50), (x, y + 50, bar_width, bar_height))
            pygame.draw.rect(surface, bar_color, (x, y + 50, int(bar_width * hp_ratio), bar_height))

            # Draw resources
            stamina_text = self._font_small.render(
                f"Stamina: {member.current_stamina}/{member.max_stamina}",
                True,
                self._color_text,
            )
            focus_text = self._font_small.render(
                f"Focus: {member.current_focus}/{member.max_focus}", True, self._color_text
            )
            prana_text = self._font_small.render(
                f"Prana: {member.current_prana}/{member.max_prana}", True, self._color_text
            )
            surface.blit(stamina_text, (x, y + 65))
            surface.blit(focus_text, (x, y + 80))
            surface.blit(prana_text, (x, y + 95))

    def _render_enemies(self, surface: pygame.Surface, state: BattleStateView) -> None:
        """Render enemies."""
        x_start = self._screen_width - 350
        y_offset = 100

        alive_enemies = [e for e in state.enemies if e.is_alive]

        for i, enemy in enumerate(alive_enemies):

            x = x_start
            y = y_offset + i * 100

            # Highlight if selected as target
            if self._menu_state == MenuState.TARGET_SELECT:
                if i == self._selected_target_index:
                    pygame.draw.rect(surface, self._color_highlight, (x - 10, y - 10, 320, 90), 3)

            # Draw name
            name_text = self._font_large.render(enemy.name, True, self._color_enemy)
            surface.blit(name_text, (x, y))

            # Draw HP
            hp_text = self._font.render(
                f"HP: {enemy.current_hp}/{enemy.max_hp}", True, self._color_text
            )
            surface.blit(hp_text, (x, y + 30))

            # HP bar
            bar_width, bar_height = Sizes.HP_BAR
            hp_ratio = enemy.current_hp / enemy.max_hp if enemy.max_hp > 0 else 0

            pygame.draw.rect(surface, (50, 50, 50), (x, y + 50, bar_width, bar_height))
            pygame.draw.rect(
                surface, self._color_hp, (x, y + 50, int(bar_width * hp_ratio), bar_height)
            )

    def _render_action_log(self, surface: pygame.Surface) -> None:
        """Render action log messages."""
        if not self._action_log:
            return

        x = 50
        y = self._screen_height - 200

        # Draw log background
        log_bg = pygame.Surface((self._screen_width - 100, 150), pygame.SRCALPHA)
        log_bg.fill((0, 0, 0, 200))
        surface.blit(log_bg, (x, y))

        # Draw messages
        for i, message in enumerate(self._action_log[-5:]):  # Last 5 messages
            text = self._font.render(message, True, self._color_text)
            surface.blit(text, (x + 10, y + 10 + i * 25))

    def _render_action_menu(self, surface: pygame.Surface) -> None:
        """Render action selection menu."""
        current_actor = self._combat.get_current_actor()
        if not current_actor or current_actor.is_enemy:
            return

        menu_x = self._screen_width // 2 - 150
        # Position menu higher to avoid overlap with action log
        menu_y = self._screen_height - 390

        # Draw menu background
        menu_bg = pygame.Surface((300, 200), pygame.SRCALPHA)
        menu_bg.fill((0, 0, 0, 220))
        surface.blit(menu_bg, (menu_x, menu_y))

        # Draw menu title
        title_text = self._font_large.render(
            f"{current_actor.name}'s Turn", True, self._color_highlight
        )
        surface.blit(title_text, (menu_x + 10, menu_y + 10))

        if self._menu_state == MenuState.MAIN_MENU:
            # Main menu options
            options = ["Attack", "Skill", "Defend", "Item"]
            for i, option in enumerate(options):
                color = (
                    self._color_highlight if i == self._selected_menu_index else self._color_text
                )
                text = self._font.render(
                    f"> {option}" if i == self._selected_menu_index else f"  {option}", True, color
                )
                surface.blit(text, (menu_x + 20, menu_y + 50 + i * 30))

        elif self._menu_state == MenuState.SKILL_SELECT:
            # Skill selection
            title = self._font.render("Select Skill:", True, self._color_text)
            surface.blit(title, (menu_x + 20, menu_y + 50))

            for i, skill_id in enumerate(current_actor.skills):
                color = (
                    self._color_highlight if i == self._selected_skill_index else self._color_text
                )
                # Get skill name from data
                skill_data = self._data_repository.get_skill(skill_id)
                skill_name = skill_data.get("name", skill_id) if skill_data else skill_id

                # Get resource cost
                cost_text = ""
                if skill_data and "resource_cost" in skill_data:
                    cost_type = skill_data["resource_cost"].get("type", "")
                    cost_amount = skill_data["resource_cost"].get("amount", 0)
                    cost_text = f" ({cost_amount} {cost_type.capitalize()})"

                display_text = (
                    f"> {skill_name}{cost_text}"
                    if i == self._selected_skill_index
                    else f"  {skill_name}{cost_text}"
                )
                text = self._font_small.render(display_text, True, color)
                surface.blit(text, (menu_x + 20, menu_y + 80 + i * 25))

        elif self._menu_state == MenuState.ITEM_SELECT:
            # Item selection
            title = self._font.render("Select Item:", True, self._color_text)
            surface.blit(title, (menu_x + 20, menu_y + 50))

            available_items = self._inventory.get_available_items()
            if not available_items:
                # No items available
                no_items_text = self._font_small.render(
                    "No items available", True, self._color_text
                )
                surface.blit(no_items_text, (menu_x + 20, menu_y + 80))
            else:
                for i, item_id in enumerate(available_items):
                    qty = self._inventory.get_quantity(item_id)
                    color = (
                        self._color_highlight
                        if i == self._selected_item_index
                        else self._color_text
                    )

                    # Get item name from data
                    item_data = self._data_repository.get_item(item_id)
                    item_name = item_data.get("name", item_id) if item_data else item_id

                    display_text = (
                        f"> {item_name} ({qty})"
                        if i == self._selected_item_index
                        else f"  {item_name} ({qty})"
                    )
                    text = self._font_small.render(display_text, True, color)
                    surface.blit(text, (menu_x + 20, menu_y + 80 + i * 25))

    def _render_battle_end(self, surface: pygame.Surface) -> None:
        """Render battle end screen with clear visual blocks."""
        if not self._battle_result:
            return

        result = self._battle_result
        outcome_text = "VICTORY!" if result.outcome == BattleOutcome.WIN else "DEFEAT..."
        outcome_color = Colors.SUCCESS if result.outcome == BattleOutcome.WIN else Colors.ERROR

        # === BLOCK 1: Outcome Header ===
        text = self._font_large.render(outcome_text, True, outcome_color)
        text_rect = text.get_rect(center=(self._screen_width // 2, 120))
        surface.blit(text, text_rect)

        y_offset = 180  # Start position for rewards/level-ups

        # === BLOCK 2: Rewards (if WIN) ===
        if result.outcome == BattleOutcome.WIN:
            # Total XP
            total_xp_text = self._font.render(
                f"Total XP: {result.total_xp}", True, self._color_text
            )
            total_xp_rect = total_xp_text.get_rect(center=(self._screen_width // 2, y_offset))
            surface.blit(total_xp_text, total_xp_rect)
            y_offset += 28

            # XP distribution per party member
            if result.earned_xp:
                for actor_id, xp in result.earned_xp.items():
                    # Get current runtime state from PartySystem (AFTER level-ups)
                    pm_state = self._party.get_member_by_actor_id(actor_id)

                    if pm_state:
                        # Use runtime level and name from PartySystem
                        current_level = pm_state.level
                        actor_name = (
                            pm_state.actor_id.replace("mc_", "").replace("comp_", "").capitalize()
                        )

                        xp_line = self._font_small.render(
                            f"{actor_name}: LV {current_level} (XP +{xp})",
                            True,
                            self._color_party,
                        )
                        xp_line_rect = xp_line.get_rect(center=(self._screen_width // 2, y_offset))
                        surface.blit(xp_line, xp_line_rect)
                        y_offset += 22
                    else:
                        logger.warning(
                            f"Cannot find party member {actor_id} in PartySystem for XP display"
                        )

            # === BLOCK 3: Level-ups ===
            if result.level_ups:
                y_offset += 20  # Extra spacing before level-up block

                # Level-up header
                level_up_header = self._font.render("LEVEL UP!", True, Colors.GOLD)
                level_up_header_rect = level_up_header.get_rect(
                    center=(self._screen_width // 2, y_offset)
                )
                surface.blit(level_up_header, level_up_header_rect)
                y_offset += 32

                # Each character's level-up
                for level_up in result.level_ups:
                    # Character name and level change
                    level_up_text = self._font_small.render(
                        f"{level_up.actor_name}: Lv {level_up.old_level} → Lv {level_up.new_level}",
                        True,
                        Colors.GOLD,
                    )
                    level_up_rect = level_up_text.get_rect(
                        center=(self._screen_width // 2, y_offset)
                    )
                    surface.blit(level_up_text, level_up_rect)
                    y_offset += 22

                    # Stat gains - split into two lines for readability
                    gains = level_up.stat_gains
                    line1_parts = []
                    line2_parts = []

                    # Line 1: HP and primary stats (6 stats max)
                    for stat, value in [
                        ("HP", gains.max_hp),
                        ("STR", gains.STR),
                        ("END", gains.END),
                        ("DEF", gains.DEF),
                        ("SPD", gains.SPD),
                        ("ACC", gains.ACC),
                    ]:
                        if value > 0:
                            line1_parts.append(f"{stat} +{value}")

                    # Line 2: Mental/spiritual stats
                    for stat, value in [
                        ("FOC", gains.FOC),
                        ("INS", gains.INS),
                        ("WILL", gains.WILL),
                        ("MAG", gains.MAG),
                        ("PRA", gains.PRA),
                        ("RES", gains.RES),
                    ]:
                        if value > 0:
                            line2_parts.append(f"{stat} +{value}")

                    # Render line 1
                    if line1_parts:
                        line1_text = self._font_small.render(
                            ", ".join(line1_parts), True, Colors.STAT_GAIN
                        )
                        line1_rect = line1_text.get_rect(center=(self._screen_width // 2, y_offset))
                        surface.blit(line1_text, line1_rect)
                        y_offset += Spacing.LG

                    # Render line 2
                    if line2_parts:
                        line2_text = self._font_small.render(
                            ", ".join(line2_parts), True, Colors.STAT_GAIN
                        )
                        line2_rect = line2_text.get_rect(center=(self._screen_width // 2, y_offset))
                        surface.blit(line2_text, line2_rect)
                        y_offset += Spacing.LG

                    y_offset += 10  # Extra spacing between characters

            # === BLOCK 4: Money ===
            if result.earned_money > 0:
                y_offset += 10
                money_text = self._font.render(
                    f"Money: {result.earned_money} gold", True, self._color_text
                )
                money_rect = money_text.get_rect(center=(self._screen_width // 2, y_offset))
                surface.blit(money_text, money_rect)
                y_offset += 30

        # === BLOCK 5: Continue Prompt (always at bottom) ===
        # Use dynamic y_offset to avoid overlap, with minimum bottom position
        prompt_y = max(y_offset + 30, self._screen_height - 60)
        prompt = self._font.render("Press SPACE to continue", True, self._color_text)
        prompt_rect = prompt.get_rect(center=(self._screen_width // 2, prompt_y))
        surface.blit(prompt, prompt_rect)


__all__ = ["BattleScene"]
