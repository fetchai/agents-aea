# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""This contains the proxy agent class."""
import os
import sys
from queue import Queue

import gym

from aea.agent import Agent
from aea.configurations.base import ConnectionConfig
from aea.helpers.base import locate
from aea.identity.base import Identity
from aea.mail.base import Envelope


sys.modules["packages.fetchai.connections.gym"] = locate(  # isort:skip
    "packages.fetchai.connections.gym"
)


from packages.fetchai.connections.gym.connection import (  # noqa: E402  # pylint: disable=wrong-import-position
    GymConnection,
)


ADDRESS = "some_address"
PUBLIC_KEY = "some_public_key"


class ProxyAgent(Agent):
    """This class implements a proxy agent to be used by a proxy environment."""

    def __init__(self, name: str, gym_env: gym.Env, proxy_env_queue: Queue) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param gym_env: gym environment
        :param proxy_env_queue: the queue of the proxy environment
        """
        identity = Identity(name, ADDRESS, PUBLIC_KEY)
        configuration = ConnectionConfig(connection_id=GymConnection.connection_id)
        super().__init__(
            identity,
            [
                GymConnection(
                    gym_env,
                    identity=identity,
                    configuration=configuration,
                    data_dir=os.getcwd(),
                )
            ],
            period=0.01,
        )
        self.proxy_env_queue = proxy_env_queue

    def setup(self) -> None:
        """Set up the agent."""

    def act(self) -> None:
        """Perform actions."""

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Handle envelope.

        :param envelope: the envelope
        """
        if envelope is not None:
            self.proxy_env_queue.put(envelope)

    def teardown(self) -> None:
        """Tear down the agent."""
