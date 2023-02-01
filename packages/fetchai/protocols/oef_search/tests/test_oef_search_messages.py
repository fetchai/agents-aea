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

"""Test messages module for oef_search protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.helpers.search.models import Constraint, ConstraintType
from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.fetchai.protocols.oef_search.custom_types import (
    AgentsInfo,
    Description,
    Query,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage


class TestMessageOefSearch(BaseProtocolMessagesTestCase):
    """Test for the 'oef_search' protocol message."""

    MESSAGE_CLASS = OefSearchMessage

    def build_messages(self) -> List[OefSearchMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            OefSearchMessage(
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=Description(
                    {"foo1": 1, "bar1": 2}
                ),  # check it please!
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                service_description=Description(
                    {"foo1": 1, "bar1": 2}
                ),  # check it please!
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=Query(
                    [Constraint("something", ConstraintType(">", 1))]
                ),  # check it please!
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                agents=("some str",),
                agents_info=AgentsInfo(
                    {
                        "key_1": {"key_1": b"value_1", "key_2": b"value_2"},
                        "key_2": {"key_3": b"value_3", "key_4": b"value_4"},
                    }
                ),
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.SUCCESS,
                agents_info=AgentsInfo(
                    {
                        "key_1": {"key_1": b"value_1", "key_2": b"value_2"},
                        "key_2": {"key_3": b"value_3", "key_4": b"value_4"},
                    }
                ),
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.OEF_ERROR,
                oef_error_operation=OefSearchMessage.OefErrorOperation.OTHER,  # check it please!
            ),
        ]

    def build_inconsistent(self) -> List[OefSearchMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            OefSearchMessage(
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                # skip content: service_description
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                # skip content: service_description
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                # skip content: query
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                # skip content: agents
                agents_info=AgentsInfo(
                    {
                        "key_1": {"key_1": b"value_1", "key_2": b"value_2"},
                        "key_2": {"key_3": b"value_3", "key_4": b"value_4"},
                    }
                ),  # check it please!
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.SUCCESS,
                # skip content: agents_info
            ),
            OefSearchMessage(
                performative=OefSearchMessage.Performative.OEF_ERROR,
                # skip content: oef_error_operation
            ),
        ]
