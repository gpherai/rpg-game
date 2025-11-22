"""Centrale UI theme constanten en ThemeProvider.

Dit bestand bevat alle visuele constanten voor de game UI:
- Kleuren
- Font groottes
- Spacing/padding
- Component afmetingen
- Menu color schemes (frozen dataclasses)
- Font caching
- ThemeProvider voor dependency injection

Gebruik:
    from tri_sarira_rpg.presentation.theme import Colors, FontSizes, Spacing, Sizes
    from tri_sarira_rpg.presentation.theme import MenuColors, DialogueColors, FontCache
    from tri_sarira_rpg.presentation.theme import UITheme, ThemeProviderProtocol, DefaultThemeProvider
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pygame


class Colors:
    """UI kleuren.

    Semantische namen voor consistente styling door de hele UI.
    """

    # Backgrounds
    BG_DARK = (20, 20, 30)
    BG_OVERLAY = (20, 20, 40, 240)  # Semi-transparent voor overlays
    BG_OVERLAY_LIGHT = (20, 20, 40, 220)  # Iets transparanter
    BG_HUD = (0, 0, 0, 180)  # HUD achtergrond

    # Text
    TEXT = (220, 220, 220)
    TEXT_LIGHT = (200, 200, 200)
    TEXT_WHITE = (255, 255, 255)
    TEXT_MUTED = (150, 150, 150)

    # Accents
    HIGHLIGHT = (255, 220, 100)  # Geselecteerde items, belangrijke info
    TITLE = (255, 200, 150)  # Titels en headers
    BORDER = (100, 150, 200)  # Randen van panels/boxes

    # Status kleuren
    SUCCESS = (100, 255, 100)
    ERROR = (255, 100, 100)
    WARNING = (255, 220, 50)

    # Game-specifieke kleuren
    HP = (100, 255, 100)
    HP_LOW = (255, 100, 100)
    PARTY = (150, 200, 255)
    PARTY_LIGHT = (150, 255, 150)
    ENEMY = (255, 150, 150)
    CURRENCY = (255, 220, 50)
    PRICE = (150, 255, 150)
    STAT_BONUS = (150, 255, 150)

    # Dialogue specifiek
    SPEAKER = (255, 220, 100)
    CHOICE = (200, 200, 255)
    CHOICE_SELECTED = (255, 255, 100)
    STAGE = (200, 200, 255)

    # Quest specifiek
    QUEST_ACTIVE = (100, 255, 100)
    QUEST_COMPLETED = (150, 150, 150)
    QUEST_SELECTED = (255, 255, 100)

    # Map kleuren
    TILE_WALKABLE = (100, 150, 100)
    TILE_BLOCKED = (60, 60, 60)
    TILE_GRID = (40, 40, 40)
    PORTAL = (255, 255, 0)
    CHEST = (150, 100, 50)
    PLAYER = (100, 150, 255)
    FOLLOWER = (150, 255, 150)
    FOLLOWER_DARK = (100, 200, 100)
    FOLLOWER_INDICATOR = (255, 255, 200)

    # Level up
    GOLD = (255, 215, 0)
    STAT_GAIN = (180, 180, 180)


class FontSizes:
    """Font groottes in pixels.

    Gebruik deze constanten voor consistente typography.
    """

    TINY = 12
    SMALL = 14
    NORMAL = 16
    MEDIUM = 18
    LARGE = 20
    XLARGE = 24
    TITLE = 28
    SUBTITLE = 32
    HERO = 48


class Spacing:
    """Padding en margin waarden in pixels.

    Gebruik voor consistente spacing door de UI.
    """

    XS = 5
    SM = 10
    MD = 15
    MEDIUM = 18  # Voor text line height
    LG = 20
    XL = 25
    XXL = 30
    XXXL = 40


class Sizes:
    """Component afmetingen.

    Standaard groottes voor UI elementen.
    """

    # Screen
    SCREEN_DEFAULT = (1280, 720)

    # Panels/Menus
    DIALOGUE_HEIGHT = 250
    DIALOGUE_MARGIN = 20
    QUEST_LOG = (600, 500)
    PAUSE_MENU = (500, 400)
    SHOP_MENU = (900, 600)
    EQUIPMENT_MENU = (800, 600)

    # Bars
    HP_BAR = (200, 10)

    # HUD
    HUD_HEIGHT = 60
    HUD_RIGHT_OFFSET = 280
    CONTROLS_BOX = (300, 100)

    # Menu items
    MENU_ITEM_HEIGHT = 40
    MENU_ITEM_SPACING = 25
    LIST_ITEM_HEIGHT = 25


class Timing:
    """Timing constanten in seconden.

    Voor animaties, feedback en delays.
    """

    MOVE_DELAY = 0.15
    FEEDBACK_DURATION = 2.0
    FEEDBACK_LONG = 3.0
    LOG_DISPLAY = 2.0


# Font naam (consistentie)
FONT_FAMILY = "monospace"


# =============================================================================
# Color Schemes - frozen dataclasses voor UI componenten
# =============================================================================


@dataclass(frozen=True)
class MenuColors:
    """Standaard kleurenschema voor menu overlays.

    Gebruik dit in plaats van losse color variabelen in UI componenten.
    Alle menu's (pause, shop, equipment, quest_log) gebruiken deze defaults.
    """

    bg: tuple = Colors.BG_OVERLAY
    border: tuple = Colors.BORDER
    text: tuple = Colors.TEXT
    highlight: tuple = Colors.HIGHLIGHT
    title: tuple = Colors.TITLE
    success: tuple = Colors.SUCCESS
    error: tuple = Colors.ERROR


@dataclass(frozen=True)
class DialogueColors:
    """Kleurenschema voor dialogue boxes.

    Specifieke kleuren voor dialogue UI.
    """

    bg: tuple = Colors.BG_OVERLAY_LIGHT
    border: tuple = Colors.BORDER
    text: tuple = Colors.TEXT_WHITE
    speaker: tuple = Colors.SPEAKER
    choice: tuple = Colors.CHOICE
    choice_selected: tuple = Colors.CHOICE_SELECTED


# =============================================================================
# Font Cache - vermijdt herhaalde SysFont aanroepen
# =============================================================================


class FontCache:
    """Cache voor pygame fonts.

    Voorkomt herhaalde pygame.font.SysFont() aanroepen door fonts
    te cachen op basis van (family, size, bold) key.

    Gebruik:
        font = FontCache.get(FontSizes.NORMAL)
        font_bold = FontCache.get(FontSizes.TITLE, bold=True)
    """

    _cache: dict[tuple[str, int, bool], pygame.Font] = {}
    _initialized: bool = False

    @classmethod
    def _ensure_init(cls) -> None:
        """Zorg dat pygame.font is geïnitialiseerd."""
        if not cls._initialized:
            import pygame

            pygame.font.init()
            cls._initialized = True

    @classmethod
    def get(
        cls, size: int, bold: bool = False, family: str = FONT_FAMILY
    ) -> pygame.Font:
        """Haal een gecachte font op.

        Parameters
        ----------
        size : int
            Font grootte in pixels (gebruik FontSizes constanten)
        bold : bool
            Of de font bold moet zijn
        family : str
            Font family naam (default: FONT_FAMILY)

        Returns
        -------
        pygame.Font
            Gecachte font instance
        """
        cls._ensure_init()

        key = (family, size, bold)
        if key not in cls._cache:
            import pygame

            cls._cache[key] = pygame.font.SysFont(family, size, bold=bold)

        return cls._cache[key]

    @classmethod
    def clear(cls) -> None:
        """Leeg de font cache (voor testing of hot-reload)."""
        cls._cache.clear()
        cls._initialized = False


# =============================================================================
# UITheme - composable theme object
# =============================================================================


@dataclass(frozen=True)
class UITheme:
    """Volledig UI theme met alle color schemes.

    Bundelt alle color schemes in één object dat kan worden
    doorgegeven aan UI componenten via ThemeProvider.

    Gebruik:
        theme = UITheme()  # Default theme
        theme = UITheme(name="night", menu=DarkMenuColors())  # Custom theme
    """

    name: str = "default"
    menu: MenuColors = field(default_factory=MenuColors)
    dialogue: DialogueColors = field(default_factory=DialogueColors)


# =============================================================================
# ThemeProviderProtocol - interface voor theme providers
# =============================================================================


@runtime_checkable
class ThemeProviderProtocol(Protocol):
    """Protocol voor theme providers.

    Definieert de interface die alle theme providers moeten implementeren.
    Gebruik dit type in UI componenten voor loose coupling.

    Gebruik:
        def __init__(self, theme_provider: ThemeProviderProtocol) -> None:
            self._theme = theme_provider.current_theme
            self._font = theme_provider.get_font(FontSizes.NORMAL)
    """

    @property
    def current_theme(self) -> UITheme:
        """Get the current theme."""
        ...

    def get_font(self, size: int, bold: bool = False) -> pygame.Font:
        """Get a cached font."""
        ...


# =============================================================================
# DefaultThemeProvider - concrete implementatie
# =============================================================================


class DefaultThemeProvider:
    """Standaard theme provider met font caching.

    Combineert UITheme met FontCache voor een complete theming oplossing.
    Kan worden geïnjecteerd in UI componenten voor loose coupling.

    Gebruik:
        provider = DefaultThemeProvider()
        theme = provider.current_theme
        font = provider.get_font(FontSizes.NORMAL)
    """

    def __init__(self, theme: UITheme | None = None) -> None:
        """Initialize theme provider.

        Parameters
        ----------
        theme : UITheme | None
            Custom theme to use, defaults to UITheme()
        """
        self._theme = theme or UITheme()

    @property
    def current_theme(self) -> UITheme:
        """Get the current theme."""
        return self._theme

    def set_theme(self, theme: UITheme) -> None:
        """Set a new theme."""
        self._theme = theme

    def get_font(self, size: int, bold: bool = False) -> pygame.Font:
        """Get a cached font."""
        return FontCache.get(size, bold)


__all__ = [
    "Colors",
    "FontSizes",
    "Spacing",
    "Sizes",
    "Timing",
    "FONT_FAMILY",
    "MenuColors",
    "DialogueColors",
    "FontCache",
    "UITheme",
    "ThemeProviderProtocol",
    "DefaultThemeProvider",
]
