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

- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.
"""

from typing import Dict, Optional

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues


class Dialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        agent_address: Address,
        role: BaseDialogue.Role,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        FipaDialogue.__init__(
            self, dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        self.weather_data = None  # type: Optional[Dict[str, str]]
        self.proposal = None  # type: Optional[Description]

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming or outgoing first message

        :param message: an incoming/outgoing first message
        :return: the agent's role
        """
        return FipaDialogue.AgentRole.SELLER


class Dialogues(Model, FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        FipaDialogues.__init__(self, self.context.agent_address)

    def _create_dialogue(
        self,
        dialogue_label: DialogueLabel,
        agent_address: Address,
        role: BaseDialogue.Role,
    ) -> Dialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = Dialogue(
            dialogue_label=dialogue_label, agent_address=agent_address, role=role
        )
        return dialogue
