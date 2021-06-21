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

"""This package contains dialogues used by the advanced_data_request skill."""

from typing import Any

from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.skills.base import Model

from packages.fetchai.protocols.http.dialogues import HttpDialogue as BaseHttpDialogue
from packages.fetchai.protocols.http.dialogues import HttpDialogues as BaseHttpDialogues
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.prometheus.dialogues import (
    PrometheusDialogue as BasePrometheusDialogue,
)
from packages.fetchai.protocols.prometheus.dialogues import (
    PrometheusDialogues as BasePrometheusDialogues,
)


HttpDialogue = BaseHttpDialogue
PrometheusDialogue = BasePrometheusDialogue


class HttpDialogues(Model, BaseHttpDialogues):
    """This class keeps track of all http dialogues."""

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
            :return: The role of the agent in this dialogue
            """
            if (
                message.performative == HttpMessage.Performative.REQUEST
                and message.sender != receiver_address
            ) or (
                message.performative == HttpMessage.Performative.RESPONSE
                and message.sender == receiver_address
            ):
                return BaseHttpDialogue.Role.SERVER

            return BaseHttpDialogue.Role.CLIENT

        BaseHttpDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )


class PrometheusDialogues(Model, BasePrometheusDialogues):
    """The dialogues class keeps track of all prometheus dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """
        self.enabled = kwargs.pop("enabled", False)
        self.metrics = kwargs.pop("metrics", [])

        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return PrometheusDialogue.Role.AGENT

        BasePrometheusDialogues.__init__(
            self,
            self_address=str(self.skill_id),
            role_from_first_message=role_from_first_message,
        )
