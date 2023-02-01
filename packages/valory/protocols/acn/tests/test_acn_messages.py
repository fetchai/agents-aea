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

"""Test messages module for acn protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.valory.protocols.acn.custom_types import AgentRecord, StatusBody
from packages.valory.protocols.acn.message import AcnMessage


class TestMessageAcn(BaseProtocolMessagesTestCase):
    """Test for the 'acn' protocol message."""

    MESSAGE_CLASS = AcnMessage

    def build_messages(self) -> List[AcnMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            AcnMessage(
                performative=AcnMessage.Performative.REGISTER,
                record=AgentRecord(
                    address="address",
                    public_key="pbk",
                    peer_public_key="peerpbk",
                    signature="sign",
                    service_id="acn",
                    ledger_id="fetchai",
                ),
            ),
            AcnMessage(
                performative=AcnMessage.Performative.LOOKUP_REQUEST,
                agent_address="some str",
            ),
            AcnMessage(
                performative=AcnMessage.Performative.LOOKUP_RESPONSE,
                record=AgentRecord(
                    address="address",
                    public_key="pbk",
                    peer_public_key="peerpbk",
                    signature="sign",
                    service_id="acn",
                    ledger_id="fetchai",
                ),
            ),
            AcnMessage(
                performative=AcnMessage.Performative.AEA_ENVELOPE,
                envelope=b"some_bytes",
                record=AgentRecord(
                    address="address",
                    public_key="pbk",
                    peer_public_key="peerpbk",
                    signature="sign",
                    service_id="acn",
                    ledger_id="fetchai",
                ),
            ),
            AcnMessage(
                performative=AcnMessage.Performative.STATUS,
                body=StatusBody(
                    status_code=AcnMessage.StatusBody.StatusCode.ERROR_UNSUPPORTED_VERSION,
                    msgs=["pbk"],
                ),
            ),
        ]

    def build_inconsistent(self) -> List[AcnMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            AcnMessage(
                performative=AcnMessage.Performative.REGISTER,
                # skip content: record
            ),
            AcnMessage(
                performative=AcnMessage.Performative.LOOKUP_REQUEST,
                # skip content: agent_address
            ),
            AcnMessage(
                performative=AcnMessage.Performative.LOOKUP_RESPONSE,
                # skip content: record
            ),
            AcnMessage(
                performative=AcnMessage.Performative.AEA_ENVELOPE,
                # skip content: envelope
                record=AgentRecord(
                    address="address",
                    public_key="pbk",
                    peer_public_key="peerpbk",
                    signature="sign",
                    service_id="acn",
                    ledger_id="fetchai",
                ),
            ),
            AcnMessage(
                performative=AcnMessage.Performative.STATUS,
                # skip content: body
            ),
        ]
