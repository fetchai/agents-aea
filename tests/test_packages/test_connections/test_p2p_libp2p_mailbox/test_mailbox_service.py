# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2019 Fetch.AI Limited
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

"""This test module contains tests for P2PLibp2p connection."""

import re
from unittest.mock import Mock

import pytest
import requests

from aea.mail.base import Envelope

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.valory.connections.p2p_libp2p_mailbox.connection import NodeClient
from packages.valory.protocols.acn import acn_pb2
from packages.valory.protocols.acn.message import AcnMessage

from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    ports,
)


MockDefaultMessageProtocol = Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@pytest.mark.asyncio
class TestMailboxAPI(BaseP2PLibp2pTest):
    """Test that connection is established and torn down correctly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.delegate_port = next(ports)
        cls.mailbox_port = next(ports)

        cls.connection_node = cls.make_connection(
            delegate=True,
            delegate_port=cls.delegate_port,
            mailbox=True,
            mailbox_port=cls.mailbox_port,
        )

        cls.connection_client = cls.make_client_connection(
            peer_public_key=cls.connection_node.node.pub,
            node_port=cls.delegate_port,
        )

    @pytest.mark.asyncio
    async def test_message_delivery(self):  # nosec
        """Test connect then disconnect."""

        url = f"https://localhost:{self.mailbox_port}"
        r = requests.get(f"{url}/ssl_signature", verify=False)  # nosec
        assert r.status_code == 200, r.text

        node_client = NodeClient(Mock(), self.connection_client.node_por)
        agent_record = node_client.make_agent_record()
        addr = agent_record.address
        performative = acn_pb2.AcnMessage.Register_Performative()  # type: ignore
        AcnMessage.AgentRecord.encode(
            performative.record, agent_record  # pylint: disable=no-member
        )
        data = performative.record.SerializeToString()  # pylint: disable=no-member

        r = requests.post(f"{url}/register", data=data, verify=False)  # nosec
        assert r.status_code == 200, r.text
        assert re.match(
            "[0-9a-f]{32}", r.text, re.I
        ), r.text  # pylint: disable=no-member
        session_id = r.text

        envelope = self.enveloped_default_message(to=addr, sender=addr)
        r = requests.post(
            f"{url}/send_envelope",
            data=envelope.encode(),
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 200, r.text

        r = requests.get(
            f"{url}/get_envelope",
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 200, r.text
        assert r.content, "no envelope"

        delivered_envelope = Envelope.decode(r.content)
        self.sent_is_delivered_envelope(envelope, delivered_envelope)

        # no new envelopes
        r = requests.get(
            f"{url}/get_envelope",
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 200, r.text
        assert not r.content

        # unregister
        r = requests.get(
            f"{url}/unregister",
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 200, r.text

        # bad session!
        r = requests.get(
            f"{url}/get_envelope",
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 400, r.text
        assert "session_id" in r.text
