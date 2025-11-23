"""Combat viewmodels voor UI-friendly data representatie.

Deze module bevat immutable dataclasses die combat state representeren
voor de presentatielaag, zonder directe koppeling aan de interne
combat systeem implementatie.
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
    """Immutable view van een combatant voor de UI.

    Dit is een snapshot van de combatant state op een bepaald moment.
    is_alive is een property (geen method) voor consistente interface.
    """

    battle_id: str  # Unieke ID binnen de battle (bijv. actor_id#n)
    actor_id: str
    name: str
    level: int
    is_enemy: bool
    is_alive: bool  # Property, niet method!
    is_defending: bool
    current_hp: int
    max_hp: int
    current_stamina: int
    max_stamina: int
    current_focus: int
    max_focus: int
    current_prana: int
    max_prana: int
    skills: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TurnOrderEntry:
    """Entry in de turn order voor UI display."""

    actor_id: str
    name: str
    is_enemy: bool
    is_current: bool


@dataclass(frozen=True)
class BattleStateView:
    """Immutable view van de volledige battle state.

    Gebruikt door BattleScene voor rendering zonder directe
    toegang tot interne combat state.
    """

    party: tuple[CombatantView, ...]
    enemies: tuple[CombatantView, ...]
    turn_order: tuple[TurnOrderEntry, ...]
    current_turn_index: int
    is_battle_active: bool


@dataclass(frozen=True)
class BattleAction:
    """Een actie die uitgevoerd wordt in combat.

    Gebruikt string IDs in plaats van object references voor decoupling.
    """

    actor_id: str  # String ID, niet Combatant object
    action_type: ActionType
    target_id: str | None = None
    skill_id: str | None = None
    item_id: str | None = None


__all__ = [
    "ActionType",
    "BattleAction",
    "BattleOutcome",
    "BattleStateView",
    "CombatantView",
    "TurnOrderEntry",
]
