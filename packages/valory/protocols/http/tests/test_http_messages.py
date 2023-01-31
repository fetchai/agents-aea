# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 valory
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

"""Test messages module for http protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.valory.protocols.http.message import HttpMessage


class TestMessageHttp(BaseProtocolMessagesTestCase):
    """Test for the 'http' protocol message."""

    MESSAGE_CLASS = HttpMessage

    def build_messages(self) -> List[HttpMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            HttpMessage(
                performative=HttpMessage.Performative.REQUEST,
                method="some str",
                url="some str",
                version="some str",
                headers="some str",
                body=b"some_bytes",
            ),
            HttpMessage(
                performative=HttpMessage.Performative.RESPONSE,
                version="some str",
                status_code=12,
                status_text="some str",
                headers="some str",
                body=b"some_bytes",
            ),
        ]

    def build_inconsistent(self) -> List[HttpMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            HttpMessage(
                performative=HttpMessage.Performative.REQUEST,
                # skip content: method
                url="some str",
                version="some str",
                headers="some str",
                body=b"some_bytes",
            ),
            HttpMessage(
                performative=HttpMessage.Performative.RESPONSE,
                # skip content: version
                status_code=12,
                status_text="some str",
                headers="some str",
                body=b"some_bytes",
            ),
        ]
