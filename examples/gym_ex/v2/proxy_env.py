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

"""This contains the BanditEnv."""

from abc import ABC, abstractmethod
import gym
from queue import Queue
from typing import Tuple, Any

from aea.mail.base import OutBox
from aea.protocols.base.message import Message

Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]

outbox: OutBox
public_key: str


class ProxyEnv(gym.Env, ABC):
    """This class is an implementation of the ProxyEnv, using bandit RL solution."""

    def __init__(self) -> None:
        """
        Instantiate the proxy environment.

        :return: None
        """
        super().__init__()
        self.queue = Queue()

    def step(self, action: Action) -> Feedback:
        """
        Run one time-step of the environment's dynamics.

        Standard 'step' method of a gym environment.

        - The action is given to apply_action, which does the necessary conversion and then executes it.
        - Then through receive_percept_message, the method waits for a reply from the real environment.
        - Finally, the received reply is converted into the standard observation, reward, done and info
        via message_to_percept

        More information in the comments under the other methods.

        :param action: the action sent to the step method (e.g. the output of an RL algorithm)
        :return: a Tuple containing the Feedback of Observation, Reward, Done and Info
        """
        self.apply_action(action)

        msg = self.receive_percept_message()

        observation, reward, done, info = self.message_to_percept(msg)

        return observation, reward, done, info

    @abstractmethod
    def apply_action(self, action: Action) -> None:
        """
        Execute the 'action' sent to the step function.

        This usually involves
        - Transforming the 'action' (e.g. price) that is an output of an RL algorithm into an action
        that is executable in the real environment (e.g. a proposal message containing the price).
        - Executing the action in the real environment (e.g. send the proposal to another agent).

        :param action: the action produced by an RL algorithm.
        """
        pass

    @abstractmethod
    def receive_percept_message(self) -> Message:
        """
        Receive the response of the real environment to the action taken via apply_action.

        The response is assumed to be in the form of a message, since the real environment is assumed
        to be a multi-agent system.

        It is assumed that the command to receive the message is blocking.

        :return: a Tuple containing the Feedback of Observation, Reward, Done and Info
        """
        pass

    @abstractmethod
    def message_to_percept(self, message: Message) -> Feedback:
        """
        Transform the message received from the real environment into observation, reward, done, info.

        :param message: the message received from the real environment.
        :return: a Tuple containing the Feedback of Observation, Reward, Done and Info
        """
        pass
