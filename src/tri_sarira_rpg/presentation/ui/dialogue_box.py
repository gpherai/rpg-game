"""UI voor dialogue."""

from __future__ import annotations

import pygame

from .widgets import Widget


class DialogueBox(Widget):
    """Toont dialooglijnen en keuzes."""

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self._lines: list[str] = []
        self._choices: list[tuple[str, str]] = []  # (choice_id, text)
        self._speaker: str = ""
        self._selected_choice_index: int = 0

        # Fonts
        pygame.font.init()
        self._font = pygame.font.SysFont("monospace", 16)
        self._font_speaker = pygame.font.SysFont("monospace", 20, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 14)

        # Colors
        self._bg_color = (20, 20, 40, 220)  # Dark blue with alpha
        self._border_color = (100, 150, 200)
        self._text_color = (255, 255, 255)
        self._speaker_color = (255, 220, 100)
        self._choice_color = (200, 200, 255)
        self._choice_selected_color = (255, 255, 100)

    def set_content(
        self, speaker: str, lines: list[str], choices: list[tuple[str, str]]
    ) -> None:
        """Update tekst en keuzeopties.

        Parameters
        ----------
        speaker : str
            Speaker ID (will be displayed as name)
        lines : list[str]
            List of text lines to display
        choices : list[tuple[str, str]]
            List of (choice_id, text) tuples
        """
        self._speaker = speaker
        self._lines = lines
        self._choices = choices
        self._selected_choice_index = 0  # Reset selection

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input events and return selected choice_id if confirmed.

        Parameters
        ----------
        event : pygame.event.Event
            Input event

        Returns
        -------
        str | None
            choice_id if a choice was confirmed, None otherwise
        """
        if event.type != pygame.KEYDOWN:
            return None

        # Navigation
        if event.key in (pygame.K_UP, pygame.K_w):
            if self._choices:
                self._selected_choice_index = (
                    self._selected_choice_index - 1
                ) % len(self._choices)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            if self._choices:
                self._selected_choice_index = (
                    self._selected_choice_index + 1
                ) % len(self._choices)

        # Confirmation
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            if self._choices:
                choice_id, _ = self._choices[self._selected_choice_index]
                return choice_id

        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Render dialoogtekst en keuzes."""
        # Create a surface with per-pixel alpha for transparency
        box_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # Draw background with alpha
        bg_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        pygame.draw.rect(box_surface, self._bg_color, bg_rect)
        pygame.draw.rect(box_surface, self._border_color, bg_rect, 2)

        # Blit to main surface
        surface.blit(box_surface, self.rect.topleft)

        # Draw speaker name
        y_offset = self.rect.top + 10
        if self._speaker:
            speaker_surf = self._font_speaker.render(
                self._speaker, True, self._speaker_color
            )
            surface.blit(speaker_surf, (self.rect.left + 15, y_offset))
            y_offset += 30

        # Draw dialogue lines
        for line in self._lines:
            line_surf = self._font.render(line, True, self._text_color)
            surface.blit(line_surf, (self.rect.left + 15, y_offset))
            y_offset += 25

        # Add spacing before choices
        if self._choices:
            y_offset += 15

        # Draw choices
        for i, (choice_id, text) in enumerate(self._choices):
            # Highlight selected choice
            color = (
                self._choice_selected_color
                if i == self._selected_choice_index
                else self._choice_color
            )

            # Draw choice number and text
            choice_text = f"{i + 1}. {text}"
            choice_surf = self._font.render(choice_text, True, color)
            surface.blit(choice_surf, (self.rect.left + 30, y_offset))
            y_offset += 25


__all__ = ["DialogueBox"]
