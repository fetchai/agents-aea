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
"""This contains the proxy gym environment."""

import sys
import time
from queue import Queue
from threading import Thread
from typing import Any, Optional, Tuple, cast

import gym

from aea.common import Address
from aea.helpers.base import locate
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue


sys.modules["packages.fetchai.connections.gym"] = locate(  # isort:skip
    "packages.fetchai.connections.gym"
)
sys.modules["packages.fetchai.protocols.gym"] = locate(  # isort:skip
    "packages.fetchai.protocols.gym"
)


from packages.fetchai.connections.gym.connection import (  # noqa: E402  # pylint: disable=wrong-import-position
    PUBLIC_ID as GYM_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.gym.dialogues import (  # noqa: E402  # pylint: disable=wrong-import-position
    GymDialogue as BaseGymDialogue,
)
from packages.fetchai.protocols.gym.dialogues import (  # noqa: E402  # pylint: disable=wrong-import-position
    GymDialogues as BaseGymDialogues,
)
from packages.fetchai.protocols.gym.message import (  # noqa: E402  # pylint: disable=wrong-import-position
    GymMessage,
)

from .agent import ProxyAgent  # noqa: E402  # pylint: disable=wrong-import-position


Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]

GymDialogue = BaseGymDialogue

GymDialogues = BaseGymDialogues


def role_from_first_message(  # pylint: disable=unused-argument
    message: Message, receiver_address: Address
) -> BaseDialogue.Role:
    """Infer the role of the agent from an incoming/outgoing first message

    :param message: an incoming/outgoing first message
    :param receiver_address: the address of the receiving agent
    :return: The role of the agent
    """
    return BaseGymDialogue.Role.AGENT


class ProxyEnv(gym.Env):
    """This class implements a proxy gym environment."""

    _agent_thread: Optional[Thread]

    def __init__(self, gym_env: gym.Env) -> None:
        """
        Instantiate the proxy environment.

        :param gym_env: gym environment
        """
        super().__init__()
        self._queue: Queue = Queue()
        self._action_counter: int = 0
        self.gym_address = str(GYM_CONNECTION_PUBLIC_ID)
        self._agent = ProxyAgent(
            name="proxy", gym_env=gym_env, proxy_env_queue=self._queue
        )
        self._agent_thread = Thread(target=self._agent.start)
        self._active_dialogue = None  # type: Optional[GymDialogue]
        self.gym_skill = "fetchai/gym:0.1.0"
        self.gym_dialogues = GymDialogues(self.gym_skill, role_from_first_message)

    @property
    def active_dialogue(self) -> GymDialogue:
        """Get the active dialogue."""
        return cast(GymDialogue, self._active_dialogue)

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

    def render(self, mode: str = "human") -> None:
        """
        Render the environment.

        :param mode: the run mode
        """
        self._agent.runtime.multiplexer.default_connection.channel.gym_env.render(mode)  # type: ignore

    def reset(self) -> None:
        """Reset the environment."""
        if not self._agent.runtime.multiplexer.is_connected:
            self._connect()
        gym_msg, gym_dialogue = self.gym_dialogues.create(
            counterparty=self.gym_address,
            performative=GymMessage.Performative.RESET,
        )
        gym_dialogue = cast(GymDialogue, gym_dialogue)
        self._active_dialogue = gym_dialogue
        self._agent.outbox.put_message(message=gym_msg)

        # Wait (blocking!) for the response envelope from the environment
        in_envelope = self._queue.get(block=True, timeout=None)  # type: GymMessage

        self._decode_status(cast(Envelope, in_envelope))

    def close(self) -> None:
        """Close the environment."""
        last_msg = self.active_dialogue.last_message
        if last_msg is None:
            raise ValueError("Cannot retrieve last message.")
        gym_msg = self.active_dialogue.reply(
            performative=GymMessage.Performative.CLOSE,
            target_message=last_msg,
        )
        self._agent.outbox.put_message(message=gym_msg)

        self._disconnect()

    def _connect(self) -> None:
        """Connect to this proxy environment. It starts a proxy agent that can interact with the framework."""
        if cast(Thread, self._agent_thread).is_alive():
            raise ValueError("Agent already running.")
        cast(Thread, self._agent_thread).start()

        while not self._agent.runtime.is_running:  # check agent completely running
            time.sleep(0.01)

    def _disconnect(self) -> None:
        """Disconnect from this proxy environment. It stops the proxy agent and kills its thread."""
        self._agent.stop()
        cast(Thread, self._agent_thread).join()
        self._agent_thread = None

    def _encode_and_send_action(self, action: Action, step_id: int) -> None:
        """
        Encode the 'action' sent to the step function and send.

        :param action: the action that is the output of an RL algorithm.
        :param step_id: the step id
        """
        last_msg = self.active_dialogue.last_message
        if last_msg is None:
            raise ValueError("Cannot retrieve last message.")
        gym_msg = self.active_dialogue.reply(
            performative=GymMessage.Performative.ACT,
            target_message=last_msg,
            action=GymMessage.AnyObject(action),
            step_id=step_id,
        )
        # Send the message via the proxy agent and to the environment
        self._agent.outbox.put_message(message=gym_msg)

    def _decode_percept(self, envelope: Envelope, expected_step_id: int) -> GymMessage:
        """
        Receive the response from the gym environment in the form of an envelope and decode it.

        The response is a PERCEPT message containing the usual 'observation', 'reward', 'done', 'info' parameters.

        :param envelope: the envelope
        :param expected_step_id: the expected step id
        :return: a message received as a response to the action performed in apply_action.
        """
        if envelope is not None:
            if (
                envelope.protocol_specification_id
                == GymMessage.protocol_specification_id
            ):
                gym_msg = cast(GymMessage, envelope.message)
                gym_dialogue = self.gym_dialogues.update(gym_msg)
                if not gym_dialogue:
                    raise ValueError("Could not udpate dialogue.")
                if not gym_dialogue == self.active_dialogue:
                    raise ValueError("Dialogue does not match.")
                if (
                    gym_msg.performative == GymMessage.Performative.PERCEPT
                    and gym_msg.step_id == expected_step_id
                ):
                    return gym_msg
                raise ValueError(
                    "Unexpected performative or no step_id: {}".format(
                        gym_msg.performative
                    )
                )
            raise ValueError(
                "Unknown protocol_specification_id: {}".format(
                    envelope.protocol_specification_id
                )
            )
        raise ValueError("Missing envelope.")

    def _decode_status(self, envelope: Envelope) -> None:
        """
        Receive the response from the gym environment in the form of an envelope and decode it.

        The response is a STATUS message.

        :param envelope: the envelope
        :return: a message received as a response to the action performed in apply_action.
        """
        if envelope is not None:
            if (
                envelope.protocol_specification_id
                == GymMessage.protocol_specification_id
            ):
                gym_msg = cast(GymMessage, envelope.message)
                gym_dialogue = self.gym_dialogues.update(gym_msg)
                if not gym_dialogue:
                    raise ValueError("Could not udpate dialogue.")
                if not gym_dialogue == self.active_dialogue:
                    raise ValueError("Dialogue does not match.")
                if (
                    gym_msg.performative == GymMessage.Performative.STATUS
                    and gym_msg.content.get("reset", "failure") == "success"
                ):

                    return None
                raise ValueError(
                    "Unexpected performative or no step_id: {}".format(
                        gym_msg.performative
                    )
                )
            raise ValueError(
                "Unknown protocol_id: {}".format(envelope.protocol_specification_id)
            )
        raise ValueError("Missing envelope.")

    @staticmethod
    def _message_to_percept(message: GymMessage) -> Feedback:
        """
        Transform the message received from the gym environment into observation, reward, done, info.

        :param message: the message received as a response to the action performed in apply_action.
        :return: the standard feedback (observation, reward, done, info) of a gym environment.
        """
        observation = cast(Any, message.observation.any)
        reward = cast(float, message.reward)
        done = cast(bool, message.done)
        info = cast(dict, message.info.any)

        return observation, reward, done, info
