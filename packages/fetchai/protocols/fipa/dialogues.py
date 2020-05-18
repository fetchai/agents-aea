# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""
This module contains the classes required for FIPA dialogue management.

- DialogueLabel: The dialogue label class acts as an identifier for dialogues.
- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.
"""

from typing import Dict, List, Optional, Tuple, Union, cast

from aea.helpers.dialogue.base import Dialogue, DialogueLabel, Dialogues
from aea.mail.base import Address
from aea.protocols.base import Message

from packages.fetchai.protocols.fipa.message import FipaMessage

VALID_PREVIOUS_PERFORMATIVES = {
    FipaMessage.Performative.CFP: [None],
    FipaMessage.Performative.PROPOSE: [FipaMessage.Performative.CFP],
    FipaMessage.Performative.ACCEPT: [FipaMessage.Performative.PROPOSE],
    FipaMessage.Performative.ACCEPT_W_INFORM: [FipaMessage.Performative.PROPOSE],
    FipaMessage.Performative.MATCH_ACCEPT: [
        FipaMessage.Performative.ACCEPT,
        FipaMessage.Performative.ACCEPT_W_INFORM,
    ],
    FipaMessage.Performative.MATCH_ACCEPT_W_INFORM: [
        FipaMessage.Performative.ACCEPT,
        FipaMessage.Performative.ACCEPT_W_INFORM,
    ],
    FipaMessage.Performative.INFORM: [
        FipaMessage.Performative.MATCH_ACCEPT,
        FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
        FipaMessage.Performative.INFORM,
    ],
    FipaMessage.Performative.DECLINE: [
        FipaMessage.Performative.CFP,
        FipaMessage.Performative.PROPOSE,
        FipaMessage.Performative.ACCEPT,
        FipaMessage.Performative.ACCEPT_W_INFORM,
    ],
}  # type: Dict[FipaMessage.Performative, List[Union[None, FipaMessage.Performative]]]

SUPPLY_DATAMODEL_NAME = "supply"
DEMAND_DATAMODEL_NAME = "demand"


class FipaDialogue(Dialogue):
    """The FIPA dialogue class maintains state of a dialogue and manages it."""

    class EndState(Dialogue.EndState):
        """This class defines the end states of a dialogue."""

        SUCCESSFUL = 0
        DECLINED_CFP = 1
        DECLINED_PROPOSE = 2
        DECLINED_ACCEPT = 3

    class AgentRole(Dialogue.Role):
        """This class defines the agent's role in the dialogue."""

        SELLER = "seller"
        BUYER = "buyer"

    def __init__(
        self, dialogue_label: DialogueLabel, role: AgentRole, **kwargs
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param is_seller: indicates whether the agent associated with the dialogue is a seller or buyer

        :return: None
        """
        Dialogue.__init__(self, dialogue_label=dialogue_label, role=role)

    @staticmethod
    def role_from_first_message(message: Message) -> Dialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        fipa_message = cast(FipaMessage, message)
        if (
            fipa_message.performative == FipaMessage.Performative.CFP
            and fipa_message.is_incoming
        ):  # cfp from other agent
            query = cast(FipaMessage.Query, fipa_message.query)
            if query.model is not None:
                is_seller = (
                    query.model.name == DEMAND_DATAMODEL_NAME
                )  # the counterparty is querying for supply
            else:
                raise ValueError("Query.model is None")
        elif (
            fipa_message.performative == FipaMessage.Performative.CFP
            and not fipa_message.is_incoming
        ):  # cfp from self
            query = cast(FipaMessage.Query, fipa_message.query)
            if query.model is not None:
                is_seller = (
                    query.model.name == SUPPLY_DATAMODEL_NAME
                )  # this agent is querying for supply
            else:
                raise ValueError("Query.model is None")
        else:
            raise ValueError("message must be a cfp")

        if is_seller:
            return FipaDialogue.AgentRole.SELLER
        else:
            return FipaDialogue.AgentRole.BUYER

    def is_valid_next_message(self, fipa_msg: Message) -> bool:
        """
        Check whether this is a valid next message in the dialogue.

        :return: True if yes, False otherwise.
        """
        fipa_msg = cast(FipaMessage, fipa_msg)
        this_message_id = fipa_msg.message_id
        this_target = fipa_msg.target
        this_performative = fipa_msg.performative
        last_message = cast(FipaMessage, self.last_message())
        if self.is_empty():
            result = (
                this_message_id == FipaDialogue.STARTING_MESSAGE_ID
                and this_target == FipaDialogue.STARTING_TARGET
                and this_performative == FipaMessage.Performative.CFP
            )
        else:
            last_message_id = last_message.message_id
            last_target = last_message.target
            last_performative = last_message.performative
            result = (
                this_message_id == last_message_id + 1
                and this_target == last_target + 1
                and last_performative in VALID_PREVIOUS_PERFORMATIVES[this_performative]
            )
        return result

    def assign_final_dialogue_label(self, final_dialogue_label: DialogueLabel) -> None:
        """
        Assign the final dialogue label.

        :param final_dialogue_label: the final dialogue label
        :return: None
        """
        assert (
            self.dialogue_label.dialogue_starter_reference
            == final_dialogue_label.dialogue_starter_reference
        )
        assert self.dialogue_label.dialogue_responder_reference == ""
        assert final_dialogue_label.dialogue_responder_reference != ""
        assert (
            self.dialogue_label.dialogue_opponent_addr
            == final_dialogue_label.dialogue_opponent_addr
        )
        assert (
            self.dialogue_label.dialogue_starter_addr
            == final_dialogue_label.dialogue_starter_addr
        )
        self._dialogue_label = final_dialogue_label


class FipaDialogueStats(object):
    """Class to handle statistics on the negotiation."""

    def __init__(self) -> None:
        """Initialize a StatsManager."""
        self._self_initiated = {
            FipaDialogue.EndState.SUCCESSFUL: 0,
            FipaDialogue.EndState.DECLINED_CFP: 0,
            FipaDialogue.EndState.DECLINED_PROPOSE: 0,
            FipaDialogue.EndState.DECLINED_ACCEPT: 0,
        }  # type: Dict[FipaDialogue.EndState, int]
        self._other_initiated = {
            FipaDialogue.EndState.SUCCESSFUL: 0,
            FipaDialogue.EndState.DECLINED_CFP: 0,
            FipaDialogue.EndState.DECLINED_PROPOSE: 0,
            FipaDialogue.EndState.DECLINED_ACCEPT: 0,
        }  # type: Dict[FipaDialogue.EndState, int]

    @property
    def self_initiated(self) -> Dict[FipaDialogue.EndState, int]:
        """Get the stats dictionary on self initiated dialogues."""
        return self._self_initiated

    @property
    def other_initiated(self) -> Dict[FipaDialogue.EndState, int]:
        """Get the stats dictionary on other initiated dialogues."""
        return self._other_initiated

    def add_dialogue_endstate(
        self, end_state: FipaDialogue.EndState, is_self_initiated: bool
    ) -> None:
        """
        Add dialogue endstate stats.

        :param end_state: the end state of the dialogue
        :param is_self_initiated: whether the dialogue is initiated by the agent or the opponent

        :return: None
        """
        if is_self_initiated:
            self._self_initiated[end_state] += 1
        else:
            self._other_initiated[end_state] += 1


class FipaDialogues(Dialogues):
    """The FIPA dialogues class keeps track of all dialogues."""

    def __init__(self, agent_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Dialogues.__init__(self, agent_address)
        self._initiated_dialogues = {}  # type: Dict[DialogueLabel, FipaDialogue]
        # self._dialogues_as_seller = {}  # type: Dict[DialogueLabel, FipaDialogue]
        # self._dialogues_as_buyer = {}  # type: Dict[DialogueLabel, FipaDialogue]
        self._dialogue_stats = FipaDialogueStats()

    # @property
    # def dialogues_as_seller(self) -> Dict[DialogueLabel, FipaDialogue]:
    #     """Get dictionary of dialogues in which the agent acts as a seller."""
    #     return self._dialogues_as_seller
    #
    # @property
    # def dialogues_as_buyer(self) -> Dict[DialogueLabel, FipaDialogue]:
    #     """Get dictionary of dialogues in which the agent acts as a buyer."""
    #     return self._dialogues_as_buyer

    @property
    def dialogue_stats(self) -> FipaDialogueStats:
        """Get the dialogue statistics."""
        return self._dialogue_stats

    def get_dialogue(self, fipa_msg: Message) -> Optional[Dialogue]:
        """
        Retrieve the dialogue 'fipa_msg' belongs to.

        :param fipa_msg: the fipa message

        :return: the dialogue, or None in case such a dialogue does not exist
        """
        result = None
        fipa_msg = cast(FipaMessage, fipa_msg)
        dialogue_reference = fipa_msg.dialogue_reference
        self_initiated_dialogue_label = DialogueLabel(
            dialogue_reference, fipa_msg.counterparty, self.agent_address
        )
        other_initiated_dialogue_label = DialogueLabel(
            dialogue_reference, fipa_msg.counterparty, fipa_msg.counterparty
        )
        if other_initiated_dialogue_label in self.dialogues:
            other_initiated_dialogue = cast(
                FipaDialogue, self.dialogues[other_initiated_dialogue_label]
            )
            result = other_initiated_dialogue
        if self_initiated_dialogue_label in self.dialogues:
            self_initiated_dialogue = cast(
                FipaDialogue, self.dialogues[self_initiated_dialogue_label]
            )
            result = self_initiated_dialogue
        return result

    def update_self_initiated_dialogue_label_on_second_message(self, second_message: FipaMessage) -> None:
        """
        Update a self initiated dialogue label with a complete dialogue reference from counterparty's first message

        :param second_message: The second message in the dialogue (the first message by the counterparty in a self initiated dialogue)
        :return: None
        """
        self_initiated_dialogue_label = (second_message.dialogue_reference[0], "")
        self_initiated_dialogue_label = DialogueLabel(
            self_initiated_dialogue_label, second_message.counterparty, self.agent_address
        )
        if self_initiated_dialogue_label in self._dialogues:
            self_initiated_dialogue = cast(FipaDialogue, self.dialogues[self_initiated_dialogue_label])
            self.dialogues.pop(self_initiated_dialogue_label)
            final_dialogue_label = DialogueLabel(
                second_message.dialogue_reference,
                self_initiated_dialogue_label.dialogue_opponent_addr,
                self_initiated_dialogue_label.dialogue_starter_addr,
            )
            self_initiated_dialogue.assign_final_dialogue_label(
                final_dialogue_label
            )
            assert self_initiated_dialogue.dialogue_label not in self.dialogues
            # if self_initiated_dialogue.is_seller:
            #     assert dialogue.dialogue_label not in self.dialogues_as_seller
            #     self._dialogues_as_seller.update({dialogue.dialogue_label: dialogue})
            # else:
            #     assert dialogue.dialogue_label not in self.dialogues_as_buyer
            #     self._dialogues_as_buyer.update({dialogue.dialogue_label: dialogue})
            self.dialogues.update({self_initiated_dialogue.dialogue_label: self_initiated_dialogue})

    def update(self, message: Message,) -> Optional[Dialogue]:
        """
        Update the state of dialogues with a new message.

        If the message is for a new dialogue, a new dialogue is created with 'message' as its first message and returned.
        If the message is addressed to an existing dialogue, the dialogue is retrieved, extended with this message and returned.
        If there are any errors, e.g. the message dialogue reference does not exists, the message is invalid w.r.t. the dialogue, return None.

        :param message: a new message
        :return: the new or existing dialogue the message is intended for, or None in case of any errors.
        """
        result = None

        fipa_msg = cast(FipaMessage, message)
        dialogue_reference = fipa_msg.dialogue_reference

        if (  # new dialogue by other
            dialogue_reference[0] != ""
            and dialogue_reference[1] == ""
            and message.is_incoming
        ):
            dialogue = self.create_opponent_initiated(
                message.counterparty,
                fipa_msg.dialogue_reference,
                Dialogue.role_from_first_message(fipa_msg),
            )
            dialogue.incoming_safe_extend(message)
            result = dialogue
        elif (  # new dialogue by self
            dialogue_reference[0] != ""
            and dialogue_reference[1] == ""
            and not message.is_incoming
        ):
            assert (
                message.counterparty is not None
            ), "The message counter-party field is not set {}".format(message)
            dialogue = self.create_self_initiated(
                dialogue_opponent_addr=message.counterparty,
                dialogue_starter_addr=self.agent_address,
                role=Dialogue.role_from_first_message(fipa_msg),
            )
            dialogue.outgoing_safe_extend(message)
            result = dialogue
        else:  # existing dialogue
            self.update_self_initiated_dialogue_label_on_second_message(fipa_msg)
            dialogue = self.get_dialogue(message)
            if dialogue is not None:
                if message.is_incoming:
                    dialogue.incoming_safe_extend(message)
                else:
                    dialogue.outgoing_safe_extend(message)
                result = dialogue
            else:  # couldn't find the dialogue
                pass
        return result

    def create_self_initiated(
        self,
        dialogue_opponent_addr: Address,
        dialogue_starter_addr: Address,
        role: FipaDialogue.AgentRole,
    ) -> Dialogue:
        """
        Create a self initiated dialogue.

        :param dialogue_opponent_addr: the pbk of the agent with which the dialogue is kept.
        :param dialogue_starter_addr: the pbk of the agent which started the dialogue
        :param role: the agent's role

        :return: the created dialogue.
        """
        dialogue_reference = (str(self._next_dialogue_nonce()), "")
        dialogue_label = DialogueLabel(
            dialogue_reference, dialogue_opponent_addr, dialogue_starter_addr
        )
        dialogue = FipaDialogue(dialogue_label, role=role)
        # self._initiated_dialogues.update({dialogue_label: dialogue})
        self.dialogues.update({dialogue_label: dialogue})
        return dialogue

    def create_opponent_initiated(
        self,
        dialogue_opponent_addr: Address,
        dialogue_reference: Tuple[str, str],
        role: FipaDialogue.AgentRole,
    ) -> Dialogue:
        """
        Save an opponent initiated dialogue.

        :param dialogue_opponent_addr: the address of the agent with which the dialogue is kept.
        :param dialogue_reference: the reference of the dialogue.
        :param role: the agent's role
        :return: the created dialogue
        """
        assert (
            dialogue_reference[0] != "" and dialogue_reference[1] == ""
        ), "Cannot initiate dialogue with preassigned dialogue_responder_reference!"
        new_dialogue_reference = (
            dialogue_reference[0],
            str(self._next_dialogue_nonce()),
        )
        dialogue_label = DialogueLabel(
            new_dialogue_reference, dialogue_opponent_addr, dialogue_opponent_addr
        )
        # result = self._create(dialogue_label, role=role)

        assert dialogue_label not in self.dialogues
        dialogue = FipaDialogue(dialogue_label, role=role)
        # if role == FipaDialogue.AgentRole.SELLER:
        #     assert dialogue_label not in self.dialogues_as_seller
        #     self._dialogues_as_seller.update({dialogue_label: dialogue})
        # else:
        #     assert dialogue_label not in self.dialogues_as_buyer
        #     self._dialogues_as_buyer.update({dialogue_label: dialogue})
        self.dialogues.update({dialogue_label: dialogue})

        return dialogue

    def _create(
        self, dialogue_label: DialogueLabel, role: FipaDialogue.AgentRole
    ) -> FipaDialogue:
        """
        Create a dialogue.

        :param dialogue_label: the dialogue label
        :param role: the agent's role

        :return: the created dialogue
        """
        pass

