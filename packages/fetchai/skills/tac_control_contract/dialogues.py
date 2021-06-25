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

- DefaultDialogue: The dialogue class maintains state of a dialogue of type default and manages it.
- DefaultDialogues: The dialogues class keeps track of all dialogues of type default.
- OefSearchDialogue: The dialogue class maintains state of a dialogue of type oef_search and manages it.
- OefSearchDialogues: The dialogues class keeps track of all dialogues of type oef_search.
- TacDialogue: The dialogue class maintains state of a dialogue of type tac and manages it.
- TacDialogues: The dialogues class keeps track of all dialogues of type tac.
"""

from enum import Enum
from typing import Any, Optional, Type

from aea.common import Address
from aea.exceptions import enforce
from aea.helpers.transaction.base import Terms
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.skills.base import Model

from packages.fetchai.protocols.contract_api.dialogues import (
    ContractApiDialogue as BaseContractApiDialogue,
)
from packages.fetchai.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogue as BaseSigningDialogue,
)
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.tac_control.dialogues import (
    DefaultDialogue as BaseDefaultDialogue,
)
from packages.fetchai.skills.tac_control.dialogues import (
    DefaultDialogues as BaseDefaultDialogues,
)
from packages.fetchai.skills.tac_control.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.skills.tac_control.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.skills.tac_control.dialogues import TacDialogue as BaseTacDialogue
from packages.fetchai.skills.tac_control.dialogues import (
    TacDialogues as BaseTacDialogues,
)


DefaultDialogue = BaseDefaultDialogue

DefaultDialogues = BaseDefaultDialogues

OefSearchDialogue = BaseOefSearchDialogue

OefSearchDialogues = BaseOefSearchDialogues

TacDialogue = BaseTacDialogue

TacDialogues = BaseTacDialogues


class ContractApiDialogue(BaseContractApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_terms", "_callable")

    class Callable(Enum):
        """Contract callable."""

        GET_DEPLOY_TRANSACTION = "get_deploy_transaction"
        GET_CREATE_BATCH_TRANSACTION = "get_create_batch_transaction"
        GET_MINT_BATCH_TRANSACTION = "get_mint_batch_transaction"

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
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
        self._terms = None  # type: Optional[Terms]
        self._callable = None  # type: Optional[ContractApiDialogue.Callable]

    @property
    def callable(self) -> "Callable":
        """Get the callable."""
        if self._callable is None:
            raise ValueError("Callable not set!")
        return self._callable

    @callable.setter
    def callable(  # pylint: disable=redefined-builtin
        self, callable: "Callable"
    ) -> None:
        """Set the callable."""
        enforce(self._callable is None, "Callable already set!")
        self._callable = callable

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
        ) -> BaseDialogue.Role:
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


class SigningDialogue(BaseSigningDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_associated_contract_api_dialogue",)

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
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
        self._associated_contract_api_dialogue = (
            None
        )  # type: Optional[ContractApiDialogue]

    @property
    def associated_contract_api_dialogue(self) -> ContractApiDialogue:
        """Get the associated contract api dialogue."""
        if self._associated_contract_api_dialogue is None:
            raise ValueError("Associated contract api dialogue not set!")
        return self._associated_contract_api_dialogue

    @associated_contract_api_dialogue.setter
    def associated_contract_api_dialogue(
        self, associated_contract_api_dialogue: ContractApiDialogue
    ) -> None:
        """Set the associated contract api dialogue."""
        enforce(
            self._associated_contract_api_dialogue is None,
            "Associated contract api dialogue already set!",
        )
        self._associated_contract_api_dialogue = associated_contract_api_dialogue


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
        ) -> BaseDialogue.Role:
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


class LedgerApiDialogue(BaseLedgerApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    __slots__ = ("_associated_signing_dialogue",)

    def __init__(
        self,
        dialogue_label: BaseDialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
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
        ) -> BaseDialogue.Role:
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
