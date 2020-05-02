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

"""This module contains the handler for the 'gym' skill."""

from typing import cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.gym.rl_agent import DEFAULT_NB_STEPS
from packages.fetchai.skills.gym.tasks import GymTask


class GymHandler(Handler):
    """Gym handler."""

    SUPPORTED_PROTOCOL = GymMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        nb_steps = kwargs.pop("nb_steps", DEFAULT_NB_STEPS)
        super().__init__(**kwargs)
        self.task = GymTask(self.context, nb_steps)

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("Gym handler: setup method called.")
        # launch the task
        self.task.setup()
        self.task.execute()

    def handle(self, message: Message) -> None:
        """
        Handle messages.

        :param message: the message
        :return: None
        """
        gym_msg = cast(GymMessage, message)
        if gym_msg.performative == GymMessage.Performative.PERCEPT:
            self.task.proxy_env_queue.put(gym_msg)
        else:
            raise ValueError(
                "Unexpected performative or no step_id: {}".format(gym_msg.performative)
            )

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        self.context.logger.info("Gym handler: teardown method called.")
        self.task.teardown()
