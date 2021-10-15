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
from queue import Queue
from typing import Any, Optional, Tuple, cast

import gym

from aea.protocols.base import Message
from aea.skills.base import SkillContext

from packages.fetchai.connections.gym.connection import (
    PUBLIC_ID as GYM_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.gym.dialogues import GymDialogue, GymDialogues


Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]

NB_STEPS = 500


class ProxyEnv(gym.Env):
    """This class is an implementation of the ProxyEnv, using bandit RL solution."""

    def __init__(self, skill_context: SkillContext) -> None:
        """
        Instantiate the proxy environment.

        :param skill_context: the skill context
        """
        super().__init__()
        self._skill_context = skill_context
        self._queue = Queue()  # type: Queue
        self._is_rl_agent_trained = False
        self._step_count = 0
        self._active_dialogue = None  # type: Optional[GymDialogue]
        self.gym_address = str(GYM_CONNECTION_PUBLIC_ID)

    @property
    def gym_dialogues(self) -> GymDialogues:
        """Get the gym dialogues."""
        return cast(GymDialogues, self._skill_context.gym_dialogues)

    @property
    def active_gym_dialogue(self) -> GymDialogue:
        """Get the active gym dialogue."""
        if self._active_dialogue is None:
            raise ValueError("GymDialogue not set yet.")
        return self._active_dialogue

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

        self._encode_and_send_action(action, step_id)

        # Wait (blocking!) for the response envelope from the environment
        gym_msg = self._queue.get(block=True, timeout=None)  # type: GymMessage

        if gym_msg.performative != GymMessage.Performative.PERCEPT:
            raise ValueError(
                "Unexpected performative. Expected={} got={}".format(
                    GymMessage.Performative.PERCEPT, gym_msg.performative
                )
            )

        if gym_msg.step_id == step_id:
            observation, reward, done, info = self._message_to_percept(gym_msg)
        else:
            raise ValueError(
                "Unexpected step id! expected={}, actual={}".format(
                    step_id, gym_msg.step_id
                )
            )

        return observation, reward, done, info

    def render(self, mode: str = "human") -> None:
        """
        Render the environment.

        :param mode: the mode
        """

    def reset(self) -> None:
        """Reset the environment."""
        self._step_count = 0
        self._is_rl_agent_trained = False
        gym_msg, gym_dialogue = self.gym_dialogues.create(
            counterparty=self.gym_address, performative=GymMessage.Performative.RESET,
        )
        gym_dialogue = cast(GymDialogue, gym_dialogue)
        self._active_dialogue = gym_dialogue
        self._skill_context.outbox.put_message(message=gym_msg)

        # Wait (blocking!) for the response envelope from the environment
        response_msg = self._queue.get(block=True, timeout=None)  # type: GymMessage

        if response_msg.performative != GymMessage.Performative.STATUS:
            raise ValueError(
                "Unexpected performative. Expected={} got={}".format(
                    GymMessage.Performative.STATUS, response_msg.performative
                )
            )

    def close(self) -> None:
        """Close the environment."""
        self._is_rl_agent_trained = True
        last_msg = self.active_gym_dialogue.last_message
        if last_msg is None:  # pragma: nocover
            raise ValueError("Cannot retrieve last message.")
        gym_msg = self.active_gym_dialogue.reply(
            performative=GymMessage.Performative.CLOSE, target_message=last_msg,
        )
        self._skill_context.outbox.put_message(message=gym_msg)

    def _encode_and_send_action(self, action: Action, step_id: int) -> None:
        """
        Encode the 'action' sent to the step function and send it.

        :param action: the action that is the output of an RL algorithm.
        :param step_id: the step id
        """
        last_msg = self.active_gym_dialogue.last_message
        if last_msg is None:  # pragma: nocover
            raise ValueError("Cannot retrieve last message.")
        gym_msg = self.active_gym_dialogue.reply(
            performative=GymMessage.Performative.ACT,
            target_message=last_msg,
            action=GymMessage.AnyObject(action),
            step_id=step_id,
        )
        # Send the message via the proxy agent and to the environment
        self._skill_context.outbox.put_message(message=gym_msg)

    @staticmethod
    def _message_to_percept(message: Message) -> Feedback:
        """
        Transform the message received from the gym environment into observation, reward, done, info.

        :param message: the message received as a response to the action performed in apply_action.
        :return: the standard feedback (observation, reward, done, info) of a gym environment.
        """
        msg = cast(GymMessage, message)
        observation = msg.observation.any
        reward = msg.reward
        done = msg.done
        info = msg.info.any

        return observation, reward, done, info


class RLAgent(ABC):
    """Abstract RL Agent."""

    @abstractmethod
    def fit(self, proxy_env: ProxyEnv, nb_steps: int) -> None:
        """
        Train the agent on the given proxy environment.

        :param proxy_env: the proxy gym environment
        :param nb_steps: number of training steps to be performed.
        """
