# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
import os
import re
import shutil
import tempfile
from unittest.mock import Mock

import pytest
import requests

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.p2p_libp2p_mailbox.connection import NodeClient
from packages.fetchai.protocols.acn import acn_pb2
from packages.fetchai.protocols.acn.message import AcnMessage
from packages.fetchai.protocols.default import DefaultSerializer
from packages.fetchai.protocols.default.message import DefaultMessage

from tests.common.utils import wait_for_condition
from tests.conftest import _make_libp2p_client_connection, _make_libp2p_connection


MockDefaultMessageProtocol = Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@pytest.mark.asyncio
class TestMailboxAPI:
    """Test that connection is established and torn down correctly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.temp_dir = os.path.join(cls.t, "temp_dir_node")
        os.mkdir(cls.temp_dir)
        cls.connection_node = _make_libp2p_connection(
            data_dir=cls.temp_dir, delegate=True, mailbox=True
        )
        temp_dir_client1 = os.path.join(cls.t, "temp_dir_client")
        os.mkdir(temp_dir_client1)
        temp_dir_client2 = os.path.join(cls.t, "temp_dir_client2")
        os.mkdir(temp_dir_client2)
        cls.connection1 = _make_libp2p_client_connection(
            data_dir=temp_dir_client1, peer_public_key=cls.connection_node.node.pub
        )

        cls.connection2 = _make_libp2p_client_connection(
            data_dir=temp_dir_client2, peer_public_key=cls.connection_node.node.pub
        )
        cls.multiplexer1 = Multiplexer([cls.connection_node])
        cls.multiplexer1.connect()

        wait_for_condition(lambda: cls.connection_node.is_connected is True, 10)

    @pytest.mark.asyncio
    async def test_message_delivery(self):  # nosec
        """Test connnect then disconnect."""
        r = requests.get("https://localhost:8888/ssl_signature", verify=False)  # nosec
        assert r.status_code == 200, r.text

        node_client = NodeClient(Mock(), self.connection2.node_por)
        agent_record = node_client.make_agent_record()
        addr = agent_record.address
        performative = acn_pb2.AcnMessage.Register_Performative()  # type: ignore
        AcnMessage.AgentRecord.encode(
            performative.record, agent_record  # pylint: disable=no-member
        )
        data = performative.record.SerializeToString()  # pylint: disable=no-member

        r = requests.post(
            "https://localhost:8888/register", data=data, verify=False  # nosec
        )
        assert r.status_code == 200, r.text
        assert re.match(
            "[0-9a-f]{32}", r.text, re.I
        ), r.text  # pylint: disable=no-member
        session_id = r.text

        envelope = self.make_envelope(addr, addr)
        r = requests.post(
            "https://localhost:8888/send_envelope",
            data=envelope.encode(),
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 200, r.text

        r = requests.get(
            "https://localhost:8888/get_envelope",
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 200, r.text
        assert r.content, "no envelope"

        delivered_envelope = Envelope.decode(r.content)
        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message == envelope.message

        # no new envelopes
        r = requests.get(
            "https://localhost:8888/get_envelope",
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 200, r.text
        assert not r.content

        # unregister
        r = requests.get(
            "https://localhost:8888/unregister",
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 200, r.text

        # bad session!
        r = requests.get(
            "https://localhost:8888/get_envelope",
            headers={"Session-Id": session_id},
            verify=False,  # nosec
        )
        assert r.status_code == 400, r.text
        assert "session_id" in r.text

    def make_envelope(self, from_: str, to_: str) -> Envelope:
        """Make sample envelope."""
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope = Envelope(
            to=to_,
            sender=from_,
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
        )
        return envelope

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.multiplexer1.disconnect()
        os.chdir(cls.cwd)
        print(open(cls.connection_node.node.log_file, "r").read())
        try:

            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
