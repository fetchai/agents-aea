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

"""Test messages module for default protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.fetchai.protocols.default.custom_types import ErrorCode
from packages.fetchai.protocols.default.message import DefaultMessage


class TestMessageDefault(BaseProtocolMessagesTestCase):
    """Test for the 'default' protocol message."""

    MESSAGE_CLASS = DefaultMessage

    def build_messages(self) -> List[DefaultMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            DefaultMessage(
                performative=DefaultMessage.Performative.BYTES,
                content=b"some_bytes",
            ),
            DefaultMessage(
                performative=DefaultMessage.Performative.ERROR,
                error_code=ErrorCode.DECODING_ERROR,  # check it please!
                error_msg="some str",
                error_data={"some str": b"some_bytes"},
            ),
            DefaultMessage(
                performative=DefaultMessage.Performative.END,
            ),
        ]

    def build_inconsistent(self) -> List[DefaultMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            DefaultMessage(
                performative=DefaultMessage.Performative.BYTES,
                # skip content: content
            ),
            DefaultMessage(
                performative=DefaultMessage.Performative.ERROR,
                # skip content: error_code
                error_msg="some str",
                error_data={"some str": b"some_bytes"},
            ),
        ]
