"""HUD-componenten voor overworld/battle.

De HUD is gedecoupled van de game systems. In plaats van direct systemen
aan te roepen, ontvangt de HUD data via update_stats() en rendert puur
op basis van die data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from tri_sarira_rpg.presentation.theme import (
    Colors,
    FontSizes,
    Sizes,
    Spacing,
    FONT_FAMILY,
)

from .widgets import Widget


# =============================================================================
# View Models - typed dataclasses voor HUD data
# =============================================================================


@dataclass(frozen=True)
class PartyMemberInfo:
    """UI-vriendelijke party member info."""

    name: str
    level: int
    is_main_character: bool = False


@dataclass
class HUDData:
    """Data model voor HUD state.

    De OverworldScene bouwt dit object en geeft het aan de HUD.
    De HUD rendert puur op basis van deze data, zonder kennis van systems.
    """

    # Zone/location
    zone_name: str = ""

    # Time
    time_display: str = ""

    # Party info
    party_members: list[PartyMemberInfo] = field(default_factory=list)
    party_max_size: int = 3

    # Player position
    player_x: int = 0
    player_y: int = 0

    # Feedback message (save/load notifications etc)
    feedback_message: str = ""
    feedback_visible: bool = False

    # Screen dimensions (needed for layout)
    screen_width: int = 1280
    screen_height: int = 720


# =============================================================================
# HUD Component
# =============================================================================


class HUD(Widget):
    """Container voor statusinformatie (zone, tijd, party, etc.).

    De HUD ontvangt data via update_stats() en rendert die data.
    Dit zorgt voor loose coupling met de game systems.
    """

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self._data: HUDData = HUDData()

        # Fonts
        pygame.font.init()
        self._font = pygame.font.SysFont(FONT_FAMILY, FontSizes.NORMAL)
        self._font_large = pygame.font.SysFont(FONT_FAMILY, FontSizes.XLARGE)

    def update_stats(self, data: HUDData) -> None:
        """Ontvang data van scene en sla op voor rendering.

        Parameters
        ----------
        data : HUDData
            Complete HUD state voor deze frame
        """
        self._data = data

    def draw(self, surface: pygame.Surface) -> None:
        """Render de HUD elementen."""
        self._draw_top_bar(surface)
        self._draw_party_info(surface)
        self._draw_controls_hint(surface)
        self._draw_feedback(surface)

    def _draw_top_bar(self, surface: pygame.Surface) -> None:
        """Render de top bar met zone en tijd."""
        # Draw semi-transparent background
        hud_bg = pygame.Surface((self._data.screen_width, Sizes.HUD_HEIGHT), pygame.SRCALPHA)
        hud_bg.fill(Colors.BG_HUD)
        surface.blit(hud_bg, (0, 0))

        # Zone name
        zone_text = self._font_large.render(self._data.zone_name, True, Colors.TEXT_WHITE)
        surface.blit(zone_text, (Spacing.LG, Spacing.MD))

        # Time display
        time_text = self._font.render(self._data.time_display, True, Colors.TEXT_LIGHT)
        surface.blit(time_text, (Spacing.LG, Spacing.XXXL))

    def _draw_party_info(self, surface: pygame.Surface) -> None:
        """Render party info in top-right corner."""
        HUD_RIGHT_X = self._data.screen_width - Sizes.HUD_RIGHT_OFFSET
        HUD_PARTY_START_Y = Spacing.MD
        PARTY_LINE_HEIGHT = Spacing.LG + 2
        HEADER_LINE_HEIGHT = PARTY_LINE_HEIGHT

        # Party header
        party_count = len(self._data.party_members)
        party_text = f"Party ({party_count}/{self._data.party_max_size}):"
        party_label = self._font.render(party_text, True, Colors.TEXT_LIGHT)
        surface.blit(party_label, (HUD_RIGHT_X, HUD_PARTY_START_Y))

        # Position header
        position_y = HUD_PARTY_START_Y + HEADER_LINE_HEIGHT
        pos_display = f"Position: ({self._data.player_x}, {self._data.player_y})"
        pos_text = self._font.render(pos_display, True, Colors.TEXT_LIGHT)
        surface.blit(pos_text, (HUD_RIGHT_X, position_y))

        # Party members
        y_offset = position_y + HEADER_LINE_HEIGHT
        for member in self._data.party_members:
            member_text = f"  {member.name} Lv {member.level}"
            if member.is_main_character:
                member_text += " (MC)"

            text = self._font.render(member_text, True, Colors.PARTY_LIGHT)
            surface.blit(text, (HUD_RIGHT_X, y_offset))
            y_offset += PARTY_LINE_HEIGHT

    def _draw_controls_hint(self, surface: pygame.Surface) -> None:
        """Render controls hint in bottom-right corner."""
        controls_width, controls_height = Sizes.CONTROLS_BOX
        controls_bg = pygame.Surface((controls_width, controls_height), pygame.SRCALPHA)
        controls_bg.fill(Colors.BG_HUD)
        surface.blit(
            controls_bg,
            (self._data.screen_width - controls_width, self._data.screen_height - controls_height),
        )

        controls_lines = [
            "Controls:",
            "Arrows: Move",
            "Space/E: Interact",
            "F5: Save  |  F9: Load",
            "G: Shop (debug, Chandrapur)",
            "B: Battle (debug)",
        ]
        for i, line in enumerate(controls_lines):
            text = self._font.render(line, True, Colors.TEXT_LIGHT)
            surface.blit(
                text,
                (
                    self._data.screen_width - controls_width + Spacing.SM,
                    self._data.screen_height - controls_height - Spacing.MD + i * Spacing.LG,
                ),
            )

    def _draw_feedback(self, surface: pygame.Surface) -> None:
        """Render feedback message (save/load notifications)."""
        if not self._data.feedback_visible or not self._data.feedback_message:
            return

        feedback_text = self._font_large.render(
            self._data.feedback_message, True, Colors.HIGHLIGHT
        )
        text_rect = feedback_text.get_rect(
            center=(self._data.screen_width // 2, self._data.screen_height // 2 - 100)
        )

        # Draw semi-transparent background
        padding = Spacing.LG
        bg_rect = pygame.Rect(
            text_rect.x - padding,
            text_rect.y - padding,
            text_rect.width + 2 * padding,
            text_rect.height + 2 * padding,
        )
        bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg.fill(Colors.BG_OVERLAY)
        surface.blit(bg, bg_rect.topleft)

        # Draw text
        surface.blit(feedback_text, text_rect)


__all__ = ["HUD", "HUDData", "PartyMemberInfo"]
