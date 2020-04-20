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

"""This module contains class representations corresponding to every custom type in the protocol specification."""
from enum import Enum


class EventType(Enum):
    """
    One of "ARRIVAL", "DEPARTURE" or "DESTINATION"
    """

    ARRIVAL = 0
    DEPARTURE = 1
    DESTINATION = 2

    def __str__(self):
        """Get string representation."""
        return str(self.value)

    @classmethod
    def get(cls, string):
        return {
            "ARRIVAL": EventType.ARRIVAL,
            "DEPARTURE": EventType.DEPARTURE,
            "DESTINATION": EventType.DESTINATION,
        }[string]

    @staticmethod
    def encode(event_type_protobuf_object, event_type_object: "EventType") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the event_type_protobuf_object argument must be matched with the instance of this class in the 'event_type_object' argument.

        :param event_type_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param event_type_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        event_type_protobuf_object.event_type = event_type_object.value

    @classmethod
    def decode(cls, event_type_protobuf_object) -> "EventType":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'event_type_protobuf_object' argument.

        :param event_type_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'event_type_protobuf_object' argument.
        """
        enum_value_from_pb2 = event_type_protobuf_object.event_type
        return EventType(enum_value_from_pb2)


class VariationStatus(Enum):
    """
    One of "ON TIME", "EARLY", "LATE" or "OFF ROUTE"
    """

    ON_TIME = 0
    EARLY = 1
    LATE = 2
    OFF_ROUTE = 3

    def __str__(self):
        """Get string representation."""
        return str(self.value)

    @classmethod
    def get(cls, string):
        return {
            "ON TIME": VariationStatus.ON_TIME,
            "EARLY": VariationStatus.EARLY,
            "LATE": VariationStatus.LATE,
            "OFF ROUTE": VariationStatus.OFF_ROUTE,
        }[string]

    @staticmethod
    def encode(
        variation_status_protobuf_object, variation_status_object: "VariationStatus"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the variation_status_protobuf_object argument must be matched with the instance of this class in the 'variation_status_object' argument.

        :param variation_status_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param variation_status_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        variation_status_protobuf_object.variation_status = (
            variation_status_object.value
        )

    @classmethod
    def decode(cls, variation_status_protobuf_object) -> "VariationStatus":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'variation_status_protobuf_object' argument.

        :param variation_status_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'variation_status_protobuf_object' argument.
        """
        enum_value_from_pb2 = variation_status_protobuf_object.variation_status
        return VariationStatus(enum_value_from_pb2)
