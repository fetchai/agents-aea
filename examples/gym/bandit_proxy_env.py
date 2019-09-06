# import os, subprocess, time, signal

import gym
from gym import error, spaces, utils
from gym.utils import seeding

from aea.protocols.base.message import Message
from aea.agent import Agent
from aea.channel.gym import GymChannel, GymConnection, DEFAULT_GYM
from aea.mail.base import Envelope, MailBox
from aea.protocols.gym.message import GymMessage
from aea.protocols.gym.serialization import GymSerializer
from env import BanditNArmedRandom

import numpy as np

from typing import List, Tuple, Any

import logging

logger = logging.getLogger(__name__)

Action = Any
Observation = Any
Reward = float
Done = bool
Info = dict
Feedback = Tuple[Observation, Reward, Done, Info]


class BanditProxyEnv(ProxyEnv):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super().__init__()
        
        # protocol object
        # outbox of the agent
        # queue between the training thread and the main thread that receives messages

    def apply_action(self, action: Action) -> None:
        # Increment the counter
        self.action_counter += 1

        # Get the good
        good_id = self._get_random_next_good()

        # Pick the best price based on own model.
        good_price_model = self.good_price_models[good_id]
        price = good_price_model.get_price_expectation()

        action = [good_id, np.array([price])]
        step_id = self.action_counter

        # Store action for step id
        self.actions[step_id] = action

        print("step_id={}, action taken: {}".format(step_id, action))
        # create and serialize the message
        gym_msg = GymMessage(performative=GymMessage.Performative.ACT, action=action, step_id=step_id)
        gym_bytes = GymSerializer().encode(gym_msg)
        self.mailbox.outbox.put_message(to=DEFAULT_GYM, sender=self.crypto.public_key,
                                        protocol_id=GymMessage.protocol_id, message=gym_bytes)

    def message_to_percept(self, message) -> Feedback:
        observation = gym_msg.get("observation")
        done = gym_msg.get("done")
        info = gym_msg.get("info")
        reward = gym_msg.get("reward")

        # step_id = gym_msg.get("step_id")

        return observation, done, reward, info