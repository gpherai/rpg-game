"""Tactische gevechtslogica (Combat v0)."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


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


@dataclass
class Combatant:
    """Een unit in combat (party member of enemy)."""

    actor_id: str  # mc_adhira, comp_rajani, en_forest_sprout, etc.
    name: str
    level: int
    is_enemy: bool

    # Stats (from actors.json / enemies.json)
    STR: int
    END: int
    DEF: int
    SPD: int = 5  # Default if not in data
    FOC: int = 5
    ACC: int = 5
    INS: int = 5
    WILL: int = 5
    MAG: int = 5
    PRA: int = 5
    RES: int = 5

    # Current resources
    current_hp: int = 0
    current_stamina: int = 0
    current_focus: int = 0
    current_prana: int = 0

    # Max resources (calculated from stats)
    max_hp: int = 0
    max_stamina: int = 0
    max_focus: int = 0
    max_prana: int = 0

    # Skills available
    skills: list[str] = field(default_factory=list)

    # Defend flag
    is_defending: bool = False

    # Status effects (v0: simple stat modifiers)
    stat_modifiers: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate max resources from stats if not already set."""
        if self.max_hp == 0:
            self.max_hp = 30 + self.END * 6
        if self.max_stamina == 0:
            self.max_stamina = 10 + self.END * 3
        if self.max_focus == 0:
            self.max_focus = 10 + self.FOC * 3
        if self.max_prana == 0:
            self.max_prana = self.PRA

        # Initialize current resources to max if not set
        if self.current_hp == 0:
            self.current_hp = self.max_hp
        if self.current_stamina == 0:
            self.current_stamina = self.max_stamina
        if self.current_focus == 0:
            self.current_focus = self.max_focus
        if self.current_prana == 0:
            self.current_prana = self.max_prana

    def is_alive(self) -> bool:
        """Check of deze combatant nog leeft."""
        return self.current_hp > 0

    def get_effective_stat(self, stat_name: str) -> int:
        """Haal stat op met modifiers."""
        base_value = getattr(self, stat_name, 0)
        modifier = self.stat_modifiers.get(stat_name, 0)
        return max(0, base_value + modifier)

    def take_damage(self, amount: int) -> int:
        """Apply damage, return actual damage taken."""
        actual_damage = min(amount, self.current_hp)
        self.current_hp -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        """Apply healing, return actual HP healed."""
        actual_heal = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual_heal
        return actual_heal

    def restore_resource(self, resource_type: str, amount: int) -> int:
        """Restore a resource (stamina/focus/prana), return actual restored."""
        if resource_type == "stamina":
            actual = min(amount, self.max_stamina - self.current_stamina)
            self.current_stamina += actual
            return actual
        elif resource_type == "focus":
            actual = min(amount, self.max_focus - self.current_focus)
            self.current_focus += actual
            return actual
        elif resource_type == "prana":
            actual = min(amount, self.max_prana - self.current_prana)
            self.current_prana += actual
            return actual
        return 0

    def consume_resource(self, resource_type: str, amount: int) -> bool:
        """Consume a resource, return True if successful."""
        if resource_type == "none":
            return True
        elif resource_type == "stamina":
            if self.current_stamina >= amount:
                self.current_stamina -= amount
                return True
        elif resource_type == "focus":
            if self.current_focus >= amount:
                self.current_focus -= amount
                return True
        elif resource_type == "prana":
            if self.current_prana >= amount:
                self.current_prana -= amount
                return True
        return False


@dataclass
class BattleAction:
    """Een actie die uitgevoerd wordt in combat."""

    actor: Combatant
    action_type: ActionType
    target: Combatant | None = None
    skill_id: str | None = None
    item_id: str | None = None


@dataclass
class BattleResult:
    """Resultaat van een battle."""

    outcome: BattleOutcome
    earned_xp: dict[str, int] = field(default_factory=dict)  # actor_id -> xp
    earned_money: int = 0
    earned_items: list[tuple[str, int]] = field(default_factory=list)  # (item_id, qty)


@dataclass
class BattleState:
    """Volledige battle state."""

    party: list[Combatant] = field(default_factory=list)
    enemies: list[Combatant] = field(default_factory=list)
    turn_order: list[Combatant] = field(default_factory=list)
    current_turn_index: int = 0
    result: BattleResult | None = None


class CombatSystem:
    """Beheert battles, turn order en skillresolutie."""

    def __init__(
        self,
        party_system: Any,
        data_repository: Any,
        items_system: Any | None = None,
    ) -> None:
        self._party = party_system
        self._data_repository = data_repository
        self._items = items_system
        self._battle_state: BattleState | None = None

    def start_battle(self, enemy_ids: list[str]) -> BattleState:
        """Initialiseer een battlecontext voor de gegeven enemies."""
        logger.info(f"Starting battle with enemies: {enemy_ids}")

        # Create party combatants from PartySystem
        party_combatants = []
        active_party = self._party.get_active_party()

        for member in active_party:
            actor_data = self._data_repository.get_actor(member.actor_id)
            if actor_data:
                combatant = self._create_combatant_from_actor(actor_data)
                party_combatants.append(combatant)
                logger.debug(
                    f"Party member: {combatant.name} (HP: {combatant.current_hp}/{combatant.max_hp})"
                )

        # Create enemy combatants
        enemy_combatants = []
        for enemy_id in enemy_ids:
            enemy_data = self._data_repository.get_enemy(enemy_id)
            if enemy_data:
                combatant = self._create_combatant_from_enemy(enemy_data)
                enemy_combatants.append(combatant)
                logger.debug(
                    f"Enemy: {combatant.name} (HP: {combatant.current_hp}/{combatant.max_hp})"
                )

        # Create turn order (simple: party first, then enemies)
        turn_order = party_combatants + enemy_combatants

        # Initialize battle state
        self._battle_state = BattleState(
            party=party_combatants,
            enemies=enemy_combatants,
            turn_order=turn_order,
            current_turn_index=0,
        )

        logger.info(f"Battle initialized: {len(party_combatants)} vs {len(enemy_combatants)}")
        return self._battle_state

    def _create_combatant_from_actor(self, actor_data: dict[str, Any]) -> Combatant:
        """Create a Combatant from actor data."""
        stats = actor_data.get("base_stats", {})
        return Combatant(
            actor_id=actor_data["id"],
            name=actor_data["name"],
            level=actor_data.get("level", 1),
            is_enemy=False,
            STR=stats.get("STR", 5),
            END=stats.get("END", 5),
            DEF=stats.get("DEF", 5),
            SPD=stats.get("SPD", 5),
            FOC=stats.get("FOC", 5),
            ACC=stats.get("ACC", 5),
            INS=stats.get("INS", 5),
            WILL=stats.get("WILL", 5),
            MAG=stats.get("MAG", 5),
            PRA=stats.get("PRA", 5),
            RES=stats.get("RES", 5),
            skills=actor_data.get("starting_skills", []),
        )

    def _create_combatant_from_enemy(self, enemy_data: dict[str, Any]) -> Combatant:
        """Create a Combatant from enemy data."""
        stats = enemy_data.get("base_stats", {})
        return Combatant(
            actor_id=enemy_data["id"],
            name=enemy_data["name"],
            level=enemy_data.get("level", 1),
            is_enemy=True,
            STR=stats.get("STR", 5),
            END=stats.get("END", 5),
            DEF=stats.get("DEF", 5),
            SPD=stats.get("SPD", 5),
            FOC=stats.get("FOC", 5),
            ACC=stats.get("ACC", 5),
            INS=stats.get("INS", 5),
            WILL=stats.get("WILL", 5),
            MAG=stats.get("MAG", 5),
            PRA=stats.get("PRA", 5),
            RES=stats.get("RES", 5),
            skills=enemy_data.get("skills", []),
        )

    def get_current_actor(self) -> Combatant | None:
        """Haal de huidige actor op (wiens beurt het is)."""
        if not self._battle_state:
            return None

        # Skip dead combatants
        while self._battle_state.current_turn_index < len(self._battle_state.turn_order):
            current = self._battle_state.turn_order[self._battle_state.current_turn_index]
            if current.is_alive():
                return current
            # Skip dead unit
            self._battle_state.current_turn_index += 1

        # End of round, reset turn order
        if self._battle_state.current_turn_index >= len(self._battle_state.turn_order):
            self._battle_state.current_turn_index = 0
            return self.get_current_actor()

        return None

    def execute_action(self, action: BattleAction) -> list[str]:
        """Voer een actie uit en retourneer feedback messages."""
        messages = []

        if action.action_type == ActionType.ATTACK:
            messages.extend(self._execute_basic_attack(action.actor, action.target))
        elif action.action_type == ActionType.SKILL:
            messages.extend(self._execute_skill(action.actor, action.target, action.skill_id))
        elif action.action_type == ActionType.DEFEND:
            messages.extend(self._execute_defend(action.actor))
        elif action.action_type == ActionType.ITEM:
            messages.extend(self._execute_item(action.actor, action.target, action.item_id))

        # Clear defend flag at end of action
        action.actor.is_defending = False

        return messages

    def _execute_basic_attack(
        self, attacker: Combatant, target: Combatant | None
    ) -> list[str]:
        """Execute a basic physical attack."""
        if not target or not target.is_alive():
            return [f"{attacker.name} attacks, but there's no target!"]

        messages = []

        # Calculate hit chance (simplified v0)
        base_hit = 80
        acc_bonus = (attacker.get_effective_stat("ACC") - target.get_effective_stat("SPD")) * 2
        hit_chance = max(20, min(95, base_hit + acc_bonus))

        # Roll for hit
        if random.randint(1, 100) > hit_chance:
            messages.append(f"{attacker.name} attacks {target.name}, but misses!")
            return messages

        # Calculate damage (Physical formula)
        raw_damage = (attacker.get_effective_stat("STR") * 1.0 + 5) - (
            target.get_effective_stat("DEF") * 0.5
        )

        # Defend reduces damage by 50%
        if target.is_defending:
            raw_damage *= 0.5
            messages.append(f"{target.name} is defending!")

        final_damage = max(1, int(raw_damage))
        actual_damage = target.take_damage(final_damage)

        messages.append(
            f"{attacker.name} attacks {target.name} for {actual_damage} damage! "
            f"(HP: {target.current_hp}/{target.max_hp})"
        )

        if not target.is_alive():
            messages.append(f"{target.name} is defeated!")

        return messages

    def _execute_skill(
        self, user: Combatant, target: Combatant | None, skill_id: str | None
    ) -> list[str]:
        """Execute a skill."""
        if not skill_id:
            return [f"{user.name} tries to use a skill, but none selected!"]

        # Load skill data
        skill_data = self._get_skill_data(skill_id)
        if not skill_data:
            return [f"{user.name} tries to use unknown skill {skill_id}!"]

        messages = []
        skill_name = skill_data.get("name", skill_id)

        # Check resource cost
        cost = skill_data.get("resource_cost", {})
        resource_type = cost.get("type", "none")
        resource_amount = cost.get("amount", 0)

        if not user.consume_resource(resource_type, resource_amount):
            messages.append(
                f"{user.name} doesn't have enough {resource_type} to use {skill_name}!"
            )
            return messages

        # Execute skill based on type
        skill_type = skill_data.get("type", "attack")
        domain = skill_data.get("domain", "Physical")
        power = skill_data.get("power", 0)
        acc_bonus = skill_data.get("accuracy_bonus", 0)

        if skill_type == "attack":
            if not target or not target.is_alive():
                return [f"{user.name} uses {skill_name}, but there's no target!"]

            # Calculate hit chance
            base_hit = 80
            stat_modifier = (user.get_effective_stat("ACC") - target.get_effective_stat("SPD")) * 2
            hit_chance = max(20, min(95, base_hit + stat_modifier + acc_bonus))

            # Roll for hit
            if random.randint(1, 100) > hit_chance:
                messages.append(f"{user.name} uses {skill_name}, but misses!")
                return messages

            # Calculate damage based on domain
            if domain == "Physical":
                raw_damage = (user.get_effective_stat("STR") * 1.0 + power) - (
                    target.get_effective_stat("DEF") * 0.5
                )
            elif domain == "Spiritual":
                raw_damage = (user.get_effective_stat("MAG") * 1.0 + power) - (
                    target.get_effective_stat("RES") * 0.5
                )
            elif domain == "Mental":
                raw_damage = (user.get_effective_stat("FOC") * 1.0 + power) - (
                    target.get_effective_stat("WILL") * 0.5
                )
            else:
                raw_damage = power

            # Defend reduces damage
            if target.is_defending:
                raw_damage *= 0.5

            final_damage = max(1, int(raw_damage))
            actual_damage = target.take_damage(final_damage)

            messages.append(
                f"{user.name} uses {skill_name} on {target.name} for {actual_damage} damage! "
                f"(HP: {target.current_hp}/{target.max_hp})"
            )

            if not target.is_alive():
                messages.append(f"{target.name} is defeated!")

        elif skill_type in ("buff", "debuff"):
            # Apply status effects
            effects = skill_data.get("effects", [])
            target_unit = target if target else user

            for effect in effects:
                effect_type = effect.get("type")
                stat = effect.get("stat")
                amount = effect.get("amount", 0)

                if effect_type == "defense_up":
                    target_unit.stat_modifiers[stat] = (
                        target_unit.stat_modifiers.get(stat, 0) + amount
                    )
                    messages.append(f"{target_unit.name}'s {stat} increased by {amount}!")
                elif effect_type == "defense_down":
                    target_unit.stat_modifiers[stat] = (
                        target_unit.stat_modifiers.get(stat, 0) - amount
                    )
                    messages.append(f"{target_unit.name}'s {stat} decreased by {amount}!")

            messages.insert(0, f"{user.name} uses {skill_name}!")

        return messages

    def _execute_defend(self, user: Combatant) -> list[str]:
        """Execute defend action."""
        user.is_defending = True
        return [f"{user.name} takes a defensive stance!"]

    def _execute_item(
        self, user: Combatant, target: Combatant | None, item_id: str | None
    ) -> list[str]:
        """Execute item usage."""
        if not item_id:
            return [f"{user.name} tries to use an item, but none selected!"]

        # Load item data
        item_data = self._get_item_data(item_id)
        if not item_data:
            return [f"{user.name} tries to use unknown item {item_id}!"]

        messages = []
        item_name = item_data.get("name", item_id)
        effect = item_data.get("effect", {})
        effect_type = effect.get("type")
        amount = effect.get("amount", 0)

        target_unit = target if target else user

        if effect_type == "heal_hp":
            actual_heal = target_unit.heal(amount)
            messages.append(
                f"{user.name} uses {item_name} on {target_unit.name}! "
                f"Restored {actual_heal} HP (HP: {target_unit.current_hp}/{target_unit.max_hp})"
            )
        elif effect_type == "restore_stamina":
            actual_restore = target_unit.restore_resource("stamina", amount)
            messages.append(
                f"{user.name} uses {item_name} on {target_unit.name}! "
                f"Restored {actual_restore} Stamina"
            )

        return messages

    def _get_skill_data(self, skill_id: str) -> dict[str, Any] | None:
        """Haal skill data op."""
        try:
            skills_data = self._data_repository._loader.load_json("skills.json")
            for skill in skills_data.get("skills", []):
                if skill.get("id") == skill_id:
                    return skill
        except Exception as e:
            logger.warning(f"Failed to load skill {skill_id}: {e}")
        return None

    def _get_item_data(self, item_id: str) -> dict[str, Any] | None:
        """Haal item data op."""
        try:
            items_data = self._data_repository._loader.load_json("items.json")
            for item in items_data.get("items", []):
                if item.get("id") == item_id:
                    return item
        except Exception as e:
            logger.warning(f"Failed to load item {item_id}: {e}")
        return None

    def advance_turn(self) -> None:
        """Ga naar de volgende beurt."""
        if self._battle_state:
            self._battle_state.current_turn_index += 1

    def check_battle_end(self) -> BattleOutcome:
        """Check of de battle is afgelopen."""
        if not self._battle_state:
            return BattleOutcome.ONGOING

        # Check if all party members dead -> LOSE
        party_alive = any(c.is_alive() for c in self._battle_state.party)
        if not party_alive:
            return BattleOutcome.LOSE

        # Check if all enemies dead -> WIN
        enemies_alive = any(c.is_alive() for c in self._battle_state.enemies)
        if not enemies_alive:
            return BattleOutcome.WIN

        return BattleOutcome.ONGOING

    def get_battle_result(self, outcome: BattleOutcome) -> BattleResult:
        """Genereer battle result met XP rewards."""
        if not self._battle_state:
            return BattleResult(outcome=outcome)

        # Calculate XP rewards (if WIN)
        earned_xp = {}
        earned_money = 0

        if outcome == BattleOutcome.WIN:
            # Sum up XP from all defeated enemies
            total_xp = 0
            for enemy in self._battle_state.enemies:
                enemy_data = self._data_repository.get_enemy(enemy.actor_id)
                if enemy_data:
                    total_xp += enemy_data.get("xp_reward", 0)
                    earned_money += random.randint(
                        enemy_data.get("money_min", 0), enemy_data.get("money_max", 0)
                    )

            # Distribute XP equally to all surviving party members
            for party_member in self._battle_state.party:
                if party_member.is_alive():
                    earned_xp[party_member.actor_id] = total_xp

            logger.info(f"Battle won! Earned {total_xp} XP per member, {earned_money} money")

        result = BattleResult(
            outcome=outcome, earned_xp=earned_xp, earned_money=earned_money
        )

        self._battle_state.result = result
        return result

    @property
    def battle_state(self) -> BattleState | None:
        """Get current battle state."""
        return self._battle_state


__all__ = ["CombatSystem", "BattleAction", "BattleResult", "ActionType", "BattleOutcome", "Combatant"]
