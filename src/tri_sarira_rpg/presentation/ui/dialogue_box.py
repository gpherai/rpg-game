"""UI voor dialogue."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from tri_sarira_rpg.presentation.theme import DialogueColors, FontCache, FontSizes, Spacing

from .widgets import Widget

if TYPE_CHECKING:
    from tri_sarira_rpg.systems.dialogue_viewmodels import DialogueView


class DialogueBox(Widget):
    """Toont dialooglijnen en keuzes.

    Werkt uitsluitend met DialogueView viewmodels - geen raw dicts of JSON.
    """

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect)
        self._view: DialogueView | None = None
        self._selected_choice_index: int = 0

        # Fonts (via cache)
        self._font = FontCache.get(FontSizes.NORMAL)
        self._font_speaker = FontCache.get(FontSizes.LARGE, bold=True)
        self._font_small = FontCache.get(FontSizes.SMALL)

        # Colors (via DialogueColors scheme)
        self._colors = DialogueColors()

    def set_view(self, view: DialogueView) -> None:
        """Update met een nieuw DialogueView viewmodel.

        Parameters
        ----------
        view : DialogueView
            Het viewmodel met speaker, tekst en keuzes
        """
        self._view = view
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
        if event.type != pygame.KEYDOWN or not self._view:
            return None

        choices = self._view.choices

        # Navigation
        if event.key in (pygame.K_UP, pygame.K_w):
            if choices:
                self._selected_choice_index = (self._selected_choice_index - 1) % len(choices)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            if choices:
                self._selected_choice_index = (self._selected_choice_index + 1) % len(choices)

        # Confirmation
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            if choices:
                return choices[self._selected_choice_index].choice_id

        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Render dialoogtekst en keuzes vanuit het viewmodel."""
        # Create a surface with per-pixel alpha for transparency
        box_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # Draw background with alpha
        bg_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        pygame.draw.rect(box_surface, self._colors.bg, bg_rect)
        pygame.draw.rect(box_surface, self._colors.border, bg_rect, 2)

        # Blit to main surface
        surface.blit(box_surface, self.rect.topleft)

        # Early return if no view set
        if not self._view:
            return

        # Draw speaker name
        y_offset = self.rect.top + Spacing.SM
        if self._view.speaker_id:
            speaker_surf = self._font_speaker.render(self._view.speaker_id, True, self._colors.speaker)
            surface.blit(speaker_surf, (self.rect.left + Spacing.MD, y_offset))
            y_offset += Spacing.XXL

        # Draw dialogue lines
        for line in self._view.lines:
            line_surf = self._font.render(line, True, self._colors.text)
            surface.blit(line_surf, (self.rect.left + Spacing.MD, y_offset))
            y_offset += Spacing.XL

        # Add spacing before choices
        choices = self._view.choices
        if choices:
            y_offset += Spacing.MD

        # Draw choices from ChoiceView viewmodels
        for i, choice in enumerate(choices):
            # Highlight selected choice
            color = (
                self._colors.choice_selected
                if i == self._selected_choice_index
                else self._colors.choice
            )

            # Draw choice number and text
            choice_text = f"{i + 1}. {choice.text}"
            choice_surf = self._font.render(choice_text, True, color)
            surface.blit(choice_surf, (self.rect.left + Spacing.XXL, y_offset))
            y_offset += Spacing.XL


__all__ = ["DialogueBox"]
