# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 fetchai
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

"""Test messages module for gym protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.fetchai.protocols.gym.custom_types import AnyObject
from packages.fetchai.protocols.gym.message import GymMessage


class TestMessageGym(BaseProtocolMessagesTestCase):
    """Test for the 'gym' protocol message."""

    MESSAGE_CLASS = GymMessage

    def build_messages(self) -> List[GymMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            GymMessage(
                performative=GymMessage.Performative.ACT,
                action=AnyObject("some_info"),
                step_id=12,
            ),
            GymMessage(
                performative=GymMessage.Performative.PERCEPT,
                step_id=12,
                observation=AnyObject("some_info1"),
                reward=1.0,
                done=True,
                info=AnyObject("some_info"),
            ),
            GymMessage(
                performative=GymMessage.Performative.STATUS,
                content={"some str": "some str"},
            ),
            GymMessage(
                performative=GymMessage.Performative.RESET,
            ),
            GymMessage(
                performative=GymMessage.Performative.CLOSE,
            ),
        ]

    def build_inconsistent(self) -> List[GymMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            GymMessage(
                performative=GymMessage.Performative.ACT,
                # skip content: action
                step_id=12,
            ),
            GymMessage(
                performative=GymMessage.Performative.PERCEPT,
                # skip content: step_id
                observation=AnyObject("some_info"),
                reward=1.4,
                done=True,
                info=AnyObject("some_info"),
            ),
            GymMessage(
                performative=GymMessage.Performative.STATUS,
                # skip content: content
            ),
        ]
