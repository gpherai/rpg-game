"""GameDataService - Facade voor UI-vriendelijke data access.

Deze service biedt een clean interface tussen de presentation layer en de data layer.
In plaats van dat UI componenten direct met DataRepository praten en raw dicts krijgen,
kunnen ze via deze service typed view models opvragen.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import DataRepositoryProtocol

logger = logging.getLogger(__name__)


# =============================================================================
# View Models - typed dataclasses voor UI rendering
# =============================================================================


@dataclass(frozen=True)
class ItemDisplayInfo:
    """UI-vriendelijke item info."""

    item_id: str
    name: str
    item_type: str
    category: str
    description: str
    stat_mods: dict[str, int]

    @property
    def display_name(self) -> str:
        """Formatted display naam."""
        return self.name

    @property
    def stat_summary(self) -> str:
        """Samenvatting van stat modifiers voor UI."""
        if not self.stat_mods:
            return ""
        parts = [f"+{v} {k}" for k, v in self.stat_mods.items()]
        return ", ".join(parts)


@dataclass(frozen=True)
class SkillDisplayInfo:
    """UI-vriendelijke skill info."""

    skill_id: str
    name: str
    domain: str
    skill_type: str
    power: int
    resource_type: str
    resource_cost: int
    description: str

    @property
    def cost_text(self) -> str:
        """Formatted resource cost voor UI."""
        if self.resource_type == "none" or self.resource_cost == 0:
            return ""
        return f"{self.resource_cost} {self.resource_type.capitalize()}"


@dataclass(frozen=True)
class EnemyDisplayInfo:
    """UI-vriendelijke enemy info."""

    enemy_id: str
    name: str
    level: int
    enemy_type: str


# =============================================================================
# GameDataService - Main facade
# =============================================================================


class GameDataService:
    """Facade voor UI-vriendelijke game data access.

    Biedt typed view models in plaats van raw dicts, zodat de UI layer
    geen kennis nodig heeft van de data structure.
    """

    def __init__(self, data_repository: DataRepositoryProtocol) -> None:
        """Initialize service.

        Parameters
        ----------
        data_repository : DataRepositoryProtocol
            Underlying data repository
        """
        self._repository = data_repository

    # -------------------------------------------------------------------------
    # Item Methods
    # -------------------------------------------------------------------------

    def get_item_info(self, item_id: str) -> ItemDisplayInfo | None:
        """Haal item display info op.

        Parameters
        ----------
        item_id : str
            Item ID

        Returns
        -------
        ItemDisplayInfo | None
            Item info, of None als niet gevonden
        """
        item_data = self._repository.get_item(item_id)
        if not item_data:
            return None

        return ItemDisplayInfo(
            item_id=item_id,
            name=item_data.get("name", item_id),
            item_type=item_data.get("type", "unknown"),
            category=item_data.get("category", "misc"),
            description=item_data.get("description", ""),
            stat_mods=item_data.get("stat_mods", {}),
        )

    def get_item_name(self, item_id: str) -> str:
        """Haal alleen item naam op (convenience method).

        Parameters
        ----------
        item_id : str
            Item ID

        Returns
        -------
        str
            Item naam, of item_id als fallback
        """
        item_data = self._repository.get_item(item_id)
        if item_data:
            return item_data.get("name", item_id)
        return item_id

    # -------------------------------------------------------------------------
    # Skill Methods
    # -------------------------------------------------------------------------

    def get_skill_info(self, skill_id: str) -> SkillDisplayInfo | None:
        """Haal skill display info op.

        Parameters
        ----------
        skill_id : str
            Skill ID

        Returns
        -------
        SkillDisplayInfo | None
            Skill info, of None als niet gevonden
        """
        skill_data = self._repository.get_skill(skill_id)
        if not skill_data:
            return None

        resource_cost = skill_data.get("resource_cost", {})

        return SkillDisplayInfo(
            skill_id=skill_id,
            name=skill_data.get("name", skill_id),
            domain=skill_data.get("domain", "Physical"),
            skill_type=skill_data.get("type", "attack"),
            power=skill_data.get("power", 0),
            resource_type=resource_cost.get("type", "none"),
            resource_cost=resource_cost.get("amount", 0),
            description=skill_data.get("description", ""),
        )

    def get_skill_name(self, skill_id: str) -> str:
        """Haal alleen skill naam op (convenience method).

        Parameters
        ----------
        skill_id : str
            Skill ID

        Returns
        -------
        str
            Skill naam, of skill_id als fallback
        """
        skill_data = self._repository.get_skill(skill_id)
        if skill_data:
            return skill_data.get("name", skill_id)
        return skill_id

    # -------------------------------------------------------------------------
    # Enemy Methods
    # -------------------------------------------------------------------------

    def get_enemy_info(self, enemy_id: str) -> EnemyDisplayInfo | None:
        """Haal enemy display info op.

        Parameters
        ----------
        enemy_id : str
            Enemy ID

        Returns
        -------
        EnemyDisplayInfo | None
            Enemy info, of None als niet gevonden
        """
        enemy_data = self._repository.get_enemy(enemy_id)
        if not enemy_data:
            return None

        return EnemyDisplayInfo(
            enemy_id=enemy_id,
            name=enemy_data.get("name", enemy_id),
            level=enemy_data.get("level", 1),
            enemy_type=enemy_data.get("type", "normal"),
        )


__all__ = [
    "GameDataService",
    "ItemDisplayInfo",
    "SkillDisplayInfo",
    "EnemyDisplayInfo",
]
