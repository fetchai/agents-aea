# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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

"""Serialization module for gym protocol."""

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.gym import gym_pb2
from packages.fetchai.protocols.gym.custom_types import AnyObject
from packages.fetchai.protocols.gym.message import GymMessage


class GymSerializer(Serializer):
    """Serialization for the 'gym' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Gym' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(GymMessage, msg)
        gym_msg = gym_pb2.GymMessage()
        gym_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        gym_msg.dialogue_starter_reference = dialogue_reference[0]
        gym_msg.dialogue_responder_reference = dialogue_reference[1]
        gym_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == GymMessage.Performative.ACT:
            performative = gym_pb2.GymMessage.Act_Performative()  # type: ignore
            action = msg.action
            AnyObject.encode(performative.action, action)
            step_id = msg.step_id
            performative.step_id = step_id
            gym_msg.act.CopyFrom(performative)
        elif performative_id == GymMessage.Performative.PERCEPT:
            performative = gym_pb2.GymMessage.Percept_Performative()  # type: ignore
            step_id = msg.step_id
            performative.step_id = step_id
            observation = msg.observation
            AnyObject.encode(performative.observation, observation)
            reward = msg.reward
            performative.reward = reward
            done = msg.done
            performative.done = done
            info = msg.info
            AnyObject.encode(performative.info, info)
            gym_msg.percept.CopyFrom(performative)
        elif performative_id == GymMessage.Performative.STATUS:
            performative = gym_pb2.GymMessage.Status_Performative()  # type: ignore
            content = msg.content
            performative.content.update(content)
            gym_msg.status.CopyFrom(performative)
        elif performative_id == GymMessage.Performative.RESET:
            performative = gym_pb2.GymMessage.Reset_Performative()  # type: ignore
            gym_msg.reset.CopyFrom(performative)
        elif performative_id == GymMessage.Performative.CLOSE:
            performative = gym_pb2.GymMessage.Close_Performative()  # type: ignore
            gym_msg.close.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        gym_bytes = gym_msg.SerializeToString()
        return gym_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Gym' message.

        :param obj: the bytes object.
        :return: the 'Gym' message.
        """
        gym_pb = gym_pb2.GymMessage()
        gym_pb.ParseFromString(obj)
        message_id = gym_pb.message_id
        dialogue_reference = (
            gym_pb.dialogue_starter_reference,
            gym_pb.dialogue_responder_reference,
        )
        target = gym_pb.target

        performative = gym_pb.WhichOneof("performative")
        performative_id = GymMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == GymMessage.Performative.ACT:
            pb2_action = gym_pb.act.action
            action = AnyObject.decode(pb2_action)
            performative_content["action"] = action
            step_id = gym_pb.act.step_id
            performative_content["step_id"] = step_id
        elif performative_id == GymMessage.Performative.PERCEPT:
            step_id = gym_pb.percept.step_id
            performative_content["step_id"] = step_id
            pb2_observation = gym_pb.percept.observation
            observation = AnyObject.decode(pb2_observation)
            performative_content["observation"] = observation
            reward = gym_pb.percept.reward
            performative_content["reward"] = reward
            done = gym_pb.percept.done
            performative_content["done"] = done
            pb2_info = gym_pb.percept.info
            info = AnyObject.decode(pb2_info)
            performative_content["info"] = info
        elif performative_id == GymMessage.Performative.STATUS:
            content = gym_pb.status.content
            content_dict = dict(content)
            performative_content["content"] = content_dict
        elif performative_id == GymMessage.Performative.RESET:
            pass
        elif performative_id == GymMessage.Performative.CLOSE:
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return GymMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
