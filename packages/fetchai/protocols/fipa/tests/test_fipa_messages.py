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

"""Test messages module for fipa protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.helpers.search.models import Constraint, ConstraintType
from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.fetchai.protocols.fipa.custom_types import Description, Query
from packages.fetchai.protocols.fipa.message import FipaMessage


class TestMessageFipa(BaseProtocolMessagesTestCase):
    """Test for the 'fipa' protocol message."""

    MESSAGE_CLASS = FipaMessage

    def build_messages(self) -> List[FipaMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            FipaMessage(
                performative=FipaMessage.Performative.CFP,
                query=Query([Constraint("something", ConstraintType(">", 1))]),
            ),
            FipaMessage(
                performative=FipaMessage.Performative.PROPOSE,
                proposal=Description({"foo1": 1, "bar1": 2}),
            ),
            FipaMessage(
                performative=FipaMessage.Performative.ACCEPT_W_INFORM,
                info={"some str": "some str"},
            ),
            FipaMessage(
                performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                info={"some str": "some str"},
            ),
            FipaMessage(
                performative=FipaMessage.Performative.INFORM,
                info={"some str": "some str"},
            ),
            FipaMessage(
                performative=FipaMessage.Performative.ACCEPT,
            ),
            FipaMessage(
                performative=FipaMessage.Performative.DECLINE,
            ),
            FipaMessage(
                performative=FipaMessage.Performative.MATCH_ACCEPT,
            ),
            FipaMessage(
                performative=FipaMessage.Performative.END,
            ),
        ]

    def build_inconsistent(self) -> List[FipaMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            FipaMessage(
                performative=FipaMessage.Performative.CFP,
                # skip content: query
            ),
            FipaMessage(
                performative=FipaMessage.Performative.PROPOSE,
                # skip content: proposal
            ),
            FipaMessage(
                performative=FipaMessage.Performative.ACCEPT_W_INFORM,
                # skip content: info
            ),
            FipaMessage(
                performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                # skip content: info
            ),
            FipaMessage(
                performative=FipaMessage.Performative.INFORM,
                # skip content: info
            ),
        ]
