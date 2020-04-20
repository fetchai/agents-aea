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

"""This module contains rail_stomp's message definition."""

import logging
from enum import Enum
from typing import Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from packages.aris.protocols.rail_stomp.custom_types import EventType as CustomEventType
from packages.aris.protocols.rail_stomp.custom_types import (
    VariationStatus as CustomVariationStatus,
)

logger = logging.getLogger("aea.packages.aris.protocols.rail_stomp.message")

DEFAULT_BODY_SIZE = 4


class RailStompMessage(Message):
    """A protocol for Train updates using stomp connections."""

    protocol_id = ProtocolId("aris", "rail_stomp", "0.1.0")

    EventType = CustomEventType

    VariationStatus = CustomVariationStatus

    class Performative(Enum):
        """Performatives for the rail_stomp protocol."""

        RAIL_UPDATES = "rail_updates"

        def __str__(self):
            """Get the string representation."""
            return self.value

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs,
    ):
        """
        Initialise an instance of RailStompMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=RailStompMessage.Performative(performative),
            **kwargs,
        )
        self._performatives = {"rail_updates"}

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        assert self.is_set("dialogue_reference"), "dialogue_reference is not set."
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        assert self.is_set("message_id"), "message_id is not set."
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return cast(RailStompMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def actual_datetime(self) -> str:
        """Get the 'actual_datetime' content from the message."""
        assert self.is_set("actual_datetime"), "'actual_datetime' content is not set."
        return cast(str, self.get("actual_datetime"))

    @property
    def current_train_id(self) -> str:
        """Get the 'current_train_id' content from the message."""
        assert self.is_set("current_train_id"), "'current_train_id' content is not set."
        return cast(str, self.get("current_train_id"))

    @property
    def division_code(self) -> str:
        """Get the 'division_code' content from the message."""
        assert self.is_set("division_code"), "'division_code' content is not set."
        return cast(str, self.get("division_code"))

    @property
    def early_late_description(self) -> str:
        """Get the 'early_late_description' content from the message."""
        assert self.is_set(
            "early_late_description"
        ), "'early_late_description' content is not set."
        return cast(str, self.get("early_late_description"))

    @property
    def event_type(self) -> CustomEventType:
        """Get the 'event_type' content from the message."""
        assert self.is_set("event_type"), "'event_type' content is not set."
        return cast(CustomEventType, self.get("event_type"))

    @property
    def is_correction(self) -> bool:
        """Get the 'is_correction' content from the message."""
        assert self.is_set("is_correction"), "'is_correction' content is not set."
        return cast(bool, self.get("is_correction"))

    @property
    def is_off_route(self) -> bool:
        """Get the 'is_off_route' content from the message."""
        assert self.is_set("is_off_route"), "'is_off_route' content is not set."
        return cast(bool, self.get("is_off_route"))

    @property
    def location(self) -> str:
        """Get the 'location' content from the message."""
        assert self.is_set("location"), "'location' content is not set."
        return cast(str, self.get("location"))

    @property
    def location_stanox(self) -> int:
        """Get the 'location_stanox' content from the message."""
        assert self.is_set("location_stanox"), "'location_stanox' content is not set."
        return cast(int, self.get("location_stanox"))

    @property
    def minutes_late(self) -> int:
        """Get the 'minutes_late' content from the message."""
        assert self.is_set("minutes_late"), "'minutes_late' content is not set."
        return cast(int, self.get("minutes_late"))

    @property
    def operating_company(self) -> str:
        """Get the 'operating_company' content from the message."""
        assert self.is_set(
            "operating_company"
        ), "'operating_company' content is not set."
        return cast(str, self.get("operating_company"))

    @property
    def original_location(self) -> str:
        """Get the 'original_location' content from the message."""
        assert self.is_set(
            "original_location"
        ), "'original_location' content is not set."
        return cast(str, self.get("original_location"))

    @property
    def original_location_planned_departure_datetime(self) -> str:
        """Get the 'original_location_planned_departure_datetime' content from the message."""
        assert self.is_set(
            "original_location_planned_departure_datetime"
        ), "'original_location_planned_departure_datetime' content is not set."
        return cast(str, self.get("original_location_planned_departure_datetime"))

    @property
    def planned_datetime(self) -> str:
        """Get the 'planned_datetime' content from the message."""
        assert self.is_set("planned_datetime"), "'planned_datetime' content is not set."
        return cast(str, self.get("planned_datetime"))

    @property
    def planned_event_type(self) -> str:
        """Get the 'planned_event_type' content from the message."""
        assert self.is_set(
            "planned_event_type"
        ), "'planned_event_type' content is not set."
        return cast(str, self.get("planned_event_type"))

    @property
    def planned_timetable_datetime(self) -> str:
        """Get the 'planned_timetable_datetime' content from the message."""
        assert self.is_set(
            "planned_timetable_datetime"
        ), "'planned_timetable_datetime' content is not set."
        return cast(str, self.get("planned_timetable_datetime"))

    @property
    def status(self) -> str:
        """Get the 'status' content from the message."""
        assert self.is_set("status"), "'status' content is not set."
        return cast(str, self.get("status"))

    @property
    def train_id(self) -> str:
        """Get the 'train_id' content from the message."""
        assert self.is_set("train_id"), "'train_id' content is not set."
        return cast(str, self.get("train_id"))

    @property
    def train_service_code(self) -> str:
        """Get the 'train_service_code' content from the message."""
        assert self.is_set(
            "train_service_code"
        ), "'train_service_code' content is not set."
        return cast(str, self.get("train_service_code"))

    @property
    def train_terminated(self) -> bool:
        """Get the 'train_terminated' content from the message."""
        assert self.is_set("train_terminated"), "'train_terminated' content is not set."
        return cast(bool, self.get("train_terminated"))

    @property
    def variation_status(self) -> CustomVariationStatus:
        """Get the 'variation_status' content from the message."""
        assert self.is_set("variation_status"), "'variation_status' content is not set."
        return cast(CustomVariationStatus, self.get("variation_status"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the rail_stomp protocol."""
        try:
            assert (
                type(self.dialogue_reference) == tuple
            ), "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                type(self.dialogue_reference)
            )
            assert (
                type(self.dialogue_reference[0]) == str
            ), "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                type(self.dialogue_reference[0])
            )
            assert (
                type(self.dialogue_reference[1]) == str
            ), "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                type(self.dialogue_reference[1])
            )
            assert (
                type(self.message_id) == int
            ), "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                type(self.message_id)
            )
            assert (
                type(self.target) == int
            ), "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                type(self.target)
            )

            # Light Protocol Rule 2
            # Check correct performative
            assert (
                type(self.performative) == RailStompMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == RailStompMessage.Performative.RAIL_UPDATES:
                expected_nb_of_contents = 21
                assert (
                    type(self.event_type) == CustomEventType
                ), "Invalid type for content 'event_type'. Expected 'EventType'. Found '{}'.".format(
                    type(self.event_type)
                )
                assert (
                    type(self.variation_status) == CustomVariationStatus
                ), "Invalid type for content 'variation_status'. Expected 'VariationStatus'. Found '{}'.".format(
                    type(self.variation_status)
                )
                assert (
                    type(self.planned_event_type) == str
                ), "Invalid type for content 'planned_event_type'. Expected 'str'. Found '{}'.".format(
                    type(self.planned_event_type)
                )
                assert (
                    type(self.status) == str
                ), "Invalid type for content 'status'. Expected 'str'. Found '{}'.".format(
                    type(self.status)
                )
                assert (
                    type(self.planned_datetime) == str
                ), "Invalid type for content 'planned_datetime'. Expected 'str'. Found '{}'.".format(
                    type(self.planned_datetime)
                )
                assert (
                    type(self.actual_datetime) == str
                ), "Invalid type for content 'actual_datetime'. Expected 'str'. Found '{}'.".format(
                    type(self.actual_datetime)
                )
                assert (
                    type(self.planned_timetable_datetime) == str
                ), "Invalid type for content 'planned_timetable_datetime'. Expected 'str'. Found '{}'.".format(
                    type(self.planned_timetable_datetime)
                )
                assert (
                    type(self.location) == str
                ), "Invalid type for content 'location'. Expected 'str'. Found '{}'.".format(
                    type(self.location)
                )
                assert (
                    type(self.location_stanox) == int
                ), "Invalid type for content 'location_stanox'. Expected 'int'. Found '{}'.".format(
                    type(self.location_stanox)
                )
                assert (
                    type(self.is_correction) == bool
                ), "Invalid type for content 'is_correction'. Expected 'bool'. Found '{}'.".format(
                    type(self.is_correction)
                )
                assert (
                    type(self.train_terminated) == bool
                ), "Invalid type for content 'train_terminated'. Expected 'bool'. Found '{}'.".format(
                    type(self.train_terminated)
                )
                assert (
                    type(self.operating_company) == str
                ), "Invalid type for content 'operating_company'. Expected 'str'. Found '{}'.".format(
                    type(self.operating_company)
                )
                assert (
                    type(self.division_code) == str
                ), "Invalid type for content 'division_code'. Expected 'str'. Found '{}'.".format(
                    type(self.division_code)
                )
                assert (
                    type(self.train_service_code) == str
                ), "Invalid type for content 'train_service_code'. Expected 'str'. Found '{}'.".format(
                    type(self.train_service_code)
                )
                assert (
                    type(self.train_id) == str
                ), "Invalid type for content 'train_id'. Expected 'str'. Found '{}'.".format(
                    type(self.train_id)
                )
                assert (
                    type(self.is_off_route) == bool
                ), "Invalid type for content 'is_off_route'. Expected 'bool'. Found '{}'.".format(
                    type(self.is_off_route)
                )
                assert (
                    type(self.current_train_id) == str
                ), "Invalid type for content 'current_train_id'. Expected 'str'. Found '{}'.".format(
                    type(self.current_train_id)
                )
                assert (
                    type(self.original_location) == str
                ), "Invalid type for content 'original_location'. Expected 'str'. Found '{}'.".format(
                    type(self.original_location)
                )
                assert (
                    type(self.original_location_planned_departure_datetime) == str
                ), "Invalid type for content 'original_location_planned_departure_datetime'. Expected 'str'. Found '{}'.".format(
                    type(self.original_location_planned_departure_datetime)
                )
                assert (
                    type(self.minutes_late) == int
                ), "Invalid type for content 'minutes_late'. Expected 'int'. Found '{}'.".format(
                    type(self.minutes_late)
                )
                assert (
                    type(self.early_late_description) == str
                ), "Invalid type for content 'early_late_description'. Expected 'str'. Found '{}'.".format(
                    type(self.early_late_description)
                )

            # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {}. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                assert (
                    self.target == 0
                ), "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                    self.target
                )
            else:
                assert (
                    0 < self.target < self.message_id
                ), "Invalid 'target'. Expected an integer between 1 and {} inclusive. Found {}.".format(
                    self.message_id - 1, self.target,
                )
        except (AssertionError, ValueError, KeyError) as e:
            logger.error(str(e))
            return False

        return True
