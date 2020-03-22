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

"""Serialization module for oef protocol."""

from typing import cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.fetchai.protocols.oef import oef_pb2
from packages.fetchai.protocols.oef.custom_types import Description
from packages.fetchai.protocols.oef.custom_types import OEFErrorOperation
from packages.fetchai.protocols.oef.custom_types import Query
from packages.fetchai.protocols.oef.message import OefMessage


class OefSerializer(Serializer):
    """Serialization for the 'oef' protocol."""

    def encode(self, msg: Message) -> bytes:
        """
        Encode a 'Oef' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(OefMessage, msg)
        oef_msg = oef_pb2.OefMessage()
        oef_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        oef_msg.dialogue_starter_reference = dialogue_reference[0]
        oef_msg.dialogue_responder_reference = dialogue_reference[1]
        oef_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == OefMessage.Performative.REGISTER_SERVICE:
            performative = oef_pb2.OefMessage.Register_Service()  # type: ignore
            service_description = msg.service_description
            performative = Description.encode(performative, service_description)
            service_id = msg.service_id
            performative.service_id = service_id
            oef_msg.register_service.CopyFrom(performative)
        elif performative_id == OefMessage.Performative.UNREGISTER_SERVICE:
            performative = oef_pb2.OefMessage.Unregister_Service()  # type: ignore
            service_description = msg.service_description
            performative = Description.encode(performative, service_description)
            oef_msg.unregister_service.CopyFrom(performative)
        elif performative_id == OefMessage.Performative.SEARCH_SERVICES:
            performative = oef_pb2.OefMessage.Search_Services()  # type: ignore
            query = msg.query
            performative = Query.encode(performative, query)
            oef_msg.search_services.CopyFrom(performative)
        elif performative_id == OefMessage.Performative.SEARCH_RESULT:
            performative = oef_pb2.OefMessage.Search_Result()  # type: ignore
            agents = msg.agents
            performative.agents.extend(agents)
            oef_msg.search_result.CopyFrom(performative)
        elif performative_id == OefMessage.Performative.OEF_ERROR:
            performative = oef_pb2.OefMessage.Oef_Error()  # type: ignore
            operation = msg.operation
            performative = OEFErrorOperation.encode(performative, operation)
            oef_msg.oef_error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        oef_bytes = oef_msg.SerializeToString()
        return oef_bytes

    def decode(self, obj: bytes) -> Message:
        """
        Decode bytes into a 'Oef' message.

        :param obj: the bytes object.
        :return: the 'Oef' message.
        """
        oef_pb = oef_pb2.OefMessage()
        oef_pb.ParseFromString(obj)
        message_id = oef_pb.message_id
        dialogue_reference = (
            oef_pb.dialogue_starter_reference,
            oef_pb.dialogue_responder_reference,
        )
        target = oef_pb.target

        performative = oef_pb.WhichOneof("performative")
        performative_id = OefMessage.Performative(str(performative))
        performative_content = dict()
        if performative_id == OefMessage.Performative.REGISTER_SERVICE:
            pb2_service_description = oef_pb.register_service.service_description
            service_description = Description.decode(pb2_service_description)
            performative_content["service_description"] = service_description
            service_id = oef_pb.register_service.service_id
            performative_content["service_id"] = service_id
        elif performative_id == OefMessage.Performative.UNREGISTER_SERVICE:
            pb2_service_description = oef_pb.unregister_service.service_description
            service_description = Description.decode(pb2_service_description)
            performative_content["service_description"] = service_description
        elif performative_id == OefMessage.Performative.SEARCH_SERVICES:
            pb2_query = oef_pb.search_services.query
            query = Query.decode(pb2_query)
            performative_content["query"] = query
        elif performative_id == OefMessage.Performative.SEARCH_RESULT:
            agents = oef_pb.search_result.agents
            agents_tuple = tuple(agents)
            performative_content["agents"] = agents_tuple
        elif performative_id == OefMessage.Performative.OEF_ERROR:
            pb2_operation = oef_pb.oef_error.operation
            operation = OEFErrorOperation.decode(pb2_operation)
            performative_content["operation"] = operation
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return OefMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
