"""Progression & Leveling system for Tri-Śarīra RPG.

Handles XP curves, level-ups, and stat growth based on Tri-profiel.
See: docs/architecture/3.5 Progression & Leveling Spec – Tri-Śarīra RPG.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# XP Curve configuration for v0 (Lv 1-10)
# Based on formula: XP_to_next(level) = base * level^growth_factor
# Reference from spec 3.5:
# - Lv 1→2: ~30 XP
# - Lv 2→3: ~50 XP
# - Lv 5→6: ~120 XP
# - Lv 10→11: ~250 XP

XP_CURVE_V0 = {
    1: 30,  # Lv 1 → Lv 2
    2: 50,  # Lv 2 → Lv 3
    3: 70,  # Lv 3 → Lv 4
    4: 95,  # Lv 4 → Lv 5
    5: 120,  # Lv 5 → Lv 6
    6: 150,  # Lv 6 → Lv 7
    7: 180,  # Lv 7 → Lv 8
    8: 215,  # Lv 8 → Lv 9
    9: 250,  # Lv 9 → Lv 10
    10: 300,  # Lv 10 → Lv 11 (future)
}


@dataclass
class TriProfile:
    """Tri-Śarīra profile defining Body/Mind/Spirit weights."""

    phys_weight: float  # Physical (Body) weight
    ment_weight: float  # Mental (Mind) weight
    spir_weight: float  # Spiritual (Spirit) weight

    def __post_init__(self) -> None:
        """Validate that weights sum to approximately 1.0."""
        total = self.phys_weight + self.ment_weight + self.spir_weight
        if not (0.95 <= total <= 1.05):
            logger.warning(f"TriProfile weights sum to {total:.2f}, expected ~1.0")


@dataclass
class StatGains:
    """Stat gains from a level-up."""

    # Physical stats
    STR: int = 0
    END: int = 0
    DEF: int = 0
    SPD: int = 0

    # Mental stats
    ACC: int = 0
    FOC: int = 0
    INS: int = 0
    WILL: int = 0

    # Spiritual stats
    MAG: int = 0
    PRA: int = 0
    RES: int = 0

    # Derived/resource stats (calculated from base stats)
    max_hp: int = 0
    max_stamina: int = 0
    max_focus: int = 0
    max_prana: int = 0

    def __str__(self) -> str:
        """Format stat gains for display."""
        parts = []
        for stat, value in [
            ("HP", self.max_hp),
            ("STR", self.STR),
            ("END", self.END),
            ("DEF", self.DEF),
            ("SPD", self.SPD),
            ("ACC", self.ACC),
            ("FOC", self.FOC),
            ("INS", self.INS),
            ("WILL", self.WILL),
            ("MAG", self.MAG),
            ("PRA", self.PRA),
            ("RES", self.RES),
        ]:
            if value > 0:
                parts.append(f"{stat} +{value}")
        return ", ".join(parts) if parts else "no gains"


@dataclass
class LevelUpResult:
    """Result of a level-up event."""

    actor_id: str
    actor_name: str
    old_level: int
    new_level: int
    stat_gains: StatGains = field(default_factory=StatGains)
    new_skills: list[str] = field(default_factory=list)  # Future: skill unlocks


class ProgressionSystem:
    """Manages XP curves, level-ups, and stat growth."""

    def __init__(self, data_repository: Any = None) -> None:
        """Initialize progression system.

        Parameters
        ----------
        data_repository : DataRepository, optional
            For loading actor growth data (future use)
        """
        self._data_repository = data_repository

    def xp_to_next_level(self, current_level: int) -> int:
        """Calculate XP needed to reach next level.

        Parameters
        ----------
        current_level : int
            Current character level

        Returns
        -------
        int
            XP required to reach next level
        """
        return XP_CURVE_V0.get(current_level, 300)  # Default 300 for unknown levels

    def calculate_stat_gains(
        self,
        current_level: int,
        new_level: int,
        tri_profile: TriProfile,
        base_stats: dict[str, int],
    ) -> StatGains:
        """Calculate stat gains for level-up(s).

        Based on spec 3.5, section 4.2:
        - BodyGain = BodyBaseGrowth * PhysWeight
        - MindGain = MindBaseGrowth * MentWeight
        - SpiritGain = SpiritBaseGrowth * SpirWeight

        For v0, we use simplified growth rates:
        - BodyBaseGrowth = 2.5 per level
        - MindBaseGrowth = 2.5 per level
        - SpiritBaseGrowth = 2.5 per level

        Stats distribution (from spec 4.2):
        - Body → STR (40%), END (30%), DEF (20%), SPD (10%)
        - Mind → ACC (10%), FOC (40%), INS (20%), WILL (30%)
        - Spirit → MAG (40%), PRA (30%), RES (20%), DEV (10%) [DEV future]

        Parameters
        ----------
        current_level : int
            Starting level
        new_level : int
            Ending level (can be multiple levels at once)
        tri_profile : TriProfile
            Character's Tri-Śarīra profile
        base_stats : dict[str, int]
            Current base stats (for resource calculation)

        Returns
        -------
        StatGains
            Total stat gains across all levels
        """
        levels_gained = new_level - current_level
        if levels_gained <= 0:
            return StatGains()

        # Base growth per level (v0 simplified)
        # Higher values ensure meaningful stat gains even with weight distribution
        body_base_growth = 10.0
        mind_base_growth = 10.0
        spirit_base_growth = 10.0

        # Total growth across all levels
        total_body_gain = body_base_growth * levels_gained * tri_profile.phys_weight
        total_mind_gain = mind_base_growth * levels_gained * tri_profile.ment_weight
        total_spirit_gain = spirit_base_growth * levels_gained * tri_profile.spir_weight

        # Distribute to individual stats (use round() for better rounding)
        gains = StatGains(
            # Physical stats (Body domain)
            STR=round(total_body_gain * 0.4),
            END=round(total_body_gain * 0.3),
            DEF=round(total_body_gain * 0.2),
            SPD=round(total_body_gain * 0.1),
            # Mental stats (Mind domain)
            ACC=round(total_mind_gain * 0.1),
            FOC=round(total_mind_gain * 0.4),
            INS=round(total_mind_gain * 0.2),
            WILL=round(total_mind_gain * 0.3),
            # Spiritual stats (Spirit domain)
            MAG=round(total_spirit_gain * 0.4),
            PRA=round(total_spirit_gain * 0.3),
            RES=round(total_spirit_gain * 0.2),
            # DEV (Devotion) - future stat, skip for now
        )

        # Calculate resource maxima changes (based on new stats)
        # MaxHP = 30 + END * 6
        # MaxStamina = 10 + END * 3
        # MaxFocus = 10 + FOC * 3
        # MaxPrana = PRA
        old_end = base_stats.get("END", 0)
        old_foc = base_stats.get("FOC", 0)
        old_pra = base_stats.get("PRA", 0)

        new_end = old_end + gains.END
        new_foc = old_foc + gains.FOC
        new_pra = old_pra + gains.PRA

        old_max_hp = 30 + old_end * 6
        old_max_stamina = 10 + old_end * 3
        old_max_focus = 10 + old_foc * 3
        old_max_prana = old_pra

        new_max_hp = 30 + new_end * 6
        new_max_stamina = 10 + new_end * 3
        new_max_focus = 10 + new_foc * 3
        new_max_prana = new_pra

        gains.max_hp = new_max_hp - old_max_hp
        gains.max_stamina = new_max_stamina - old_max_stamina
        gains.max_focus = new_max_focus - old_max_focus
        gains.max_prana = new_max_prana - old_max_prana

        return gains

    def apply_xp_and_level_up(
        self,
        actor_id: str,
        actor_name: str,
        current_level: int,
        current_xp: int,
        earned_xp: int,
        tri_profile: TriProfile,
        base_stats: dict[str, int],
    ) -> tuple[int, int, list[LevelUpResult]]:
        """Apply earned XP and process any level-ups.

        Parameters
        ----------
        actor_id : str
            Actor ID
        actor_name : str
            Actor display name
        current_level : int
            Current level
        current_xp : int
            Current XP towards next level
        earned_xp : int
            XP earned from battle
        tri_profile : TriProfile
            Character's Tri-Śarīra profile
        base_stats : dict[str, int]
            Current base stats

        Returns
        -------
        tuple[int, int, list[LevelUpResult]]
            (new_level, remaining_xp, level_up_results)
        """
        new_xp = current_xp + earned_xp
        new_level = current_level
        level_ups: list[LevelUpResult] = []

        logger.debug(
            f"{actor_name}: {earned_xp} XP earned, total {new_xp}/{self.xp_to_next_level(current_level)}"
        )

        # Process level-ups (can be multiple in one go)
        while new_level < 10:  # v0 cap at level 10
            xp_needed = self.xp_to_next_level(new_level)
            if new_xp >= xp_needed:
                # Level up!
                old_level = new_level
                new_level += 1
                new_xp -= xp_needed

                # Calculate stat gains
                stat_gains = self.calculate_stat_gains(
                    old_level, new_level, tri_profile, base_stats
                )

                # Update base_stats for next level calculation
                base_stats = {
                    "STR": base_stats.get("STR", 0) + stat_gains.STR,
                    "END": base_stats.get("END", 0) + stat_gains.END,
                    "DEF": base_stats.get("DEF", 0) + stat_gains.DEF,
                    "SPD": base_stats.get("SPD", 0) + stat_gains.SPD,
                    "ACC": base_stats.get("ACC", 0) + stat_gains.ACC,
                    "FOC": base_stats.get("FOC", 0) + stat_gains.FOC,
                    "INS": base_stats.get("INS", 0) + stat_gains.INS,
                    "WILL": base_stats.get("WILL", 0) + stat_gains.WILL,
                    "MAG": base_stats.get("MAG", 0) + stat_gains.MAG,
                    "PRA": base_stats.get("PRA", 0) + stat_gains.PRA,
                    "RES": base_stats.get("RES", 0) + stat_gains.RES,
                }

                level_up = LevelUpResult(
                    actor_id=actor_id,
                    actor_name=actor_name,
                    old_level=old_level,
                    new_level=new_level,
                    stat_gains=stat_gains,
                )
                level_ups.append(level_up)

                logger.info(
                    f"{actor_name} leveled up! Lv {old_level} → Lv {new_level} ({stat_gains})"
                )
            else:
                # Not enough XP for next level
                break

        return (new_level, new_xp, level_ups)


__all__ = ["ProgressionSystem", "TriProfile", "StatGains", "LevelUpResult", "XP_CURVE_V0"]
