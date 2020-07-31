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

from typing import Dict

from aea.helpers.dialogue.base import Dialogue
from aea.helpers.dialogue.base import DialogueLabel
from aea.protocols.base import Message
from aea.protocols.default.dialogues import DefaultDialogue as BaseDefaultDialogue
from aea.protocols.default.dialogues import DefaultDialogues as BaseDefaultDialogues
from aea.skills.base import Model

from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.protocols.tac.dialogues import TacDialogue as BaseTacDialogue
from packages.fetchai.protocols.tac.dialogues import TacDialogues as BaseTacDialogues


DefaultDialogue = BaseDefaultDialogue


class DefaultDialogues(Model, BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseDefaultDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> Dialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return DefaultDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: Dialogue.Role,
    ) -> DefaultDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = DefaultDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


OefSearchDialogue = BaseOefSearchDialogue


class OefSearchDialogues(Model, BaseOefSearchDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseOefSearchDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> Dialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return BaseOefSearchDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: Dialogue.Role,
    ) -> OefSearchDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = OefSearchDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


TacDialogue = BaseTacDialogue


class TacDialogues(Model, BaseTacDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseTacDialogues.__init__(self, self.context.agent_address)
        self._dialogue_by_address = {}  # type: Dict[str, Dialogue]

    @property
    def dialogue_by_address(self) -> Dict[str, Dialogue]:
        """Get the dialogue by address."""
        return self._dialogue_by_address

    @staticmethod
    def role_from_first_message(message: Message) -> Dialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return TacDialogue.Role.CONTROLLER

    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: Dialogue.Role,
    ) -> TacDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = TacDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        self._dialogue_by_address[dialogue_label.dialogue_opponent_addr] = dialogue
        return dialogue
