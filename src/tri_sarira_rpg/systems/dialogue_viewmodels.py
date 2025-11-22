"""Dialogue viewmodels voor UI-friendly data representatie.

Deze module bevat immutable dataclasses die dialogue state representeren
voor de presentatielaag, zonder directe koppeling aan de interne
dialogue systeem implementatie.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tri_sarira_rpg.core.protocols import (
        EconomySystemProtocol,
        FlagsSystemProtocol,
        InventorySystemProtocol,
        PartySystemProtocol,
        QuestSystemProtocol,
    )


@dataclass(frozen=True)
class ChoiceView:
    """UI-vriendelijke representatie van een keuze.

    Dit is een immutable snapshot voor rendering.
    """

    choice_id: str
    text: str
    index: int  # Voor UI numbering (0-based)


@dataclass(frozen=True)
class DialogueView:
    """UI-vriendelijke representatie van de huidige dialogue state.

    Gebruikt door presentation layer voor rendering zonder directe
    toegang tot interne dialogue state.
    """

    speaker_id: str
    lines: tuple[str, ...]  # Immutable tuple ipv list
    choices: tuple[ChoiceView, ...]  # Immutable tuple ipv list
    can_auto_advance: bool


@dataclass(frozen=True)
class ConversationResult:
    """Resultaat van een dialogue action.

    Immutable view van wat er is gebeurd na een keuze of auto-advance.
    """

    conversation_ended: bool
    next_node_id: str | None = None
    effects_applied: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class DialogueContext:
    """Context voor dialogue evaluatie (referenties naar andere systems).

    Dit is NIET frozen omdat het runtime system references bevat.
    """

    flags_system: FlagsSystemProtocol | None = None
    party_system: PartySystemProtocol | None = None
    inventory_system: InventorySystemProtocol | None = None
    economy_system: EconomySystemProtocol | None = None
    quest_system: QuestSystemProtocol | None = None


# DialogueSession is niet frozen omdat het mutable state heeft
class DialogueSession:
    """Een actieve dialogue sessie.

    Bevat mutable state voor de lopende conversatie.
    """

    def __init__(
        self,
        dialogue_id: str,
        graph: Any,  # DialogueGraph - avoid circular import
        context: DialogueContext,
        start_node_id: str = "n_intro",
    ) -> None:
        self.dialogue_id = dialogue_id
        self.graph = graph
        self.context = context
        self.current_node_id = start_node_id
        self.conversation_ended = False

    def get_current_node(self) -> Any | None:
        """Haal de huidige node op."""
        return self.graph.nodes.get(self.current_node_id)


__all__ = [
    "ChoiceView",
    "ConversationResult",
    "DialogueContext",
    "DialogueSession",
    "DialogueView",
]
