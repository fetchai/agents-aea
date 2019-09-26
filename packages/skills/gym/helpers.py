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

"""This module contains the helpers for the 'gym' skill."""

from abc import ABC, abstractmethod
import gym
from queue import Queue
from typing import Any, Tuple, cast

from aea.mail.base import Envelope
from aea.skills.base import SkillContext
from aea.protocols.base import Message
from gym_protocol.message import GymMessage
from gym_protocol.serialization import GymSerializer

Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]

DEFAULT_GYM = 'gym'
NB_STEPS = 4000


class ProxyEnv(gym.Env):
    """This class is an implementation of the ProxyEnv, using bandit RL solution."""

    def __init__(self, skill_context: SkillContext) -> None:
        """
        Instantiate the proxy environment.

        :param skill_context: the skill context
        :return: None
        """
        super().__init__()
        self._skill_context = skill_context
        self._queue = Queue()  # type: Queue
        self._is_rl_agent_trained = False
        self._step_count = 0

    @property
    def queue(self) -> Queue:
        """Get queue."""
        return self._queue

    @property
    def is_rl_agent_trained(self) -> bool:
        """Get training status."""
        return self._is_rl_agent_trained

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
        self._step_count += 1
        step_id = self._step_count

        out_envelope = self._encode_action(action, step_id)

        # Send the envelope via the proxy agent and to the environment
        self._skill_context.outbox.put(out_envelope)

        # Wait (blocking!) for the response envelope from the environment
        gym_msg = self._queue.get(block=True, timeout=None)  # type: GymMessage

        gym_msg_step_id = gym_msg.get("step_id")
        if gym_msg_step_id == step_id:
            observation, reward, done, info = self._message_to_percept(gym_msg)
        else:
            raise ValueError("Unexpected step id! expected={}, actual={}".format(step_id, gym_msg_step_id))

        return observation, reward, done, info

    def render(self, mode='human') -> None:
        """
        Render the environment.

        :return: None
        """
        pass

    def reset(self) -> None:
        """
        Reset the environment.

        :return: None
        """
        self._step_count = 0
        self._is_rl_agent_trained = False
        gym_msg = GymMessage(performative=GymMessage.Performative.RESET)
        gym_bytes = GymSerializer().encode(gym_msg)
        envelope = Envelope(to=DEFAULT_GYM, sender=self._skill_context.agent_public_key, protocol_id=GymMessage.protocol_id,
                            message=gym_bytes)
        self._skill_context.outbox.put(envelope)

    def close(self) -> None:
        """
        Close the environment.

        :return: None
        """
        self._is_rl_agent_trained = True
        gym_msg = GymMessage(performative=GymMessage.Performative.CLOSE)
        gym_bytes = GymSerializer().encode(gym_msg)
        envelope = Envelope(to=DEFAULT_GYM, sender=self._skill_context.agent_public_key, protocol_id=GymMessage.protocol_id,
                            message=gym_bytes)
        self._skill_context.outbox.put(envelope)

    def _encode_action(self, action: Action, step_id: int) -> Envelope:
        """
        Encode the 'action' sent to the step function as one or several envelopes.

        :param action: the action that is the output of an RL algorithm.
        :param step_id: the step id
        :return: an envelope
        """
        gym_msg = GymMessage(performative=GymMessage.Performative.ACT, action=action, step_id=step_id)
        gym_bytes = GymSerializer().encode(gym_msg)
        envelope = Envelope(to=DEFAULT_GYM, sender=self._skill_context.agent_public_key, protocol_id=GymMessage.protocol_id,
                            message=gym_bytes)
        return envelope

    def _message_to_percept(self, message: Message) -> Feedback:
        """
        Transform the message received from the gym environment into observation, reward, done, info.

        :param: the message received as a response to the action performed in apply_action.
        :return: the standard feedback (observation, reward, done, info) of a gym environment.
        """
        observation = cast(Any, message.get("observation"))
        reward = cast(float, message.get("reward"))
        done = cast(bool, message.get("done"))
        info = cast(dict, message.get("info"))

        return observation, reward, done, info


class RLAgent(ABC):
    """Abstract RL Agent."""

    @abstractmethod
    def fit(self, proxy_env: ProxyEnv, nb_steps: int) -> None:
        """
        Train the agent on the given proxy environment.

        :param proxy_env: the proxy gym environment
        :param nb_steps: number of training steps to be performed.
        :return: None
        """
