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

"""This contains the BanditProxyEnv."""

import gym
import logging
from threading import Thread
from typing import Tuple, Any, Optional

from aea.channel.gym import DEFAULT_GYM
from aea.mail.base import Envelope
from aea.protocols.base.message import Message
from aea.protocols.gym.message import GymMessage
from aea.protocols.gym.serialization import GymSerializer

from .proxy_agent import ProxyAgent
from .proxy_env import ProxyEnv

logger = logging.getLogger(__name__)

Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]


class BanditProxyEnv(ProxyEnv):
    metadata = {'render.modes': ['human']}

    def __init__(self, gym_env: gym.Env):
        super().__init__()
        self.action_counter = 0
        self.proxy_agent = ProxyAgent(name="proxy", env=gym_env, proxy_env_queue=self.queue)
        self.proxy_agent_thread = Thread(target=self.proxy_agent.start)

    def connect(self):
        self.proxy_agent_thread.start()

    def disconnect(self):
        self.proxy_agent.stop()
        self.proxy_agent_thread.join()
        self.proxy_agent_thread = None

    def apply_action(self, action: Action) -> None:
        self.action_counter += 1

        step_id = self.action_counter
        gym_msg = GymMessage(performative=GymMessage.Performative.ACT, action=action, step_id=step_id)
        gym_bytes = GymSerializer().encode(gym_msg)
        self.proxy_agent.outbox.put_message(to=DEFAULT_GYM, sender=self.proxy_agent.crypto.public_key,
                                            protocol_id=GymMessage.protocol_id, message=gym_bytes)

    def receive_percept_message(self) -> Message:
        envelope = self.queue.get(block=True, timeout=None)  # type: Optional[Envelope]
        expected_step_id = self.action_counter

        # assert to ensure envelope is an instance of Envelope
        if envelope is not None:
            if envelope.protocol_id == 'gym':
                gym_msg = GymSerializer().decode(envelope.message)
                gym_msg_performative = GymMessage.Performative(gym_msg.get("performative"))
                gym_msg_step_id = gym_msg.get("step_id")
                if gym_msg_performative == GymMessage.Performative.PERCEPT and gym_msg_step_id == expected_step_id:
                    return gym_msg
                else:
                    raise ValueError("Unexpected performative or no step_id: {}".format(gym_msg_performative))
            else:
                raise ValueError("Unknown protocol_id: {}".format(envelope.protocol_id))
        else:
            raise ValueError("Missing envelope.")

    def message_to_percept(self, message: Message) -> Feedback:
        observation = message.get("observation")
        done = message.get("done")
        info = message.get("info")
        reward = message.get("reward")

        return observation, done, reward, info

    def render(self, mode='human'):
        pass

    def reset(self):
        pass
