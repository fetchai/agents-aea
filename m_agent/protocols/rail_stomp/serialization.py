# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 aris
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

"""Serialization module for rail_stomp protocol."""

from typing import Any, Dict, cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from packages.aris.protocols.rail_stomp import rail_stomp_pb2
from packages.aris.protocols.rail_stomp.custom_types import EventType
from packages.aris.protocols.rail_stomp.custom_types import VariationStatus
from packages.aris.protocols.rail_stomp.message import RailStompMessage


class RailStompSerializer(Serializer):
    """Serialization for the 'rail_stomp' protocol."""

    def encode(self, msg: Message) -> bytes:
        """
        Encode a 'RailStomp' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(RailStompMessage, msg)
        rail_stomp_msg = rail_stomp_pb2.RailStompMessage()
        rail_stomp_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        rail_stomp_msg.dialogue_starter_reference = dialogue_reference[0]
        rail_stomp_msg.dialogue_responder_reference = dialogue_reference[1]
        rail_stomp_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == RailStompMessage.Performative.RAIL_UPDATES:
            performative = rail_stomp_pb2.RailStompMessage.Rail_Updates_Performative()  # type: ignore
            event_type = msg.event_type
            EventType.encode(performative.event_type, event_type)
            variation_status = msg.variation_status
            VariationStatus.encode(performative.variation_status, variation_status)
            planned_event_type = msg.planned_event_type
            performative.planned_event_type = planned_event_type
            status = msg.status
            performative.status = status
            planned_datetime = msg.planned_datetime
            performative.planned_datetime = planned_datetime
            actual_datetime = msg.actual_datetime
            performative.actual_datetime = actual_datetime
            planned_timetable_datetime = msg.planned_timetable_datetime
            performative.planned_timetable_datetime = planned_timetable_datetime
            location = msg.location
            performative.location = location
            location_stanox = msg.location_stanox
            performative.location_stanox = location_stanox
            is_correction = msg.is_correction
            performative.is_correction = is_correction
            train_terminated = msg.train_terminated
            performative.train_terminated = train_terminated
            operating_company = msg.operating_company
            performative.operating_company = operating_company
            division_code = msg.division_code
            performative.division_code = division_code
            train_service_code = msg.train_service_code
            performative.train_service_code = train_service_code
            train_id = msg.train_id
            performative.train_id = train_id
            is_off_route = msg.is_off_route
            performative.is_off_route = is_off_route
            current_train_id = msg.current_train_id
            performative.current_train_id = current_train_id
            original_location = msg.original_location
            performative.original_location = original_location
            original_location_planned_departure_datetime = (
                msg.original_location_planned_departure_datetime
            )
            performative.original_location_planned_departure_datetime = (
                original_location_planned_departure_datetime
            )
            minutes_late = msg.minutes_late
            performative.minutes_late = minutes_late
            early_late_description = msg.early_late_description
            performative.early_late_description = early_late_description
            rail_stomp_msg.rail_updates.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        rail_stomp_bytes = rail_stomp_msg.SerializeToString()
        return rail_stomp_bytes

    def decode(self, obj: bytes) -> Message:
        """
        Decode bytes into a 'RailStomp' message.

        :param obj: the bytes object.
        :return: the 'RailStomp' message.
        """
        rail_stomp_pb = rail_stomp_pb2.RailStompMessage()
        rail_stomp_pb.ParseFromString(obj)
        message_id = rail_stomp_pb.message_id
        dialogue_reference = (
            rail_stomp_pb.dialogue_starter_reference,
            rail_stomp_pb.dialogue_responder_reference,
        )
        target = rail_stomp_pb.target

        performative = rail_stomp_pb.WhichOneof("performative")
        performative_id = RailStompMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == RailStompMessage.Performative.RAIL_UPDATES:
            pb2_event_type = rail_stomp_pb.rail_updates.event_type
            event_type = EventType.decode(pb2_event_type)
            performative_content["event_type"] = event_type
            pb2_variation_status = rail_stomp_pb.rail_updates.variation_status
            variation_status = VariationStatus.decode(pb2_variation_status)
            performative_content["variation_status"] = variation_status
            planned_event_type = rail_stomp_pb.rail_updates.planned_event_type
            performative_content["planned_event_type"] = planned_event_type
            status = rail_stomp_pb.rail_updates.status
            performative_content["status"] = status
            planned_datetime = rail_stomp_pb.rail_updates.planned_datetime
            performative_content["planned_datetime"] = planned_datetime
            actual_datetime = rail_stomp_pb.rail_updates.actual_datetime
            performative_content["actual_datetime"] = actual_datetime
            planned_timetable_datetime = (
                rail_stomp_pb.rail_updates.planned_timetable_datetime
            )
            performative_content[
                "planned_timetable_datetime"
            ] = planned_timetable_datetime
            location = rail_stomp_pb.rail_updates.location
            performative_content["location"] = location
            location_stanox = rail_stomp_pb.rail_updates.location_stanox
            performative_content["location_stanox"] = location_stanox
            is_correction = rail_stomp_pb.rail_updates.is_correction
            performative_content["is_correction"] = is_correction
            train_terminated = rail_stomp_pb.rail_updates.train_terminated
            performative_content["train_terminated"] = train_terminated
            operating_company = rail_stomp_pb.rail_updates.operating_company
            performative_content["operating_company"] = operating_company
            division_code = rail_stomp_pb.rail_updates.division_code
            performative_content["division_code"] = division_code
            train_service_code = rail_stomp_pb.rail_updates.train_service_code
            performative_content["train_service_code"] = train_service_code
            train_id = rail_stomp_pb.rail_updates.train_id
            performative_content["train_id"] = train_id
            is_off_route = rail_stomp_pb.rail_updates.is_off_route
            performative_content["is_off_route"] = is_off_route
            current_train_id = rail_stomp_pb.rail_updates.current_train_id
            performative_content["current_train_id"] = current_train_id
            original_location = rail_stomp_pb.rail_updates.original_location
            performative_content["original_location"] = original_location
            original_location_planned_departure_datetime = (
                rail_stomp_pb.rail_updates.original_location_planned_departure_datetime
            )
            performative_content[
                "original_location_planned_departure_datetime"
            ] = original_location_planned_departure_datetime
            minutes_late = rail_stomp_pb.rail_updates.minutes_late
            performative_content["minutes_late"] = minutes_late
            early_late_description = rail_stomp_pb.rail_updates.early_late_description
            performative_content["early_late_description"] = early_late_description
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return RailStompMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
