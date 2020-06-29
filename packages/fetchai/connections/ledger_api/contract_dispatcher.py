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

"""This module contains the implementation of the contract API request dispatcher."""
from aea.crypto.registries import Registry
from aea.helpers.dialogue.base import (
    Dialogue as BaseDialogue,
    DialogueLabel as BaseDialogueLabel,
    Dialogues as BaseDialogues,
)
from aea.mail.base import Envelope
from aea.protocols.base import Message

from packages.fetchai.connections.ledger_api.base import (
    CONNECTION_ID,
    RequestDispatcher,
)
from packages.fetchai.protocols.contract_api.dialogues import ContractApiDialogue
from packages.fetchai.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)


class ContractApiDialogues(BaseContractApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        BaseContractApiDialogues.__init__(self, str(CONNECTION_ID))

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return ContractApiDialogue.AgentRole.LEDGER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> ContractApiDialogue:
        """
        Create an instance of contract API dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = ContractApiDialogue(
            dialogue_label=dialogue_label, agent_address=str(CONNECTION_ID), role=role,
        )
        return dialogue


class ContractApiRequestDispatcher(RequestDispatcher):
    """Implement the contract API request dispatcher."""

    def __init__(self, **kwargs):
        """Initialize the dispatcher."""
        super().__init__(**kwargs)
        self._contract_api_dialogues = ContractApiDialogues()

    @property
    def dialogues(self) -> BaseDialogues:
        """Get the dialouges."""
        return self._contract_api_dialogues

    def get_error_message(self, *args) -> Message:
        pass

    @property
    def registry(self) -> Registry:
        pass

    def get_message(self, envelope: Envelope) -> Message:
        pass

    def get_ledger_id(self, message: Message) -> str:
        pass
