"""Dialooggraphs en keuzes volgens 3.4 Quests & Dialogue System Spec."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConditionType(Enum):
    """Condition types voor dialogue node/choice filtering."""

    FLAG_SET = "FLAG_SET"
    FLAG_NOT_SET = "FLAG_NOT_SET"
    COMPANION_IN_PARTY = "COMPANION_IN_PARTY"
    # Future: QUEST_STATE, TIME_BAND, etc.


class EffectType(Enum):
    """Effect types die toegepast kunnen worden via dialogue."""

    SET_FLAG = "SET_FLAG"
    CLEAR_FLAG = "CLEAR_FLAG"
    GIVE_ITEM = "GIVE_ITEM"
    MODIFY_MONEY = "MODIFY_MONEY"
    # Quest effects (nog niet geïmplementeerd, maar wel voorzien)
    QUEST_START = "QUEST_START"
    QUEST_ADVANCE = "QUEST_ADVANCE"
    QUEST_COMPLETE = "QUEST_COMPLETE"


@dataclass
class Line:
    """Een tekstregel in een dialogue node."""

    text: str
    emotion: str | None = None


@dataclass
class Condition:
    """Een conditie voor node/choice visibility."""

    condition_type: str  # ConditionType value
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class EffectRef:
    """Een effect dat uitgevoerd moet worden."""

    effect_type: str  # EffectType value
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Choice:
    """Een keuze-optie in een dialogue node."""

    choice_id: str
    text: str
    conditions: list[Condition] = field(default_factory=list)
    effects: list[EffectRef] = field(default_factory=list)
    next_node_id: str | None = None
    end_conversation: bool = False


@dataclass
class DialogueNode:
    """Een node in een dialogue graph."""

    node_id: str
    speaker_id: str
    lines: list[Line]
    choices: list[Choice] = field(default_factory=list)
    auto_advance_to: str | None = None
    conditions: list[Condition] = field(default_factory=list)
    end_conversation: bool = False


@dataclass
class DialogueGraph:
    """Een complete dialogue graph (meestal per NPC of scene)."""

    dialogue_id: str
    scope: str  # "NPC", "SCENE", etc.
    owner_id: str  # npc_id of scene identifier
    nodes: dict[str, DialogueNode] = field(default_factory=dict)


@dataclass
class DialogueContext:
    """Context voor dialogue evaluatie (referenties naar andere systems)."""

    flags_system: Any | None = None
    party_system: Any | None = None
    inventory_system: Any | None = None
    economy_system: Any | None = None
    quest_system: Any | None = None


@dataclass
class ChoiceView:
    """UI-vriendelijke representatie van een keuze."""

    choice_id: str
    text: str
    index: int  # Voor UI numbering (0-based)


@dataclass
class DialogueView:
    """UI-vriendelijke representatie van de huidige dialogue state."""

    speaker_id: str
    lines: list[str]  # Combined text lines
    choices: list[ChoiceView]
    can_auto_advance: bool


@dataclass
class ConversationResult:
    """Resultaat van een dialogue action."""

    conversation_ended: bool
    next_node_id: str | None = None
    effects_applied: list[str] = field(default_factory=list)


class DialogueSession:
    """Een actieve dialogue sessie."""

    def __init__(
        self,
        dialogue_id: str,
        graph: DialogueGraph,
        context: DialogueContext,
        start_node_id: str = "n_intro",
    ) -> None:
        self.dialogue_id = dialogue_id
        self.graph = graph
        self.context = context
        self.current_node_id = start_node_id
        self.conversation_ended = False

    def get_current_node(self) -> DialogueNode | None:
        """Haal de huidige node op."""
        return self.graph.nodes.get(self.current_node_id)


class DialogueSystem:
    """Beheert dialoogstate en levert nodes aan UI."""

    def __init__(self, data_repository: Any | None = None) -> None:
        self._data_repository = data_repository
        self._active_session: DialogueSession | None = None

    def start_dialogue(
        self, dialogue_id: str, context: DialogueContext, start_node_id: str = "n_intro"
    ) -> DialogueSession | None:
        """Start een nieuwe dialogue sessie.

        Parameters
        ----------
        dialogue_id : str
            ID van de dialogue graph om te laden
        context : DialogueContext
            Context met referenties naar andere systems
        start_node_id : str
            ID van de start node (default: "n_intro")

        Returns
        -------
        DialogueSession | None
            Nieuwe sessie, of None als dialogue niet gevonden
        """
        if not self._data_repository:
            logger.error("DialogueSystem has no data_repository")
            return None

        # Load dialogue data
        dialogue_data = self._data_repository.get_dialogue(dialogue_id)
        if not dialogue_data:
            logger.error(f"Dialogue not found: {dialogue_id}")
            return None

        # Parse dialogue graph
        graph = self._parse_dialogue_graph(dialogue_data)
        if not graph:
            logger.error(f"Failed to parse dialogue: {dialogue_id}")
            return None

        # Check if start node exists
        if start_node_id not in graph.nodes:
            logger.error(f"Start node '{start_node_id}' not found in dialogue '{dialogue_id}'")
            return None

        # Create session
        session = DialogueSession(dialogue_id, graph, context, start_node_id)
        self._active_session = session

        logger.info(f"Started dialogue: {dialogue_id} at node {start_node_id}")
        return session

    def get_current_view(self, session: DialogueSession) -> DialogueView | None:
        """Haal de huidige view op voor UI rendering.

        Parameters
        ----------
        session : DialogueSession
            Actieve dialogue sessie

        Returns
        -------
        DialogueView | None
            View voor UI, of None als sessie beëindigd
        """
        if session.conversation_ended:
            return None

        node = session.get_current_node()
        if not node:
            logger.error(f"Current node '{session.current_node_id}' not found in graph")
            session.conversation_ended = True
            return None

        # Check node conditions
        if not self._evaluate_conditions(node.conditions, session.context):
            logger.warning(f"Node {node.node_id} conditions not met, ending conversation")
            session.conversation_ended = True
            return None

        # Combine lines into list of text strings
        lines = [line.text for line in node.lines]

        # Filter choices based on conditions
        visible_choices = []
        for i, choice in enumerate(node.choices):
            if self._evaluate_conditions(choice.conditions, session.context):
                visible_choices.append(ChoiceView(choice.choice_id, choice.text, i))

        # Check for auto-advance
        can_auto_advance = (
            len(visible_choices) == 0
            and node.auto_advance_to is not None
            and not node.end_conversation
        )

        return DialogueView(
            speaker_id=node.speaker_id,
            lines=lines,
            choices=visible_choices,
            can_auto_advance=can_auto_advance,
        )

    def choose_option(self, session: DialogueSession, choice_id: str) -> ConversationResult:
        """Verwerk spelerkeuze en advance naar volgende node.

        Parameters
        ----------
        session : DialogueSession
            Actieve dialogue sessie
        choice_id : str
            ID van de gekozen optie

        Returns
        -------
        ConversationResult
            Resultaat met nieuwe state
        """
        node = session.get_current_node()
        if not node:
            return ConversationResult(conversation_ended=True)

        # Find the chosen choice
        chosen_choice = None
        for choice in node.choices:
            if choice.choice_id == choice_id:
                chosen_choice = choice
                break

        if not chosen_choice:
            logger.error(f"Choice '{choice_id}' not found in node '{node.node_id}'")
            return ConversationResult(conversation_ended=True)

        # Apply effects
        effects_applied = self._apply_effects(chosen_choice.effects, session.context)

        # Determine next state
        if chosen_choice.end_conversation:
            session.conversation_ended = True
            return ConversationResult(conversation_ended=True, effects_applied=effects_applied)

        # Advance to next node
        next_node_id = chosen_choice.next_node_id
        if next_node_id:
            session.current_node_id = next_node_id
            logger.debug(f"Advanced to node: {next_node_id}")
            return ConversationResult(
                conversation_ended=False,
                next_node_id=next_node_id,
                effects_applied=effects_applied,
            )
        else:
            # No next node and no end_conversation -> end anyway
            logger.warning(
                f"Choice '{choice_id}' has no next_node_id and end_conversation=False, ending anyway"
            )
            session.conversation_ended = True
            return ConversationResult(conversation_ended=True, effects_applied=effects_applied)

    def auto_advance(self, session: DialogueSession) -> ConversationResult:
        """Auto-advance naar volgende node (als geen choices).

        Parameters
        ----------
        session : DialogueSession
            Actieve dialogue sessie

        Returns
        -------
        ConversationResult
            Resultaat met nieuwe state
        """
        node = session.get_current_node()
        if not node:
            return ConversationResult(conversation_ended=True)

        if node.end_conversation:
            session.conversation_ended = True
            return ConversationResult(conversation_ended=True)

        if node.auto_advance_to:
            session.current_node_id = node.auto_advance_to
            logger.debug(f"Auto-advanced to node: {node.auto_advance_to}")
            return ConversationResult(conversation_ended=False, next_node_id=node.auto_advance_to)
        else:
            # No auto_advance and no choices -> end conversation
            session.conversation_ended = True
            return ConversationResult(conversation_ended=True)

    def _parse_dialogue_graph(self, data: dict[str, Any]) -> DialogueGraph | None:
        """Parse dialogue data into DialogueGraph object."""
        try:
            dialogue_id = data["dialogue_id"]
            scope = data.get("scope", "NPC")
            owner_id = data.get("owner_id", "")

            nodes_dict = {}
            for node_data in data.get("nodes", []):
                node = self._parse_node(node_data)
                if node:
                    nodes_dict[node.node_id] = node

            return DialogueGraph(
                dialogue_id=dialogue_id,
                scope=scope,
                owner_id=owner_id,
                nodes=nodes_dict,
            )
        except KeyError as e:
            logger.error(f"Missing required key in dialogue data: {e}")
            return None

    def _parse_node(self, data: dict[str, Any]) -> DialogueNode | None:
        """Parse node data into DialogueNode object."""
        try:
            node_id = data["node_id"]
            speaker_id = data["speaker_id"]

            # Parse lines
            lines = []
            for line_data in data.get("lines", []):
                if isinstance(line_data, dict):
                    lines.append(
                        Line(
                            text=line_data.get("text", ""),
                            emotion=line_data.get("emotion"),
                        )
                    )
                elif isinstance(line_data, str):
                    lines.append(Line(text=line_data))

            # Parse choices
            choices = []
            for choice_data in data.get("choices", []):
                choice = self._parse_choice(choice_data)
                if choice:
                    choices.append(choice)

            # Parse conditions
            conditions = []
            for cond_data in data.get("conditions", []):
                cond = self._parse_condition(cond_data)
                if cond:
                    conditions.append(cond)

            return DialogueNode(
                node_id=node_id,
                speaker_id=speaker_id,
                lines=lines,
                choices=choices,
                auto_advance_to=data.get("auto_advance_to"),
                conditions=conditions,
                end_conversation=data.get("end_conversation", False),
            )
        except KeyError as e:
            logger.error(f"Missing required key in node data: {e}")
            return None

    def _parse_choice(self, data: dict[str, Any]) -> Choice | None:
        """Parse choice data into Choice object."""
        try:
            choice_id = data["choice_id"]
            text = data["text"]

            # Parse conditions
            conditions = []
            for cond_data in data.get("conditions", []):
                cond = self._parse_condition(cond_data)
                if cond:
                    conditions.append(cond)

            # Parse effects
            effects = []
            for effect_data in data.get("effects", []):
                effect = self._parse_effect(effect_data)
                if effect:
                    effects.append(effect)

            return Choice(
                choice_id=choice_id,
                text=text,
                conditions=conditions,
                effects=effects,
                next_node_id=data.get("next_node_id"),
                end_conversation=data.get("end_conversation", False),
            )
        except KeyError as e:
            logger.error(f"Missing required key in choice data: {e}")
            return None

    def _parse_condition(self, data: dict[str, Any]) -> Condition | None:
        """Parse condition data into Condition object."""
        try:
            condition_type = data["condition_type"]
            params = data.get("params", {})
            return Condition(condition_type=condition_type, params=params)
        except KeyError as e:
            logger.error(f"Missing required key in condition data: {e}")
            return None

    def _parse_effect(self, data: dict[str, Any]) -> EffectRef | None:
        """Parse effect data into EffectRef object."""
        try:
            effect_type = data["effect_type"]
            params = {k: v for k, v in data.items() if k != "effect_type"}
            return EffectRef(effect_type=effect_type, params=params)
        except KeyError as e:
            logger.error(f"Missing required key in effect data: {e}")
            return None

    def _evaluate_conditions(self, conditions: list[Condition], context: DialogueContext) -> bool:
        """Evalueer of alle conditions waar zijn.

        Parameters
        ----------
        conditions : list[Condition]
            List van conditions om te checken
        context : DialogueContext
            Context met system referenties

        Returns
        -------
        bool
            True als alle conditions waar zijn
        """
        for condition in conditions:
            if not self._evaluate_single_condition(condition, context):
                return False
        return True

    def _evaluate_single_condition(self, condition: Condition, context: DialogueContext) -> bool:
        """Evalueer een enkele condition."""
        cond_type = condition.condition_type

        if cond_type == "FLAG_SET":
            flag_id = condition.params.get("flag_id")
            if not flag_id:
                logger.warning("FLAG_SET condition missing flag_id")
                return False
            if context.flags_system:
                return context.flags_system.has_flag(flag_id)
            return False

        elif cond_type == "FLAG_NOT_SET":
            flag_id = condition.params.get("flag_id")
            if not flag_id:
                logger.warning("FLAG_NOT_SET condition missing flag_id")
                return False
            if context.flags_system:
                return not context.flags_system.has_flag(flag_id)
            return True  # If no flags system, flag is not set

        elif cond_type == "COMPANION_IN_PARTY":
            npc_id = condition.params.get("npc_id")
            if not npc_id:
                logger.warning("COMPANION_IN_PARTY condition missing npc_id")
                return False
            if context.party_system:
                return context.party_system.is_in_active_party(npc_id)
            return False

        else:
            logger.warning(f"Unknown condition type: {cond_type}")
            return True  # Unknown conditions pass by default

    def _apply_effects(self, effects: list[EffectRef], context: DialogueContext) -> list[str]:
        """Pas alle effects toe en return lijst van toegepaste effects.

        Parameters
        ----------
        effects : list[EffectRef]
            List van effects om toe te passen
        context : DialogueContext
            Context met system referenties

        Returns
        -------
        list[str]
            List van effect descriptions
        """
        applied = []
        for effect in effects:
            result = self._apply_single_effect(effect, context)
            if result:
                applied.append(result)
        return applied

    def _apply_single_effect(self, effect: EffectRef, context: DialogueContext) -> str | None:
        """Pas een enkel effect toe."""
        effect_type = effect.effect_type

        if effect_type == "SET_FLAG":
            flag_id = effect.params.get("flag_id")
            if not flag_id:
                logger.warning("SET_FLAG effect missing flag_id")
                return None
            if context.flags_system:
                context.flags_system.set_flag(flag_id)
                logger.info(f"Set flag: {flag_id}")
                return f"Set flag: {flag_id}"
            return None

        elif effect_type == "CLEAR_FLAG":
            flag_id = effect.params.get("flag_id")
            if not flag_id:
                logger.warning("CLEAR_FLAG effect missing flag_id")
                return None
            if context.flags_system:
                context.flags_system.clear_flag(flag_id)
                logger.info(f"Cleared flag: {flag_id}")
                return f"Cleared flag: {flag_id}"
            return None

        elif effect_type == "GIVE_ITEM":
            item_id = effect.params.get("item_id")
            quantity = effect.params.get("quantity", 1)
            if not item_id:
                logger.warning("GIVE_ITEM effect missing item_id")
                return None
            if context.inventory_system:
                context.inventory_system.add_item(item_id, quantity)
                logger.info(f"Gave item: {item_id} x{quantity}")
                return f"Gave item: {item_id} x{quantity}"
            return None

        elif effect_type == "MODIFY_MONEY":
            amount = effect.params.get("amount", 0)
            if context.economy_system:
                # EconomySystem might not have modify_money yet, log for now
                logger.info(f"Modify money: {amount} (not implemented)")
                return f"Modify money: {amount} (not implemented)"
            else:
                logger.info(f"Modify money: {amount} (no economy system)")
                return None

        elif effect_type == "QUEST_START":
            quest_id = effect.params.get("quest_id")
            if not quest_id:
                logger.warning("QUEST_START effect missing quest_id")
                return None
            if context.quest_system:
                try:
                    context.quest_system.start_quest(quest_id)
                    logger.info(f"Started quest: {quest_id}")
                    return f"Started quest: {quest_id}"
                except Exception as e:
                    logger.error(f"Failed to start quest {quest_id}: {e}")
                    return None
            else:
                logger.warning(f"QUEST_START: {quest_id} (no quest system)")
                return None

        elif effect_type == "QUEST_ADVANCE":
            quest_id = effect.params.get("quest_id")
            next_stage_id = effect.params.get("next_stage_id")
            if not quest_id:
                logger.warning("QUEST_ADVANCE effect missing quest_id")
                return None
            if context.quest_system:
                try:
                    context.quest_system.advance_quest(quest_id, next_stage_id)
                    logger.info(f"Advanced quest: {quest_id} to stage {next_stage_id}")
                    return f"Advanced quest: {quest_id}"
                except Exception as e:
                    logger.error(f"Failed to advance quest {quest_id}: {e}")
                    return None
            else:
                logger.warning(f"QUEST_ADVANCE: {quest_id} (no quest system)")
                return None

        elif effect_type == "QUEST_COMPLETE":
            quest_id = effect.params.get("quest_id")
            if not quest_id:
                logger.warning("QUEST_COMPLETE effect missing quest_id")
                return None
            if context.quest_system:
                try:
                    context.quest_system.complete_quest(quest_id)
                    logger.info(f"Completed quest: {quest_id}")
                    return f"Completed quest: {quest_id}"
                except Exception as e:
                    logger.error(f"Failed to complete quest {quest_id}: {e}")
                    return None
            else:
                logger.warning(f"QUEST_COMPLETE: {quest_id} (no quest system)")
                return None

        else:
            logger.warning(f"Unknown effect type: {effect_type}")
            return None


__all__ = ["DialogueSystem", "DialogueContext", "DialogueSession", "DialogueView"]
