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

"""This module contains the classes required for dialogue management."""

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.protocols.base import Message
from aea.protocols.default.dialogues import DefaultDialogue as BaseDefaultDialogue
from aea.protocols.default.dialogues import DefaultDialogues as BaseDefaultDialogues
from aea.skills.base import Model

DefaultDialogue = BaseDefaultDialogue


class DefaultDialogues(Model, BaseDefaultDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        BaseDefaultDialogues.__init__(self, self.context.agent_name)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return DefaultDialogue.Role.AGENT

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> DefaultDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = DefaultDialogue(
            dialogue_label=dialogue_label,
            agent_address=self.context.agent_name,
            role=role,
        )
        return dialogue
