"""Protocol definitions voor loose coupling tussen systems.

Deze module definieert abstracte interfaces (Protocols) voor alle game systems.
Hierdoor kunnen systems naar interfaces programmeren ipv concrete implementaties,
wat tight coupling voorkomt en testing vereenvoudigt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from tri_sarira_rpg.systems.combat_viewmodels import (
        BattleAction,
        BattleOutcome,
        BattleStateView,
        CombatantView,
    )
    from tri_sarira_rpg.systems.equipment import EquipResult
    from tri_sarira_rpg.systems.progression import StatGains
    from tri_sarira_rpg.systems.quest import QuestDefinition, QuestLogEntry, QuestState
    from tri_sarira_rpg.systems.shop import BuyResult, ShopDefinition, ShopInventoryEntry


# =============================================================================
# Base Protocol voor Saveable Systems
# =============================================================================


@runtime_checkable
class SaveableSystem(Protocol):
    """Protocol voor systems die save/load ondersteunen."""

    def get_save_state(self) -> dict[str, Any] | list[Any]:
        """Haal serializable state op voor saving."""
        ...

    def restore_from_save(self, state: dict[str, Any] | list[Any]) -> None:
        """Herstel state vanuit save data."""
        ...


# =============================================================================
# Party System Protocol
# =============================================================================


class PartyMemberProtocol(Protocol):
    """Protocol voor party member data."""

    @property
    def npc_id(self) -> str:
        ...

    @property
    def actor_id(self) -> str:
        ...

    @property
    def is_main_character(self) -> bool:
        ...

    @property
    def level(self) -> int:
        ...

    @property
    def xp(self) -> int:
        ...

    @property
    def base_stats(self) -> dict[str, int]:
        ...


@runtime_checkable
class PartySystemProtocol(SaveableSystem, Protocol):
    """Protocol voor PartySystem interface."""

    def get_active_party(self) -> list[PartyMemberProtocol]:
        """Haal actieve party members op."""
        ...

    def get_main_character(self) -> PartyMemberProtocol | None:
        """Haal de main character op."""
        ...

    def get_party_member(self, actor_id: str) -> PartyMemberProtocol | None:
        """Haal party member op via actor_id."""
        ...

    def get_member_by_actor_id(self, actor_id: str) -> PartyMemberProtocol | None:
        """Alias voor get_party_member."""
        ...

    def is_in_party(self, npc_id: str) -> bool:
        """Check of NPC in active party zit."""
        ...

    def is_in_active_party(self, npc_id: str) -> bool:
        """Alias voor is_in_party."""
        ...

    def update_member_level(self, actor_id: str, new_level: int, new_xp: int) -> None:
        """Update level en XP van een party member."""
        ...

    def apply_stat_gains(self, actor_id: str, stat_gains: StatGains) -> None:
        """Pas stat gains toe op een party member."""
        ...

    @property
    def party_max_size(self) -> int:
        """Maximum party size."""
        ...


# =============================================================================
# Data Repository Protocol
# =============================================================================


@runtime_checkable
class DataRepositoryProtocol(Protocol):
    """Protocol voor DataRepository interface."""

    def get_actor(self, actor_id: str) -> dict[str, Any] | None:
        """Haal actor definitie op."""
        ...

    def get_enemy(self, enemy_id: str) -> dict[str, Any] | None:
        """Haal enemy definitie op."""
        ...

    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Haal skill definitie op."""
        ...

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        """Haal item definitie op."""
        ...

    def get_dialogue(self, dialogue_id: str) -> dict[str, Any] | None:
        """Haal dialogue graph op."""
        ...

    def get_quest(self, quest_id: str) -> dict[str, Any] | None:
        """Haal quest definitie op."""
        ...

    def get_all_quests(self) -> list[dict[str, Any]]:
        """Haal alle quest definities op."""
        ...

    def get_shop(self, shop_id: str) -> dict[str, Any] | None:
        """Haal shop definitie op."""
        ...

    def get_npc_meta(self) -> dict[str, Any]:
        """Haal NPC metadata op."""
        ...


# =============================================================================
# Inventory System Protocol
# =============================================================================


@runtime_checkable
class InventorySystemProtocol(SaveableSystem, Protocol):
    """Protocol voor InventorySystem interface."""

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        """Voeg item toe aan inventory."""
        ...

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Verwijder item uit inventory."""
        ...

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check of item in inventory zit."""
        ...

    def get_quantity(self, item_id: str) -> int:
        """Haal aantal van item op."""
        ...

    def get_available_items(self) -> list[str]:
        """Haal lijst van beschikbare items op."""
        ...


# =============================================================================
# Time System Protocol
# =============================================================================


@runtime_checkable
class TimeSystemProtocol(SaveableSystem, Protocol):
    """Protocol voor TimeSystem interface."""

    def update(self, dt: float) -> None:
        """Update time met delta time."""
        ...

    def get_time_display(self) -> str:
        """Haal display string voor huidige tijd op."""
        ...

    def on_player_step(self) -> None:
        """Callback wanneer speler een stap zet."""
        ...


# =============================================================================
# World System Protocol
# =============================================================================


@runtime_checkable
class WorldSystemProtocol(SaveableSystem, Protocol):
    """Protocol voor WorldSystem interface."""

    @property
    def current_zone_id(self) -> str:
        """Huidige zone ID."""
        ...

    def get_zone_name(self) -> str:
        """Haal display naam van huidige zone op."""
        ...

    def move_player(self, dx: int, dy: int) -> bool:
        """Verplaats speler, return True als beweging succesvol."""
        ...

    def interact(self) -> None:
        """Interacteer met object voor speler."""
        ...


# =============================================================================
# Flags System Protocol
# =============================================================================


@runtime_checkable
class FlagsSystemProtocol(SaveableSystem, Protocol):
    """Protocol voor GameStateFlags interface."""

    def has_flag(self, flag_id: str) -> bool:
        """Check of flag gezet is."""
        ...

    def set_flag(self, flag_id: str) -> None:
        """Zet een flag."""
        ...

    def clear_flag(self, flag_id: str) -> None:
        """Verwijder een flag."""
        ...


# =============================================================================
# Quest System Protocol
# =============================================================================


@runtime_checkable
class QuestSystemProtocol(SaveableSystem, Protocol):
    """Protocol voor QuestSystem interface."""

    def start_quest(self, quest_id: str) -> QuestState:
        """Start een quest."""
        ...

    def advance_quest(self, quest_id: str, next_stage_id: str | None = None) -> QuestState:
        """Advance quest naar volgende stage."""
        ...

    def complete_quest(self, quest_id: str) -> QuestState:
        """Markeer quest als voltooid."""
        ...

    def get_definition(self, quest_id: str) -> QuestDefinition | None:
        """Haal quest definitie op."""
        ...

    def build_quest_log_view(self) -> list[QuestLogEntry]:
        """Bouw quest log view voor UI."""
        ...


# =============================================================================
# Shop System Protocol
# =============================================================================


@runtime_checkable
class ShopSystemProtocol(SaveableSystem, Protocol):
    """Protocol voor ShopSystem interface."""

    def get_currency(self) -> int:
        """Haal huidige currency op."""
        ...

    def get_shop_definition(self, shop_id: str) -> ShopDefinition | None:
        """Haal shop definitie op."""
        ...

    def get_available_items(self, shop_id: str, chapter_id: int = 1) -> list[ShopInventoryEntry]:
        """Haal beschikbare items voor shop op."""
        ...

    def buy_item(self, shop_id: str, item_id: str, quantity: int = 1) -> BuyResult:
        """Koop item uit shop."""
        ...


# =============================================================================
# Equipment System Protocol
# =============================================================================


@runtime_checkable
class EquipmentSystemProtocol(Protocol):
    """Protocol voor EquipmentSystem interface."""

    def get_effective_stats(self, actor_id: str) -> dict[str, int]:
        """Haal effective stats op (base + gear bonuses)."""
        ...

    def get_all_equipped_gear(self, actor_id: str) -> dict[str, str | None]:
        """Haal alle equipped gear op voor actor."""
        ...

    def get_available_gear_for_slot(self, slot: str) -> list[str]:
        """Haal beschikbare gear voor slot op."""
        ...

    def equip_gear(self, actor_id: str, item_id: str, slot: str) -> EquipResult:
        """Equip gear in slot."""
        ...

    def unequip_gear(self, actor_id: str, slot: str) -> EquipResult:
        """Unequip gear uit slot."""
        ...


# =============================================================================
# Combat System Protocol
# =============================================================================


@runtime_checkable
class CombatSystemProtocol(Protocol):
    """Protocol voor CombatSystem interface.

    Definieert de methods die presentation layer nodig heeft voor battle rendering
    en interactie, zonder directe toegang tot interne CombatSystem state.
    """

    def start_battle(self, enemy_ids: list[str]) -> BattleStateView:
        """Start een battle met de gegeven enemies."""
        ...

    def get_battle_state_view(self) -> BattleStateView | None:
        """Haal huidige battle state view op voor UI rendering."""
        ...

    def get_current_actor(self) -> CombatantView | None:
        """Haal de huidige actor op (wiens beurt het is)."""
        ...

    def execute_action(self, action: BattleAction) -> list[str]:
        """Voer een actie uit en retourneer feedback messages."""
        ...

    def advance_turn(self) -> None:
        """Ga naar de volgende beurt."""
        ...

    def check_battle_end(self) -> BattleOutcome:
        """Check of de battle is afgelopen."""
        ...


# =============================================================================
# Economy System Protocol (placeholder)
# =============================================================================


@runtime_checkable
class EconomySystemProtocol(Protocol):
    """Protocol voor EconomySystem interface (nog niet volledig geïmplementeerd)."""

    def modify_currency(self, amount: int) -> None:
        """Wijzig currency met amount (kan negatief zijn)."""
        ...


# =============================================================================
# Game Protocol
# =============================================================================


@runtime_checkable
class GameProtocol(Protocol):
    """Protocol voor Game class interface.

    Definieert de methods die presentation layer nodig heeft van de Game class,
    zonder directe dependency op de concrete Game implementatie.
    """

    def save_game(self, slot_id: int = 1) -> bool:
        """Save game naar opgegeven slot."""
        ...

    def load_game(self, slot_id: int = 1) -> bool:
        """Load game van opgegeven slot."""
        ...

    def return_to_main_menu(self) -> None:
        """Keer terug naar main menu."""
        ...

    def start_overworld(self) -> None:
        """Start/herstart overworld scene."""
        ...

    def start_new_game(self) -> None:
        """Start een nieuw spel."""
        ...


__all__ = [
    "SaveableSystem",
    "PartyMemberProtocol",
    "PartySystemProtocol",
    "DataRepositoryProtocol",
    "InventorySystemProtocol",
    "TimeSystemProtocol",
    "WorldSystemProtocol",
    "FlagsSystemProtocol",
    "QuestSystemProtocol",
    "ShopSystemProtocol",
    "EquipmentSystemProtocol",
    "CombatSystemProtocol",
    "EconomySystemProtocol",
    "GameProtocol",
]
