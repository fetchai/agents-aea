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
from typing import cast, TYPE_CHECKING

from aea.mail.base import Envelope
from aea.skills.base import Handler

if TYPE_CHECKING:
    from packages.protocols.gym.message import GymMessage
    from packages.protocols.gym.serialization import GymSerializer
    from packages.skills.gym.tasks import GymTask
else:
    from gym_protocol.message import GymMessage
    from gym_protocol.serialization import GymSerializer
    from gym_skill.tasks import GymTask


class GymHandler(Handler):
    """Gym handler."""

    SUPPORTED_PROTOCOL = "gym"

    def __init__(self, **kwargs):
        """Initialize the handler."""
        print("GymHandler.__init__: arguments: {}".format(kwargs))
        super().__init__(**kwargs)

    def setup(self) -> None:
        """Set up the handler."""
        print("Gym handler: setup method called.")

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Handle envelopes.

        :param envelope: the envelope
        :return: None
        """
        gym_msg = GymSerializer().decode(envelope.message)
        gym_msg_performative = GymMessage.Performative(gym_msg.get("performative"))
        if gym_msg_performative == GymMessage.Performative.PERCEPT:
            assert self.context.tasks is not None, "Incorrect initialization."
            assert len(self.context.tasks) == 1, "Too many tasks loaded!"
            gym_task = cast(GymTask, self.context.tasks[0])
            gym_task.proxy_env_queue.put(gym_msg)
        else:
            raise ValueError("Unexpected performative or no step_id: {}".format(gym_msg_performative))

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        print("Gym handler: teardown method called.")
