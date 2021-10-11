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

from typing import Any, Optional, Type, cast

from aea.common import Address
from aea.exceptions import enforce
from aea.helpers.search.models import Description
from aea.helpers.transaction.base import Terms
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel
from aea.skills.base import Model

from packages.fetchai.protocols.contract_api.dialogues import (
    ContractApiDialogue as BaseContractApiDialogue,
)
from packages.fetchai.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.cosm_trade.dialogues import (
    CosmTradeDialogue as BaseCosmTradeDialogue,
)
from packages.fetchai.protocols.cosm_trade.dialogues import (
    CosmTradeDialogues as BaseCosmTradeDialogues,
)
from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue as BaseDefaultDialogue,
)
from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogues as BaseDefaultDialogues,
)
from packages.fetchai.protocols.fipa.dialogues import FipaDialogue as BaseFipaDialogue
from packages.fetchai.protocols.fipa.dialogues import FipaDialogues as BaseFipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogue as BaseSigningDialogue,
)
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.tac_negotiation.helpers import (
    DEMAND_DATAMODEL_NAME,
    SUPPLY_DATAMODEL_NAME,
)


class FipaDialogue(BaseFipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_proposal", "_terms", "_counterparty_signature")

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[FipaMessage] = FipaMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        BaseFipaDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._proposal = None  # type: Optional[Description]
        self._terms = None  # type: Optional[Terms]
        self._counterparty_signature = None  # type: Optional[str]

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
    def proposal(self) -> Description:
        """Get the proposal."""
        if self._proposal is None:
            raise ValueError("Proposal not set!")
        return self._proposal

    @proposal.setter
    def proposal(self, proposal: Description) -> None:
        """Set the proposal."""
        enforce(self._proposal is None, "Proposal already set!")
        self._proposal = proposal

    @property
    def terms(self) -> Terms:
        """Get the terms."""
        if self._terms is None:
            raise ValueError("Terms not set!")
        return self._terms

    @terms.setter
    def terms(self, terms: Terms) -> None:
        """Set the terms."""
        enforce(self._terms is None, "Terms already set!")
        self._terms = terms


class FipaDialogues(Model, BaseFipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
                raise ValueError("First message must be a CFP!")  # pragma: nocover
            query = fipa_message.query
            if query.model is None:
                raise ValueError("Query must have a data model!")  # pragma: nocover
            if query.model.name not in [
                SUPPLY_DATAMODEL_NAME,
                DEMAND_DATAMODEL_NAME,
            ]:
                raise ValueError(  # pragma: nocover
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
            dialogue_class=FipaDialogue,
        )


class ContractApiDialogue(BaseContractApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_associated_fipa_dialogue",)

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[ContractApiMessage] = ContractApiMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        BaseContractApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._associated_fipa_dialogue: Optional[FipaDialogue] = None

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


class ContractApiDialogues(Model, BaseContractApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            return ContractApiDialogue.Role.AGENT

        BaseContractApiDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=ContractApiDialogue,
        )


CosmTradeDialogue = BaseCosmTradeDialogue


class CosmTradeDialogues(Model, BaseCosmTradeDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            return CosmTradeDialogue.Role.AGENT

        BaseCosmTradeDialogues.__init__(
            self,
            self_address=self.context.agent_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=CosmTradeDialogue,
        )


DefaultDialogue = BaseDefaultDialogue


class DefaultDialogues(Model, BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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


class LedgerApiDialogue(BaseLedgerApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_associated_signing_dialogue",)

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[LedgerApiMessage] = LedgerApiMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        BaseLedgerApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._associated_signing_dialogue = None  # type: Optional[SigningDialogue]

    @property
    def associated_signing_dialogue(self) -> "SigningDialogue":
        """Get the associated signing dialogue."""
        if self._associated_signing_dialogue is None:
            raise ValueError("Associated signing dialogue not set!")
        return self._associated_signing_dialogue

    @associated_signing_dialogue.setter
    def associated_signing_dialogue(
        self, associated_signing_dialogue: "SigningDialogue"
    ) -> None:
        """Set the associated signing dialogue."""
        enforce(
            self._associated_signing_dialogue is None,
            "Associated signing dialogue already set!",
        )
        self._associated_signing_dialogue = associated_signing_dialogue


class LedgerApiDialogues(Model, BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            return BaseLedgerApiDialogue.Role.AGENT

        BaseLedgerApiDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerApiDialogue,
        )


class OefSearchDialogue(BaseOefSearchDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_is_seller_search",)

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
        :param message_class: the message class
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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=OefSearchDialogue,
        )


class SigningDialogue(BaseSigningDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_associated_fipa_dialogue",)

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
        :param message_class: the message class
        """
        BaseSigningDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )
        self._associated_fipa_dialogue: Optional[FipaDialogue] = None
        self._associated_cosm_trade_dialogue: Optional[CosmTradeDialogue] = None

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

    @property
    def associated_cosm_trade_dialogue(self) -> Optional[CosmTradeDialogue]:
        """Get associated_cosm_trade_dialogue."""
        return self._associated_cosm_trade_dialogue

    @associated_cosm_trade_dialogue.setter
    def associated_cosm_trade_dialogue(
        self, associated_cosm_trade_dialogue: CosmTradeDialogue
    ) -> None:
        """Set associated_cosm_trade_dialogue."""
        enforce(
            self._associated_cosm_trade_dialogue is None,
            "associated_cosm_trade_dialogue already set!",
        )
        self._associated_cosm_trade_dialogue = associated_cosm_trade_dialogue


class SigningDialogues(Model, BaseSigningDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
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
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=SigningDialogue,
        )
