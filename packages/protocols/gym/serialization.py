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

"""Serialization for the Gym protocol."""
import base64
import copy
import json
import pickle
import sys
from typing import Any, TYPE_CHECKING, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.gym.message import GymMessage
else:
    from gym_protocol.message import GymMessage  # pragma: no cover


class GymSerializer(Serializer):
    """Serialization for the Gym protocol."""

    def encode(self, msg: Message) -> bytes:
        """
        Decode the message.

        :param msg: the message object
        :return: the bytes
        """
        msg = cast(GymMessage, msg)
        new_body = copy.copy(msg.body)
        new_body["performative"] = msg.performative.value

        if msg.performative == GymMessage.Performative.ACT:
            action = msg.action  # type: Any
            action_bytes = base64.b64encode(pickle.dumps(action)).decode("utf-8")
            new_body["action"] = action_bytes
            new_body["step_id"] = msg.step_id
        elif msg.performative == GymMessage.Performative.PERCEPT:
            # observation, reward and info are gym implementation specific, done is boolean
            observation = msg.observation
            observation_bytes = base64.b64encode(pickle.dumps(observation)).decode("utf-8")
            new_body["observation"] = observation_bytes
            reward = msg.reward  # type: Any
            reward_bytes = base64.b64encode(pickle.dumps(reward)).decode("utf-8")
            new_body["reward"] = reward_bytes
            info = msg.info  # type: Any
            info_bytes = base64.b64encode(pickle.dumps(info)).decode("utf-8")
            new_body["info"] = info_bytes
            new_body["step_id"] = msg.step_id

        gym_message_bytes = json.dumps(new_body).encode("utf-8")
        return gym_message_bytes

    def decode(self, obj: bytes) -> Message:
        """
        Decode the message.

        :param obj: the bytes object
        :return: the message
        """
        json_msg = json.loads(obj.decode("utf-8"))
        performative = GymMessage.Performative(json_msg["performative"])
        new_body = copy.copy(json_msg)
        new_body["performative"] = performative

        if performative == GymMessage.Performative.ACT:
            action_bytes = base64.b64decode(json_msg["action"])
            action = pickle.loads(action_bytes)
            new_body["action"] = action
            new_body["step_id"] = json_msg["step_id"]
        elif performative == GymMessage.Performative.PERCEPT:
            # observation, reward and info are gym implementation specific, done is boolean
            observation_bytes = base64.b64decode(json_msg["observation"])
            observation = pickle.loads(observation_bytes)
            new_body["observation"] = observation
            reward_bytes = base64.b64decode(json_msg["reward"])
            reward = pickle.loads(reward_bytes)
            new_body["reward"] = reward
            info_bytes = base64.b64decode(json_msg["info"])
            info = pickle.loads(info_bytes)
            new_body["info"] = info
            new_body["step_id"] = json_msg["step_id"]

        gym_message = GymMessage(performative=performative, body=new_body)
        return gym_message
