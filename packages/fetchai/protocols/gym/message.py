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

"""This module contains gym's message definition."""

import logging
from enum import Enum
from typing import Dict, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from packages.fetchai.protocols.gym.custom_types import AnyObject as CustomAnyObject

logger = logging.getLogger("aea.packages.fetchai.protocols.gym.message")

DEFAULT_BODY_SIZE = 4


class GymMessage(Message):
    """A protocol for interacting with a gym connection."""

    protocol_id = ProtocolId("fetchai", "gym", "0.3.0")

    AnyObject = CustomAnyObject

    class Performative(Enum):
        """Performatives for the gym protocol."""

        ACT = "act"
        CLOSE = "close"
        PERCEPT = "percept"
        RESET = "reset"
        STATUS = "status"

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs,
    ):
        """
        Initialise an instance of GymMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=GymMessage.Performative(performative),
            **kwargs,
        )
        self._performatives = {"act", "close", "percept", "reset", "status"}

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
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return cast(GymMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def action(self) -> CustomAnyObject:
        """Get the 'action' content from the message."""
        assert self.is_set("action"), "'action' content is not set."
        return cast(CustomAnyObject, self.get("action"))

    @property
    def content(self) -> Dict[str, str]:
        """Get the 'content' content from the message."""
        assert self.is_set("content"), "'content' content is not set."
        return cast(Dict[str, str], self.get("content"))

    @property
    def done(self) -> bool:
        """Get the 'done' content from the message."""
        assert self.is_set("done"), "'done' content is not set."
        return cast(bool, self.get("done"))

    @property
    def info(self) -> CustomAnyObject:
        """Get the 'info' content from the message."""
        assert self.is_set("info"), "'info' content is not set."
        return cast(CustomAnyObject, self.get("info"))

    @property
    def observation(self) -> CustomAnyObject:
        """Get the 'observation' content from the message."""
        assert self.is_set("observation"), "'observation' content is not set."
        return cast(CustomAnyObject, self.get("observation"))

    @property
    def reward(self) -> float:
        """Get the 'reward' content from the message."""
        assert self.is_set("reward"), "'reward' content is not set."
        return cast(float, self.get("reward"))

    @property
    def step_id(self) -> int:
        """Get the 'step_id' content from the message."""
        assert self.is_set("step_id"), "'step_id' content is not set."
        return cast(int, self.get("step_id"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the gym protocol."""
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
                type(self.performative) == GymMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == GymMessage.Performative.ACT:
                expected_nb_of_contents = 2
                assert (
                    type(self.action) == CustomAnyObject
                ), "Invalid type for content 'action'. Expected 'AnyObject'. Found '{}'.".format(
                    type(self.action)
                )
                assert (
                    type(self.step_id) == int
                ), "Invalid type for content 'step_id'. Expected 'int'. Found '{}'.".format(
                    type(self.step_id)
                )
            elif self.performative == GymMessage.Performative.PERCEPT:
                expected_nb_of_contents = 5
                assert (
                    type(self.step_id) == int
                ), "Invalid type for content 'step_id'. Expected 'int'. Found '{}'.".format(
                    type(self.step_id)
                )
                assert (
                    type(self.observation) == CustomAnyObject
                ), "Invalid type for content 'observation'. Expected 'AnyObject'. Found '{}'.".format(
                    type(self.observation)
                )
                assert (
                    type(self.reward) == float
                ), "Invalid type for content 'reward'. Expected 'float'. Found '{}'.".format(
                    type(self.reward)
                )
                assert (
                    type(self.done) == bool
                ), "Invalid type for content 'done'. Expected 'bool'. Found '{}'.".format(
                    type(self.done)
                )
                assert (
                    type(self.info) == CustomAnyObject
                ), "Invalid type for content 'info'. Expected 'AnyObject'. Found '{}'.".format(
                    type(self.info)
                )
            elif self.performative == GymMessage.Performative.STATUS:
                expected_nb_of_contents = 1
                assert (
                    type(self.content) == dict
                ), "Invalid type for content 'content'. Expected 'dict'. Found '{}'.".format(
                    type(self.content)
                )
                for key_of_content, value_of_content in self.content.items():
                    assert (
                        type(key_of_content) == str
                    ), "Invalid type for dictionary keys in content 'content'. Expected 'str'. Found '{}'.".format(
                        type(key_of_content)
                    )
                    assert (
                        type(value_of_content) == str
                    ), "Invalid type for dictionary values in content 'content'. Expected 'str'. Found '{}'.".format(
                        type(value_of_content)
                    )
            elif self.performative == GymMessage.Performative.RESET:
                expected_nb_of_contents = 0
            elif self.performative == GymMessage.Performative.CLOSE:
                expected_nb_of_contents = 0

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
