# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 open_aea
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

"""Test messages module for signing protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.open_aea.protocols.signing.custom_types import (
    ErrorCode,
    RawMessage,
    RawTransaction,
    SignedMessage,
    SignedTransaction,
    Terms,
)
from packages.open_aea.protocols.signing.message import SigningMessage


class TestMessageSigning(BaseProtocolMessagesTestCase):
    """Test for the 'signing' protocol message."""

    __test__ = True
    MESSAGE_CLASS = SigningMessage

    def build_messages(self) -> List[SigningMessage]:
        """Build the messages to be used for testing."""
        return [
            SigningMessage(
                performative=SigningMessage.Performative.SIGN_TRANSACTION,
                terms=Terms(),  # check it please!
                raw_transaction=RawTransaction(),  # check it please!
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGN_MESSAGE,
                terms=Terms(),  # check it please!
                raw_message=RawMessage(),  # check it please!
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=SignedTransaction(),  # check it please!
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SignedMessage(),  # check it please!
            ),
            SigningMessage(
                performative=SigningMessage.Performative.ERROR,
                error_code=ErrorCode(),  # check it please!
            ),
        ]

    def build_inconsistent(self) -> List[SigningMessage]:
        """Build inconsistent messages to be used for testing."""
        return [
            SigningMessage(
                performative=SigningMessage.Performative.SIGN_TRANSACTION,
                # skip content: terms
                raw_transaction=RawTransaction(),  # check it please!
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGN_MESSAGE,
                # skip content: terms
                raw_message=RawMessage(),  # check it please!
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                # skip content: signed_transaction
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                # skip content: signed_message
            ),
            SigningMessage(
                performative=SigningMessage.Performative.ERROR,
                # skip content: error_code
            ),
        ]
