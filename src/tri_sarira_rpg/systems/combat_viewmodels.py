"""Combat view models voor UI-friendly data representatie.

Deze module bevat frozen dataclasses die combat data representeren
op een manier die geschikt is voor de presentation layer, zonder
directe toegang tot interne CombatSystem state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ActionType(Enum):
    """Soorten acties in combat."""

    ATTACK = "attack"
    SKILL = "skill"
    DEFEND = "defend"
    ITEM = "item"


class BattleOutcome(Enum):
    """Mogelijke uitkomsten van een battle."""

    WIN = "win"
    LOSE = "lose"
    ESCAPE = "escape"
    ONGOING = "ongoing"


@dataclass(frozen=True)
class CombatantView:
    """UI-friendly view van een combatant.

    Bevat alle data die de UI nodig heeft om een combatant te renderen,
    zonder toegang tot interne Combatant methods.
    """

    actor_id: str
    name: str
    level: int
    is_enemy: bool
    is_alive: bool
    is_defending: bool

    # HP
    current_hp: int
    max_hp: int

    # Resources
    current_stamina: int
    max_stamina: int
    current_focus: int
    max_focus: int
    current_prana: int
    max_prana: int

    # Skills (voor skill menu)
    skills: tuple[str, ...] = field(default_factory=tuple)

    @property
    def hp_ratio(self) -> float:
        """HP als ratio (0.0 - 1.0) voor HP bars."""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0

    @property
    def is_low_hp(self) -> bool:
        """True als HP onder 30% is."""
        return self.hp_ratio < 0.3


@dataclass(frozen=True)
class TurnOrderEntry:
    """Entry in de turn order voor UI weergave."""

    actor_id: str
    name: str
    is_enemy: bool
    is_current: bool
    is_alive: bool


@dataclass(frozen=True)
class BattleStateView:
    """UI-friendly view van de volledige battle state.

    Bevat alle data die BattleScene nodig heeft om de battle te renderen.
    """

    party: tuple[CombatantView, ...]
    enemies: tuple[CombatantView, ...]
    turn_order: tuple[TurnOrderEntry, ...]
    current_actor_id: str | None
    outcome: BattleOutcome = BattleOutcome.ONGOING

    @property
    def alive_party(self) -> tuple[CombatantView, ...]:
        """Alleen levende party members."""
        return tuple(m for m in self.party if m.is_alive)

    @property
    def alive_enemies(self) -> tuple[CombatantView, ...]:
        """Alleen levende enemies."""
        return tuple(e for e in self.enemies if e.is_alive)

    @property
    def current_actor(self) -> CombatantView | None:
        """De huidige actor (wiens beurt het is)."""
        if not self.current_actor_id:
            return None
        for combatant in self.party + self.enemies:
            if combatant.actor_id == self.current_actor_id:
                return combatant
        return None


@dataclass(frozen=True)
class BattleAction:
    """Een actie die uitgevoerd wordt in combat.

    Dit is een immutable versie voor de protocol interface.
    """

    actor_id: str
    action_type: ActionType
    target_id: str | None = None
    skill_id: str | None = None
    item_id: str | None = None


__all__ = [
    "ActionType",
    "BattleOutcome",
    "CombatantView",
    "TurnOrderEntry",
    "BattleStateView",
    "BattleAction",
]
