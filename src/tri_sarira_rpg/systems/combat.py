"""Tactische gevechtslogica (Combat v0)."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .combat_viewmodels import (
    ActionType,
    BattleAction as BattleActionView,
    BattleOutcome,
    BattleStateView,
    CombatantView,
    TurnOrderEntry,
)
from .progression import LevelUpResult, ProgressionSystem, TriProfile

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import (
        DataRepositoryProtocol,
        EquipmentSystemProtocol,
        InventorySystemProtocol,
        PartySystemProtocol,
    )

logger = logging.getLogger(__name__)


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
    level_ups: list[LevelUpResult] = field(default_factory=list)  # Level-up events

    @property
    def total_xp(self) -> int:
        """Total XP distributed across all party members."""
        return sum(self.earned_xp.values()) if self.earned_xp else 0

    @property
    def xp_per_member(self) -> int:
        """XP per party member (assumes equal distribution in v0)."""
        if not self.earned_xp:
            return 0
        # In v0, all members get the same XP, so return the first value
        return next(iter(self.earned_xp.values()), 0)


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
        party_system: PartySystemProtocol,
        data_repository: DataRepositoryProtocol,
        items_system: InventorySystemProtocol | None = None,
        equipment_system: EquipmentSystemProtocol | None = None,
    ) -> None:
        self._party = party_system
        self._data_repository = data_repository
        self._items = items_system
        self._equipment = equipment_system
        self._battle_state: BattleState | None = None
        self._progression = ProgressionSystem(data_repository=data_repository)

    def start_battle(self, enemy_ids: list[str]) -> BattleState:
        """Initialiseer een battlecontext voor de gegeven enemies."""
        logger.info(f"Starting battle with enemies: {enemy_ids}")

        # Create party combatants from PartySystem
        party_combatants = []
        active_party = self._party.get_active_party()

        for member in active_party:
            actor_data = self._data_repository.get_actor(member.actor_id)
            if actor_data:
                # Use effective stats (base + gear) if equipment system available
                if self._equipment:
                    stats = self._equipment.get_effective_stats(member.actor_id)
                else:
                    stats = member.base_stats

                combatant = self._create_combatant_from_actor(
                    actor_data=actor_data,
                    level=member.level,
                    stats=stats,
                )
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

    def _create_combatant_from_actor(
        self,
        actor_data: dict[str, Any],
        level: int | None = None,
        stats: dict[str, int] | None = None,
    ) -> Combatant:
        """Create a Combatant from actor data.

        Parameters
        ----------
        actor_data : dict[str, Any]
            Actor data from repository
        level : int | None
            Override level (from PartyMember), if None uses actor_data level
        stats : dict[str, int] | None
            Override stats (effective stats with gear), if None uses actor_data base_stats
        """
        # Use provided stats or fall back to actor_data
        if stats is None:
            stats = actor_data.get("base_stats", {})
        if level is None:
            level = actor_data.get("level", 1)

        return Combatant(
            actor_id=actor_data["id"],
            name=actor_data["name"],
            level=level,
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

    def _execute_basic_attack(self, attacker: Combatant, target: Combatant | None) -> list[str]:
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
            messages.append(f"{user.name} doesn't have enough {resource_type} to use {skill_name}!")
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
        """Haal skill data op via DataRepository."""
        skill = self._data_repository.get_skill(skill_id)
        if skill is None:
            logger.warning(f"Skill {skill_id} not found in skills.json")
        return skill

    def _get_item_data(self, item_id: str) -> dict[str, Any] | None:
        """Haal item data op via DataRepository."""
        item = self._data_repository.get_item(item_id)
        if item is None:
            logger.warning(f"Item {item_id} not found in items.json")
        return item

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
        """Genereer battle result met XP rewards en level-ups."""
        if not self._battle_state:
            return BattleResult(outcome=outcome)

        # Calculate XP rewards (if WIN)
        earned_xp = {}
        earned_money = 0
        level_ups: list[LevelUpResult] = []

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

            # Process level-ups for each party member
            for party_member in self._battle_state.party:
                if not party_member.is_alive():
                    continue

                # Get actor data for tri_profile
                actor_data = self._data_repository.get_actor(party_member.actor_id)
                if not actor_data:
                    logger.warning(f"No actor data for {party_member.actor_id}, skipping level-up")
                    continue

                tri_profile_data = actor_data.get("tri_profile")
                if not tri_profile_data:
                    logger.warning(f"No tri_profile for {party_member.actor_id}, skipping level-up")
                    continue

                tri_profile = TriProfile(
                    phys_weight=tri_profile_data.get("phys_weight", 0.33),
                    ment_weight=tri_profile_data.get("ment_weight", 0.33),
                    spir_weight=tri_profile_data.get("spir_weight", 0.34),
                )

                # Get current XP from PartySystem
                pm_state = self._party.get_party_member(party_member.actor_id)
                if not pm_state:
                    continue

                current_level = pm_state.level
                current_xp = getattr(pm_state, "xp", 0)  # May not exist yet in v0

                # Collect base stats for resource calculation
                base_stats = {
                    "STR": party_member.STR,
                    "END": party_member.END,
                    "DEF": party_member.DEF,
                    "SPD": party_member.SPD,
                    "ACC": party_member.ACC,
                    "FOC": party_member.FOC,
                    "INS": party_member.INS,
                    "WILL": party_member.WILL,
                    "MAG": party_member.MAG,
                    "PRA": party_member.PRA,
                    "RES": party_member.RES,
                }

                # Apply XP and process level-ups
                new_level, new_xp, member_level_ups = self._progression.apply_xp_and_level_up(
                    actor_id=party_member.actor_id,
                    actor_name=party_member.name,
                    current_level=current_level,
                    current_xp=current_xp,
                    earned_xp=total_xp,
                    tri_profile=tri_profile,
                    base_stats=base_stats,
                )

                # If level-up occurred, update combatant and party member
                if member_level_ups:
                    level_ups.extend(member_level_ups)

                    # Apply all stat gains to combatant
                    for lvl_up in member_level_ups:
                        gains = lvl_up.stat_gains
                        party_member.STR += gains.STR
                        party_member.END += gains.END
                        party_member.DEF += gains.DEF
                        party_member.SPD += gains.SPD
                        party_member.ACC += gains.ACC
                        party_member.FOC += gains.FOC
                        party_member.INS += gains.INS
                        party_member.WILL += gains.WILL
                        party_member.MAG += gains.MAG
                        party_member.PRA += gains.PRA
                        party_member.RES += gains.RES

                        # Update max resources
                        party_member.max_hp += gains.max_hp
                        party_member.max_stamina += gains.max_stamina
                        party_member.max_focus += gains.max_focus
                        party_member.max_prana += gains.max_prana

                    # Refill HP/resources to new max (level-up heal)
                    party_member.current_hp = party_member.max_hp
                    party_member.current_stamina = party_member.max_stamina
                    party_member.current_focus = party_member.max_focus
                    party_member.current_prana = party_member.max_prana

                    # Update level in combatant
                    party_member.level = new_level

                    logger.info(
                        f"{party_member.name} leveled up to Lv {new_level}! HP fully restored."
                    )

                # Update PartySystem (persistent state)
                # Note: This assumes PartySystem has methods to update level/xp/stats
                # For v0, we may need to add these methods if they don't exist
                self._party.update_member_level(party_member.actor_id, new_level, new_xp)

                # Update PartySystem stats if level-up occurred
                if member_level_ups:
                    for lvl_up in member_level_ups:
                        self._party.apply_stat_gains(party_member.actor_id, lvl_up.stat_gains)

        result = BattleResult(
            outcome=outcome,
            earned_xp=earned_xp,
            earned_money=earned_money,
            level_ups=level_ups,
        )

        self._battle_state.result = result
        return result

    @property
    def battle_state(self) -> BattleState | None:
        """Get current battle state."""
        return self._battle_state

    # =========================================================================
    # ViewModel Methods (voor CombatSystemProtocol)
    # =========================================================================

    def _combatant_to_view(self, combatant: Combatant) -> CombatantView:
        """Convert een Combatant naar een CombatantView."""
        return CombatantView(
            actor_id=combatant.actor_id,
            name=combatant.name,
            level=combatant.level,
            is_enemy=combatant.is_enemy,
            is_alive=combatant.is_alive(),
            is_defending=combatant.is_defending,
            current_hp=combatant.current_hp,
            max_hp=combatant.max_hp,
            current_stamina=combatant.current_stamina,
            max_stamina=combatant.max_stamina,
            current_focus=combatant.current_focus,
            max_focus=combatant.max_focus,
            current_prana=combatant.current_prana,
            max_prana=combatant.max_prana,
            skills=tuple(combatant.skills),
        )

    def get_battle_state_view(self) -> BattleStateView | None:
        """Haal huidige battle state view op voor UI rendering.

        Returns een immutable view van de battle state die geschikt is
        voor de presentation layer.
        """
        if not self._battle_state:
            return None

        # Convert party members to views
        party_views = tuple(
            self._combatant_to_view(m) for m in self._battle_state.party
        )

        # Convert enemies to views
        enemy_views = tuple(
            self._combatant_to_view(e) for e in self._battle_state.enemies
        )

        # Build turn order entries
        current_actor = self.get_current_actor()
        current_actor_id = current_actor.actor_id if current_actor else None

        turn_order = tuple(
            TurnOrderEntry(
                actor_id=c.actor_id,
                name=c.name,
                is_enemy=c.is_enemy,
                is_current=(c.actor_id == current_actor_id),
                is_alive=c.is_alive(),
            )
            for c in self._battle_state.turn_order
        )

        return BattleStateView(
            party=party_views,
            enemies=enemy_views,
            turn_order=turn_order,
            current_actor_id=current_actor_id,
            outcome=self.check_battle_end(),
        )


__all__ = [
    "CombatSystem",
    "BattleAction",
    "BattleResult",
    "ActionType",
    "BattleOutcome",
    "Combatant",
]
