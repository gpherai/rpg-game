"""Partybeheer en companion-lifecycle volgens 3.3 NPC & Party System Spec."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PartyMember:
    """Een actief party-lid (protagonist of companion)."""

    npc_id: str
    actor_id: str
    is_main_character: bool = False
    is_guest: bool = False
    tier: str | None = None


@dataclass
class PartyState:
    """Volledige party state: active + reserve."""

    active_party: list[PartyMember] = field(default_factory=list)
    reserve_pool: list[PartyMember] = field(default_factory=list)
    party_max_size: int = 2  # Voor Step 4 v0: 1 MC + 1 companion


class PartySystem:
    """Houdt bij wie actief is, welke companions beschikbaar zijn en hun stats.

    Voor Step 4 v0:
    - Main character (Adhira) altijd in active_party
    - Max party size = 2 (MC + 1 companion)
    - Rajani als recruitable companion
    - Geen savegame integratie (in-memory only)
    """

    def __init__(self, data_repository: Any | None = None, npc_meta: dict[str, Any] | None = None) -> None:
        """Initialize PartySystem op basis van npc_meta data.

        Parameters
        ----------
        data_repository : Any | None
            Data repository voor actors/enemies (optional voor nu)
        npc_meta : dict[str, Any] | None
            NPC metadata (npc_meta.json). Als None, gebruik defaults.
        """
        self._data_repository = data_repository
        self._state = PartyState()

        # Init op basis van npc_meta
        if npc_meta:
            self._init_from_npc_meta(npc_meta)
        else:
            # Fallback: alleen MC in party
            logger.warning("PartySystem initialized without npc_meta, adding only MC")
            mc = PartyMember(
                npc_id="npc_mc_adhira",
                actor_id="mc_adhira",
                is_main_character=True,
                tier="S"
            )
            self._state.active_party.append(mc)

        logger.info(f"PartySystem initialized: {len(self._state.active_party)} active, {len(self._state.reserve_pool)} reserve")

    def _init_from_npc_meta(self, npc_meta: dict[str, Any]) -> None:
        """Initialize party state op basis van npc_meta.json."""
        npcs = npc_meta.get("npcs", [])

        for npc_data in npcs:
            npc_id = npc_data["npc_id"]
            actor_id = npc_data["actor_id"]
            tier = npc_data.get("tier")
            is_main = npc_data.get("is_main_character", False)
            flags = npc_data.get("companion_flags", {})

            # Check wat de initial state moet zijn
            recruited = flags.get("recruited", False)
            in_party = flags.get("in_party", False)
            in_reserve = flags.get("in_reserve_pool", False)
            is_guest = flags.get("guest_only", False)

            if not recruited:
                # Nog niet gerekruteerd -> skip voor nu
                logger.debug(f"NPC {npc_id} not recruited yet, skipping")
                continue

            member = PartyMember(
                npc_id=npc_id,
                actor_id=actor_id,
                is_main_character=is_main,
                is_guest=is_guest,
                tier=tier
            )

            if in_party:
                self._state.active_party.append(member)
                logger.info(f"Added {npc_id} ({actor_id}) to active party")
            elif in_reserve:
                self._state.reserve_pool.append(member)
                logger.info(f"Added {npc_id} ({actor_id}) to reserve pool")

        # Sanity check: er moet altijd precies 1 main character zijn
        mc_count = sum(1 for m in self._state.active_party if m.is_main_character)
        if mc_count == 0:
            logger.error("No main character in party! Adding default MC")
            self._state.active_party.insert(0, PartyMember(
                npc_id="npc_mc_adhira",
                actor_id="mc_adhira",
                is_main_character=True,
                tier="S"
            ))
        elif mc_count > 1:
            logger.warning(f"Multiple main characters in party ({mc_count})")

    def get_active_party(self) -> list[PartyMember]:
        """Get alle actieve party members."""
        return list(self._state.active_party)

    def get_reserve_pool(self) -> list[PartyMember]:
        """Get alle reserve pool members."""
        return list(self._state.reserve_pool)

    def get_main_character(self) -> PartyMember | None:
        """Get de main character (protagonist)."""
        for member in self._state.active_party:
            if member.is_main_character:
                return member
        return None

    def is_in_party(self, npc_id: str) -> bool:
        """Check of NPC in active party zit."""
        return any(m.npc_id == npc_id for m in self._state.active_party)

    def is_in_reserve(self, npc_id: str) -> bool:
        """Check of NPC in reserve pool zit."""
        return any(m.npc_id == npc_id for m in self._state.reserve_pool)

    def add_to_reserve_pool(self, npc_id: str, actor_id: str, tier: str | None = None, is_guest: bool = False) -> None:
        """Voeg een companion toe aan reserve pool (recruitment).

        Parameters
        ----------
        npc_id : str
            NPC ID (bijv. "npc_comp_rajani")
        actor_id : str
            Actor ID uit actors.json (bijv. "comp_rajani")
        tier : str | None
            Tier (S/A/B/etc)
        is_guest : bool
            Guest-only flag
        """
        # Check of al in party/reserve
        if self.is_in_party(npc_id):
            logger.warning(f"{npc_id} already in active party")
            return
        if self.is_in_reserve(npc_id):
            logger.warning(f"{npc_id} already in reserve pool")
            return

        member = PartyMember(
            npc_id=npc_id,
            actor_id=actor_id,
            is_main_character=False,
            is_guest=is_guest,
            tier=tier
        )
        self._state.reserve_pool.append(member)
        logger.info(f"Added {npc_id} ({actor_id}) to reserve pool")

    def add_to_active_party(self, npc_id: str) -> bool:
        """Verplaats member van reserve naar active party.

        Parameters
        ----------
        npc_id : str
            NPC ID

        Returns
        -------
        bool
            True als succesvol, False als party vol of NPC niet in reserve
        """
        # Check party size limit
        if len(self._state.active_party) >= self._state.party_max_size:
            logger.warning(f"Party full ({self._state.party_max_size}), cannot add {npc_id}")
            return False

        # Find in reserve pool
        member = None
        for i, m in enumerate(self._state.reserve_pool):
            if m.npc_id == npc_id:
                member = self._state.reserve_pool.pop(i)
                break

        if not member:
            logger.warning(f"{npc_id} not in reserve pool")
            return False

        self._state.active_party.append(member)
        logger.info(f"Added {npc_id} ({member.actor_id}) to active party")
        return True

    def move_to_reserve(self, npc_id: str) -> bool:
        """Verplaats member van active party naar reserve.

        Main character kan niet removed worden.

        Parameters
        ----------
        npc_id : str
            NPC ID

        Returns
        -------
        bool
            True als succesvol, False als main character of niet in party
        """
        # Find in active party
        member = None
        for i, m in enumerate(self._state.active_party):
            if m.npc_id == npc_id:
                if m.is_main_character:
                    logger.warning(f"Cannot remove main character {npc_id} from party")
                    return False
                member = self._state.active_party.pop(i)
                break

        if not member:
            logger.warning(f"{npc_id} not in active party")
            return False

        self._state.reserve_pool.append(member)
        logger.info(f"Moved {npc_id} ({member.actor_id}) to reserve pool")
        return True

    def get_member_by_npc_id(self, npc_id: str) -> PartyMember | None:
        """Find member by npc_id (in active of reserve)."""
        for member in self._state.active_party:
            if member.npc_id == npc_id:
                return member
        for member in self._state.reserve_pool:
            if member.npc_id == npc_id:
                return member
        return None

    def get_member_by_actor_id(self, actor_id: str) -> PartyMember | None:
        """Find member by actor_id (in active of reserve)."""
        for member in self._state.active_party:
            if member.actor_id == actor_id:
                return member
        for member in self._state.reserve_pool:
            if member.actor_id == actor_id:
                return member
        return None

    @property
    def party_max_size(self) -> int:
        """Max party size."""
        return self._state.party_max_size

    @property
    def active_count(self) -> int:
        """Aantal actieve party members."""
        return len(self._state.active_party)

    @property
    def reserve_count(self) -> int:
        """Aantal reserve members."""
        return len(self._state.reserve_pool)


__all__ = ["PartySystem", "PartyMember", "PartyState"]
