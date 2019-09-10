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

"""This contains the proxy agent class."""

import gym
from queue import Queue
from typing import Optional

from aea.agent import Agent
from aea.channel.gym import GymConnection
from aea.mail.base import Envelope, MailBox


class ProxyAgent(Agent):
    """This class implements a simple RL agent."""

    def __init__(self, name: str, env: gym.Env, proxy_env_queue: Queue) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param env: gym environment
        :param proxy_env_queue: the queue of the proxy environment
        :return: None
        """
        super().__init__(name, timeout=0)
        self.proxy_env_queue = proxy_env_queue
        self.mailbox = MailBox(GymConnection(self.crypto.public_key, env))

    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """
        pass

    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """
        pass

    def react(self) -> None:
        """
        React to incoming events.

        :return: None
        """
        while not self.inbox.empty():
            envelope = self.inbox.get_nowait()  # type: Optional[Envelope]
            if envelope is not None:
                if envelope.protocol_id == 'gym':
                    self.proxy_env_queue.put(envelope)
                else:
                    raise ValueError("Unknown protocol_id: {}".format(envelope.protocol_id))

    def update(self) -> None:
        """Update the current state of the agent.

        :return None
        """
        pass

    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """
        pass
