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
This module contains the classes required for dialogue management.

- Dialogues: The dialogues class keeps track of all dialogues.
"""

from typing import Optional, Type, cast

from aea.common import Address
from aea.exceptions import enforce
from aea.protocols.base import Message
from aea.protocols.default.dialogues import DefaultDialogue as BaseDefaultDialogue
from aea.protocols.default.dialogues import DefaultDialogues as BaseDefaultDialogues
from aea.protocols.dialogue.base import Dialogue, DialogueLabel
from aea.protocols.signing.dialogues import SigningDialogue as BaseSigningDialogue
from aea.protocols.signing.dialogues import SigningDialogues as BaseSigningDialogues
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue as BaseFipaDialogue
from packages.fetchai.protocols.fipa.dialogues import FipaDialogues as BaseFipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.tac_negotiation.helpers import (
    DEMAND_DATAMODEL_NAME,
    SUPPLY_DATAMODEL_NAME,
)


DefaultDialogue = BaseDefaultDialogue


class DefaultDialogues(Model, BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return DefaultDialogue.Role.AGENT

        BaseDefaultDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )


FipaDialogue = BaseFipaDialogue


class FipaDialogues(Model, BaseFipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            fipa_message = cast(FipaMessage, message)
            if fipa_message.performative != FipaMessage.Performative.CFP:
                raise ValueError("First message must be a CFP!")
            query = fipa_message.query
            if query.model is None:
                raise ValueError("Query must have a data model!")
            if query.model.name not in [
                SUPPLY_DATAMODEL_NAME,
                DEMAND_DATAMODEL_NAME,
            ]:
                raise ValueError(
                    "Query data model name must be in [{},{}]".format(
                        SUPPLY_DATAMODEL_NAME, DEMAND_DATAMODEL_NAME
                    )
                )
            if message.sender != receiver_address:  # message is by other
                is_seller = (
                    query.model.name == SUPPLY_DATAMODEL_NAME
                )  # the counterparty is querying for supply/sellers (this agent is receiving their CFP so is the seller)
            else:  # message is by self
                is_seller = (
                    query.model.name == DEMAND_DATAMODEL_NAME
                )  # the agent is querying for demand/buyers (this agent is sending the CFP so it is the seller)
            role = FipaDialogue.Role.SELLER if is_seller else FipaDialogue.Role.BUYER
            return role

        BaseFipaDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
        )


class OefSearchDialogue(BaseOefSearchDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[OefSearchMessage] = OefSearchMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        BaseOefSearchDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._is_seller_search = None  # type: Optional[bool]

    @property
    def is_seller_search(self) -> bool:
        """Get if it is a seller search."""
        if self._is_seller_search is None:
            raise ValueError("is_seller_search not set!")
        return self._is_seller_search

    @is_seller_search.setter
    def is_seller_search(self, is_seller_search: bool) -> None:
        """Set is_seller_search."""
        enforce(self._is_seller_search is None, "is_seller_search already set!")
        self._is_seller_search = is_seller_search


class OefSearchDialogues(Model, BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseOefSearchDialogue.Role.AGENT

        BaseOefSearchDialogues.__init__(
            self,
            self_address=self.context.agent_address + "_" + str(self.context.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=OefSearchDialogue,
        )


class SigningDialogue(BaseSigningDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[SigningMessage] = SigningMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        BaseSigningDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._counterparty_signature = None  # type: Optional[str]
        self._associated_fipa_dialogue: Optional[FipaDialogue] = None

    @property
    def counterparty_signature(self) -> str:
        """Get counterparty signature."""
        if self._counterparty_signature is None:
            raise ValueError("counterparty_signature not set!")
        return self._counterparty_signature

    @counterparty_signature.setter
    def counterparty_signature(self, counterparty_signature: str) -> None:
        """Set is_seller_search."""
        enforce(
            self._counterparty_signature is None, "counterparty_signature already set!"
        )
        self._counterparty_signature = counterparty_signature

    @property
    def associated_fipa_dialogue(self) -> FipaDialogue:
        """Get associated_fipa_dialogue."""
        if self._associated_fipa_dialogue is None:
            raise ValueError("associated_fipa_dialogue not set!")
        return self._associated_fipa_dialogue

    @associated_fipa_dialogue.setter
    def associated_fipa_dialogue(self, associated_fipa_dialogue: FipaDialogue) -> None:
        """Set associated_fipa_dialogue."""
        enforce(
            self._associated_fipa_dialogue is None,
            "associated_fipa_dialogue already set!",
        )
        self._associated_fipa_dialogue = associated_fipa_dialogue


class SigningDialogues(Model, BaseSigningDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return BaseSigningDialogue.Role.SKILL

        BaseSigningDialogues.__init__(
            self,
            self_address=str(self.context.skill_id),
            role_from_first_message=role_from_first_message,
        )
