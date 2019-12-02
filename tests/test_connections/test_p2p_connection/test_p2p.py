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

"""Peer to Peer connection and channel."""
from aea.connections.p2p.connection import PeerToPeerConnection
from unittest import mock
import logging
from fetchai.ledger.crypto import entity
import pytest

from aea.mail.base import Envelope

logger = logging.getLogger(__name__)


class TestP2p:
    """Contains the test for the p2p connection."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.address = "127.0.0.1"
        cls.port = 8000
        m_fet_key = "6d56fd47e98465824aa85dfe620ad3dbf092b772abc6c6a182e458b5c56ad13b"
        cls.ent = entity.Entity.from_hex(m_fet_key)
        cls.p2p_connection = PeerToPeerConnection(public_key=cls.ent.public_key_hex,
                                                  provider_addr=cls.address,
                                                  provider_port=cls.port)

    def test_initialization(self):
        """Test the initialisation of the class."""
        assert self.p2p_connection.public_key == self.ent.public_key_hex

    def test_connect(self):
        """Test the connection to the search service."""
        with mock.patch("fetch.p2p.api.http_calls.HTTPCalls.register") as mocked_register:
            mocked_register.return_value = {"status": "OK"}
            self.p2p_connection.connect()
            assert self.p2p_connection.connection_status.is_connected is True

    def test_disconnect(self):
        """Test the disconnect from the p2p connection."""
        with mock.patch("fetch.p2p.api.http_calls.HTTPCalls.register") as mocked_register:
            mocked_register.return_value = {"status": "OK"}
            self.p2p_connection.connect()
        with mock.patch("fetch.p2p.api.http_calls.HTTPCalls.unregister")as mocked_unregister:
            mocked_unregister.return_value = {'status': 'OK'}
            self.p2p_connection.disconnect()
            assert self.p2p_connection.connection_status.is_connected is False

    @pytest.mark.asyncio
    async def test_send(self):
        """Test the send functionality of the p2p connection."""
        with mock.patch("fetch.p2p.api.http_calls.HTTPCalls.register") as mocked_register:
            mocked_register.return_value = {"status": "OK"}
            self.p2p_connection.connect()
        envelope = Envelope(to="receiver", sender="sender", protocol_id="protocol", message=b"Hello")
        with mock.patch("fetch.p2p.api.http_calls.HTTPCalls.send_message") as mocked_send_message:
            mocked_send_message.return_value = {'status': 'OK'}
            await self.p2p_connection.send(envelope=envelope)
            # TODO: Consider returning the response from the server in order to be able to assert that the message send!
            assert self.p2p_connection._connection.empty() is True

    # @pytest.mark.asyncio
    # async def test_receive(self):
    #     """Test the receive functionality of the p2p connection."""
    #
    #     s_msg = {"FROM": {"NODE_ADDRESS": "node_address",
    #                       "SENDER_ADDRESS": "sender_address"},
    #              "TO": {"NODE_ADDRESS": "node_address",
    #                     "RECEIVER_ADDRESS": "receiver_address"},
    #              "PROTOCOL": "protocol",
    #              "CONTEXT": "context",
    #              "PAYLOAD": "payload"}
    #     messages = [s_msg]
    #     with mock.patch("fetch.p2p.api.http_calls.HTTPCalls.get_messages") as mocked_get_messages:
    #         mocked_get_messages.return_value = messages
    #         env = await self.p2p_connection.receive()
    #         logger.info(env)
    #         assert env.get("PROTOCOL") == "protocol"
