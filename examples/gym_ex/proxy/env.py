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

"""This contains the proxy gym environment."""

import sys
import time
from queue import Queue
from threading import Thread
from typing import Any, Tuple, cast

import gym

from aea.configurations.base import PublicId
from aea.helpers.base import locate
from aea.mail.base import Envelope
from aea.protocols.base import Message

sys.modules["packages.fetchai.connections.gym"] = locate(
    "packages.fetchai.connections.gym"
)
sys.modules["packages.fetchai.protocols.gym"] = locate("packages.fetchai.protocols.gym")
from packages.fetchai.protocols.gym.message import GymMessage  # noqa: E402

from .agent import ProxyAgent  # noqa: E402

Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]

DEFAULT_GYM = "gym"


class ProxyEnv(gym.Env):
    """This class implements a proxy gym environment."""

    def __init__(self, gym_env: gym.Env) -> None:
        """
        Instantiate the proxy environment.

        :param gym_env: gym environment
        :return: None
        """
        super().__init__()
        self._queue = Queue()
        self._action_counter = 0
        self._agent = ProxyAgent(
            name="proxy", gym_env=gym_env, proxy_env_queue=self._queue
        )
        self._agent_address = self._agent.identity.address
        self._agent_thread = Thread(target=self._agent.start)

    def step(self, action: Action) -> Feedback:
        """
        Run one time-step of the environment's dynamics.

        Mirrors the standard 'step' method of a gym environment.

        - The action is given to _encode_action, which does the necessary conversion to an envelope.
        - The envelope is given to the outbox of the proxy agent.
        - The method blocks until the _queue returns an envelope.
        - The envelope is decoded with _decode_percept to a message.
        - The message is converted into the standard observation, reward, done and info via _message_to_percept

        :param action: the action sent to the step method (e.g. the output of an RL algorithm)
        :return: a Tuple containing the Feedback of Observation, Reward, Done and Info
        """
        self._action_counter += 1
        step_id = self._action_counter

        self._encode_and_send_action(action, step_id)

        # Wait (blocking!) for the response envelope from the environment
        in_envelope = self._queue.get(block=True, timeout=None)  # type: Envelope

        msg = self._decode_percept(in_envelope, step_id)

        observation, reward, done, info = self._message_to_percept(msg)

        return observation, reward, done, info

    def render(self, mode="human") -> None:
        """
        Render the environment.

        :return: None
        """
        # TODO: adapt this line to the new APIs. We no longer have a mailbox.
        self._agent.mailbox._connection.channel.gym_env.render(mode)

    def reset(self) -> None:
        """
        Reset the environment.

        :return: None
        """
        if not self._agent.multiplexer.is_connected:
            self._connect()
        gym_msg = GymMessage(performative=GymMessage.Performative.RESET)
        gym_msg.counterparty = DEFAULT_GYM
        self._agent.outbox.put_message(message=gym_msg, sender=self._agent_address)

    def close(self) -> None:
        """
        Close the environment.

        :return: None
        """
        gym_msg = GymMessage(performative=GymMessage.Performative.CLOSE)
        gym_msg.counterparty = DEFAULT_GYM
        self._agent.outbox.put_message(message=gym_msg, sender=self._agent_address)

        self._disconnect()

    def _connect(self):
        """
        Connect to this proxy environment. It starts a proxy agent that can interact with the framework.

        :return: None
        """
        assert not self._agent_thread.is_alive(), "Agent already running."
        self._agent_thread.start()
        while not self._agent.multiplexer.is_connected:
            time.sleep(0.1)

    def _disconnect(self):
        """
        Disconnect from this proxy environment. It stops the proxy agent and kills its thread.

        :return: None
        """
        self._agent.stop()
        self._agent_thread.join()
        self._agent_thread = None

    def _encode_and_send_action(self, action: Action, step_id: int) -> None:
        """
        Encode the 'action' sent to the step function and send.

        :param action: the action that is the output of an RL algorithm.
        :param step_id: the step id
        :return: an envelope
        """
        gym_msg = GymMessage(
            performative=GymMessage.Performative.ACT,
            action=GymMessage.AnyObject(action),
            step_id=step_id,
        )
        gym_msg.counterparty = DEFAULT_GYM
        # Send the message via the proxy agent and to the environment
        self._agent.outbox.put_message(message=gym_msg, sender=self._agent_address)

    def _decode_percept(self, envelope: Envelope, expected_step_id: int) -> Message:
        """
        Receive the response from the gym environment in the form of an envelope and decode it.

        The response is a PERCEPT message containing the usual 'observation', 'reward', 'done', 'info' parameters.

        :param expected_step_id: the expected step id
        :return: a message received as a response to the action performed in apply_action.
        """
        if envelope is not None:
            if envelope.protocol_id == PublicId.from_str("fetchai/gym:0.3.0"):
                gym_msg = envelope.message
                if (
                    gym_msg.performative == GymMessage.Performative.PERCEPT
                    and gym_msg.step_id == expected_step_id
                ):
                    return gym_msg
                else:
                    raise ValueError(
                        "Unexpected performative or no step_id: {}".format(
                            gym_msg.performative
                        )
                    )
            else:
                raise ValueError("Unknown protocol_id: {}".format(envelope.protocol_id))
        else:
            raise ValueError("Missing envelope.")

    def _message_to_percept(self, message: Message) -> Feedback:
        """
        Transform the message received from the gym environment into observation, reward, done, info.

        :param: the message received as a response to the action performed in apply_action.
        :return: the standard feedback (observation, reward, done, info) of a gym environment.
        """
        observation = cast(Any, message.observation.any)
        reward = cast(float, message.reward)
        done = cast(bool, message.done)
        info = cast(dict, message.info.any)

        return observation, reward, done, info
