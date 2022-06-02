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

"""This module contains gym's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Dict, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.fetchai.protocols.gym.custom_types import AnyObject as CustomAnyObject


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.gym.message")

DEFAULT_BODY_SIZE = 4


class GymMessage(Message):
    """A protocol for interacting with a gym connection."""

    protocol_id = PublicId.from_str("fetchai/gym:1.0.0")
    protocol_specification_id = PublicId.from_str("fetchai/gym:1.0.0")

    AnyObject = CustomAnyObject

    class Performative(Message.Performative):
        """Performatives for the gym protocol."""

        ACT = "act"
        CLOSE = "close"
        PERCEPT = "percept"
        RESET = "reset"
        STATUS = "status"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {"act", "close", "percept", "reset", "status"}
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "action",
            "content",
            "dialogue_reference",
            "done",
            "info",
            "message_id",
            "observation",
            "performative",
            "reward",
            "step_id",
            "target",
        )

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs: Any,
    ):
        """
        Initialise an instance of GymMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        :param **kwargs: extra options.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=GymMessage.Performative(performative),
            **kwargs,
        )

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        enforce(self.is_set("dialogue_reference"), "dialogue_reference is not set.")
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        enforce(self.is_set("message_id"), "message_id is not set.")
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        enforce(self.is_set("performative"), "performative is not set.")
        return cast(GymMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def action(self) -> CustomAnyObject:
        """Get the 'action' content from the message."""
        enforce(self.is_set("action"), "'action' content is not set.")
        return cast(CustomAnyObject, self.get("action"))

    @property
    def content(self) -> Dict[str, str]:
        """Get the 'content' content from the message."""
        enforce(self.is_set("content"), "'content' content is not set.")
        return cast(Dict[str, str], self.get("content"))

    @property
    def done(self) -> bool:
        """Get the 'done' content from the message."""
        enforce(self.is_set("done"), "'done' content is not set.")
        return cast(bool, self.get("done"))

    @property
    def info(self) -> CustomAnyObject:
        """Get the 'info' content from the message."""
        enforce(self.is_set("info"), "'info' content is not set.")
        return cast(CustomAnyObject, self.get("info"))

    @property
    def observation(self) -> CustomAnyObject:
        """Get the 'observation' content from the message."""
        enforce(self.is_set("observation"), "'observation' content is not set.")
        return cast(CustomAnyObject, self.get("observation"))

    @property
    def reward(self) -> float:
        """Get the 'reward' content from the message."""
        enforce(self.is_set("reward"), "'reward' content is not set.")
        return cast(float, self.get("reward"))

    @property
    def step_id(self) -> int:
        """Get the 'step_id' content from the message."""
        enforce(self.is_set("step_id"), "'step_id' content is not set.")
        return cast(int, self.get("step_id"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the gym protocol."""
        try:
            enforce(
                isinstance(self.dialogue_reference, tuple),
                "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                    type(self.dialogue_reference)
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[0], str),
                "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[0])
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[1], str),
                "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[1])
                ),
            )
            enforce(
                type(self.message_id) is int,
                "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                    type(self.message_id)
                ),
            )
            enforce(
                type(self.target) is int,
                "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                    type(self.target)
                ),
            )

            # Light Protocol Rule 2
            # Check correct performative
            enforce(
                isinstance(self.performative, GymMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == GymMessage.Performative.ACT:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.action, CustomAnyObject),
                    "Invalid type for content 'action'. Expected 'AnyObject'. Found '{}'.".format(
                        type(self.action)
                    ),
                )
                enforce(
                    type(self.step_id) is int,
                    "Invalid type for content 'step_id'. Expected 'int'. Found '{}'.".format(
                        type(self.step_id)
                    ),
                )
            elif self.performative == GymMessage.Performative.PERCEPT:
                expected_nb_of_contents = 5
                enforce(
                    type(self.step_id) is int,
                    "Invalid type for content 'step_id'. Expected 'int'. Found '{}'.".format(
                        type(self.step_id)
                    ),
                )
                enforce(
                    isinstance(self.observation, CustomAnyObject),
                    "Invalid type for content 'observation'. Expected 'AnyObject'. Found '{}'.".format(
                        type(self.observation)
                    ),
                )
                enforce(
                    isinstance(self.reward, float),
                    "Invalid type for content 'reward'. Expected 'float'. Found '{}'.".format(
                        type(self.reward)
                    ),
                )
                enforce(
                    isinstance(self.done, bool),
                    "Invalid type for content 'done'. Expected 'bool'. Found '{}'.".format(
                        type(self.done)
                    ),
                )
                enforce(
                    isinstance(self.info, CustomAnyObject),
                    "Invalid type for content 'info'. Expected 'AnyObject'. Found '{}'.".format(
                        type(self.info)
                    ),
                )
            elif self.performative == GymMessage.Performative.STATUS:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.content, dict),
                    "Invalid type for content 'content'. Expected 'dict'. Found '{}'.".format(
                        type(self.content)
                    ),
                )
                for key_of_content, value_of_content in self.content.items():
                    enforce(
                        isinstance(key_of_content, str),
                        "Invalid type for dictionary keys in content 'content'. Expected 'str'. Found '{}'.".format(
                            type(key_of_content)
                        ),
                    )
                    enforce(
                        isinstance(value_of_content, str),
                        "Invalid type for dictionary values in content 'content'. Expected 'str'. Found '{}'.".format(
                            type(value_of_content)
                        ),
                    )
            elif self.performative == GymMessage.Performative.RESET:
                expected_nb_of_contents = 0
            elif self.performative == GymMessage.Performative.CLOSE:
                expected_nb_of_contents = 0

            # Check correct content count
            enforce(
                expected_nb_of_contents == actual_nb_of_contents,
                "Incorrect number of contents. Expected {}. Found {}".format(
                    expected_nb_of_contents, actual_nb_of_contents
                ),
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                enforce(
                    self.target == 0,
                    "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                        self.target
                    ),
                )
        except (AEAEnforceError, ValueError, KeyError) as e:
            _default_logger.error(str(e))
            return False

        return True
