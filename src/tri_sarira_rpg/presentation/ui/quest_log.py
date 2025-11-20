"""UI voor quest log."""

from __future__ import annotations

import pygame

from .widgets import Widget


class QuestLogUI(Widget):
    """Toont actieve quests met status en voortgang."""

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self._quest_entries: list[dict] = []  # QuestLogEntry data
        self._selected_index: int = 0

        # Fonts
        pygame.font.init()
        self._font_title = pygame.font.SysFont("monospace", 20, bold=True)
        self._font_quest = pygame.font.SysFont("monospace", 16, bold=True)
        self._font_description = pygame.font.SysFont("monospace", 14)
        self._font_small = pygame.font.SysFont("monospace", 12)

        # Colors
        self._bg_color = (20, 20, 30, 240)  # Dark with alpha
        self._border_color = (100, 150, 200)
        self._title_color = (255, 220, 100)
        self._quest_active_color = (100, 255, 100)
        self._quest_completed_color = (150, 150, 150)
        self._quest_selected_color = (255, 255, 100)
        self._text_color = (255, 255, 255)
        self._stage_color = (200, 200, 255)

    def set_quests(self, quest_entries: list[dict]) -> None:
        """Update quest lijst.

        Parameters
        ----------
        quest_entries : list[dict]
            List van QuestLogEntry dictionaries met keys:
            - quest_id: str
            - title: str
            - status: str (QuestStatus value)
            - current_stage_description: str
            - is_tracked: bool
        """
        self._quest_entries = quest_entries
        self._selected_index = 0  # Reset selection

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events voor navigatie.

        Parameters
        ----------
        event : pygame.event.Event
            Input event
        """
        if event.type != pygame.KEYDOWN:
            return

        # Navigation
        if event.key in (pygame.K_UP, pygame.K_w):
            if self._quest_entries:
                self._selected_index = (self._selected_index - 1) % len(self._quest_entries)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            if self._quest_entries:
                self._selected_index = (self._selected_index + 1) % len(self._quest_entries)

    def draw(self, surface: pygame.Surface) -> None:
        """Render quest log."""
        # Create a surface with per-pixel alpha for transparency
        log_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # Draw background with alpha
        bg_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        pygame.draw.rect(log_surface, self._bg_color, bg_rect)
        pygame.draw.rect(log_surface, self._border_color, bg_rect, 3)

        # Blit to main surface
        surface.blit(log_surface, self.rect.topleft)

        # Draw title
        y_offset = self.rect.top + 15
        title_surf = self._font_title.render("QUEST LOG", True, self._title_color)
        title_x = self.rect.left + (self.rect.width - title_surf.get_width()) // 2
        surface.blit(title_surf, (title_x, y_offset))
        y_offset += 40

        # Draw quests
        if not self._quest_entries:
            # No quests at all
            no_quests_surf = self._font_description.render("Geen quests", True, self._text_color)
            surface.blit(no_quests_surf, (self.rect.left + 20, y_offset))
        else:
            for i, entry in enumerate(self._quest_entries):
                # Determine if this quest is selected
                is_selected = i == self._selected_index

                # Quest status color
                status = entry.get("status", "ACTIVE")
                if status == "COMPLETED":
                    quest_color = self._quest_completed_color
                else:
                    quest_color = (
                        self._quest_selected_color if is_selected else self._quest_active_color
                    )

                # Draw quest title
                title = entry.get("title", "Unknown Quest")
                prefix = "> " if is_selected else "  "
                title_text = f"{prefix}{title}"
                title_surf = self._font_quest.render(title_text, True, quest_color)
                title_x = self.rect.left + 20
                title_y = y_offset
                surface.blit(title_surf, (title_x, title_y))

                # Draw strikethrough for completed quests
                if status == "COMPLETED":
                    line_y = title_y + title_surf.get_height() // 2
                    line_start_x = title_x
                    line_end_x = title_x + title_surf.get_width()
                    pygame.draw.line(
                        surface,
                        quest_color,
                        (line_start_x, line_y),
                        (line_end_x, line_y),
                        2,  # Line thickness
                    )

                y_offset += 25

                # Draw current stage description (only for selected quest)
                if is_selected:
                    stage_desc = entry.get("current_stage_description", "")
                    if stage_desc:
                        # Wrap text if needed (simple wrap at word boundaries)
                        max_width = self.rect.width - 60
                        wrapped_lines = self._wrap_text(stage_desc, max_width)
                        for line in wrapped_lines:
                            stage_surf = self._font_description.render(
                                line, True, self._stage_color
                            )
                            surface.blit(stage_surf, (self.rect.left + 40, y_offset))
                            y_offset += 20
                    y_offset += 10  # Extra spacing after selected quest

        # Draw help text at bottom
        y_offset = self.rect.bottom - 40
        help_text = "W/S: Navigate | Q: Close"
        help_surf = self._font_small.render(help_text, True, self._text_color)
        help_x = self.rect.left + (self.rect.width - help_surf.get_width()) // 2
        surface.blit(help_surf, (help_x, y_offset))

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width.

        Parameters
        ----------
        text : str
            Text to wrap
        max_width : int
            Maximum width in pixels

        Returns
        -------
        list[str]
            List of wrapped lines
        """
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surf = self._font_description.render(test_line, True, (255, 255, 255))
            if test_surf.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [text]


__all__ = ["QuestLogUI"]
