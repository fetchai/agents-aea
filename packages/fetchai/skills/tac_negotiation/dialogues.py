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

from typing import cast

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.search.models import Query
from aea.protocols.base import Message
from aea.skills.base import Model

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue, FipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.skills.tac_negotiation.helpers import SUPPLY_DATAMODEL_NAME


Dialogue = FipaDialogue


class Dialogues(Model, FipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)
        FipaDialogues.__init__(self, self.context.agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming or outgoing first message

        :param message: an incoming/outgoing first message
        :return: the agent's role
        """
        fipa_message = cast(FipaMessage, message)
        query = cast(Query, fipa_message.query)
        if query.model is not None:
            is_seller = (
                query.model.name == SUPPLY_DATAMODEL_NAME
            )  # the counterparty is querying for supply
            if is_seller:
                return FipaDialogue.AgentRole.SELLER
            else:
                return FipaDialogue.AgentRole.BUYER
        else:
            raise ValueError("Query has no data model!")
