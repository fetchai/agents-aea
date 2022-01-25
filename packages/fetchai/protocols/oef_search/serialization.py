# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 fetchai
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

"""Serialization module for oef_search protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.fetchai.protocols.oef_search import oef_search_pb2
from packages.fetchai.protocols.oef_search.custom_types import (
    AgentsInfo,
    Description,
    OefErrorOperation,
    Query,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage


class OefSearchSerializer(Serializer):
    """Serialization for the 'oef_search' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'OefSearch' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(OefSearchMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        oef_search_msg = oef_search_pb2.OefSearchMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == OefSearchMessage.Performative.REGISTER_SERVICE:
            performative = oef_search_pb2.OefSearchMessage.Register_Service_Performative()  # type: ignore
            service_description = msg.service_description
            Description.encode(performative.service_description, service_description)
            oef_search_msg.register_service.CopyFrom(performative)
        elif performative_id == OefSearchMessage.Performative.UNREGISTER_SERVICE:
            performative = oef_search_pb2.OefSearchMessage.Unregister_Service_Performative()  # type: ignore
            service_description = msg.service_description
            Description.encode(performative.service_description, service_description)
            oef_search_msg.unregister_service.CopyFrom(performative)
        elif performative_id == OefSearchMessage.Performative.SEARCH_SERVICES:
            performative = oef_search_pb2.OefSearchMessage.Search_Services_Performative()  # type: ignore
            query = msg.query
            Query.encode(performative.query, query)
            oef_search_msg.search_services.CopyFrom(performative)
        elif performative_id == OefSearchMessage.Performative.SEARCH_RESULT:
            performative = oef_search_pb2.OefSearchMessage.Search_Result_Performative()  # type: ignore
            agents = msg.agents
            performative.agents.extend(agents)
            agents_info = msg.agents_info
            AgentsInfo.encode(performative.agents_info, agents_info)
            oef_search_msg.search_result.CopyFrom(performative)
        elif performative_id == OefSearchMessage.Performative.SUCCESS:
            performative = oef_search_pb2.OefSearchMessage.Success_Performative()  # type: ignore
            agents_info = msg.agents_info
            AgentsInfo.encode(performative.agents_info, agents_info)
            oef_search_msg.success.CopyFrom(performative)
        elif performative_id == OefSearchMessage.Performative.OEF_ERROR:
            performative = oef_search_pb2.OefSearchMessage.Oef_Error_Performative()  # type: ignore
            oef_error_operation = msg.oef_error_operation
            OefErrorOperation.encode(
                performative.oef_error_operation, oef_error_operation
            )
            oef_search_msg.oef_error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = oef_search_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'OefSearch' message.

        :param obj: the bytes object.
        :return: the 'OefSearch' message.
        """
        message_pb = ProtobufMessage()
        oef_search_pb = oef_search_pb2.OefSearchMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        oef_search_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = oef_search_pb.WhichOneof("performative")
        performative_id = OefSearchMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == OefSearchMessage.Performative.REGISTER_SERVICE:
            pb2_service_description = oef_search_pb.register_service.service_description
            service_description = Description.decode(pb2_service_description)
            performative_content["service_description"] = service_description
        elif performative_id == OefSearchMessage.Performative.UNREGISTER_SERVICE:
            pb2_service_description = (
                oef_search_pb.unregister_service.service_description
            )
            service_description = Description.decode(pb2_service_description)
            performative_content["service_description"] = service_description
        elif performative_id == OefSearchMessage.Performative.SEARCH_SERVICES:
            pb2_query = oef_search_pb.search_services.query
            query = Query.decode(pb2_query)
            performative_content["query"] = query
        elif performative_id == OefSearchMessage.Performative.SEARCH_RESULT:
            agents = oef_search_pb.search_result.agents
            agents_tuple = tuple(agents)
            performative_content["agents"] = agents_tuple
            pb2_agents_info = oef_search_pb.search_result.agents_info
            agents_info = AgentsInfo.decode(pb2_agents_info)
            performative_content["agents_info"] = agents_info
        elif performative_id == OefSearchMessage.Performative.SUCCESS:
            pb2_agents_info = oef_search_pb.success.agents_info
            agents_info = AgentsInfo.decode(pb2_agents_info)
            performative_content["agents_info"] = agents_info
        elif performative_id == OefSearchMessage.Performative.OEF_ERROR:
            pb2_oef_error_operation = oef_search_pb.oef_error.oef_error_operation
            oef_error_operation = OefErrorOperation.decode(pb2_oef_error_operation)
            performative_content["oef_error_operation"] = oef_error_operation
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return OefSearchMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
