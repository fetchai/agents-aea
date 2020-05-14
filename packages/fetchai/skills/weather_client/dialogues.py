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

from typing import Optional

from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description
from aea.protocols.base import Message
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues


class Dialogue(FipaDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(self, dialogue_label: DialogueLabel, is_seller: bool) -> None:
        """
        Initialize a dialogue label.

        :param dialogue_label: the identifier of the dialogue
        :param is_seller: indicates whether the agent associated with the dialogue is a seller or buyer

        :return: None
        """
        FipaDialogue.__init__(self, dialogue_label=dialogue_label, is_seller=is_seller)
        self.proposal = None  # type: Optional[Description]

    @staticmethod
    def role_from_first_message(message: Message) -> Optional[FipaDialogue.AgentRole]:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return FipaDialogue.AgentRole.BUYER


class Dialogues(Model, FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        FipaDialogues.__init__(self, self.context.agent_address)
