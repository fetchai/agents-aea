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

"""This test module contains negative tests for Libp2p tcp client connection."""

import asyncio
import os
from asyncio.futures import Future
from unittest.mock import Mock, patch

import pytest

from aea.configurations.base import ConnectionConfig

from packages.valory.connections.p2p_libp2p_client.connection import (
    NodeClient,
    P2PLibp2pClientConnection,
)

from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    _process_cert,
    create_identity,
    libp2p_log_on_failure_all,
    make_cert_request,
    ports,
)


DONE_FUTURE: asyncio.Future = asyncio.Future()
DONE_FUTURE.set_result(None)


@pytest.mark.asyncio
class TestLibp2pClientConnectionFailureNodeNotConnected(BaseP2PLibp2pTest):
    """Test that connection fails when node not running"""

    public_key = BaseP2PLibp2pTest.default_crypto.public_key
    connection = _make_libp2p_client_connection(peer_public_key=public_key)

    @pytest.mark.asyncio
    async def test_node_not_running(self):
        """Test the node is not running."""
        with pytest.raises(Exception):
            await self.connection.connect()

    @pytest.mark.asyncio
    async def test_connect_attempts(self):
        """Test connect attempts."""

        self.connection.connect_retries = 2
        with patch(
            "aea.helpers.pipe.TCPSocketChannelClient.connect",
            side_effect=Exception("test exception on connect"),
        ) as open_connection_mock:
            with pytest.raises(Exception, match="test exception on connect"):
                await self.connection.connect()
            assert open_connection_mock.call_count == self.connection.connect_retries

    @pytest.mark.asyncio
    async def test_reconnect_on_receive_fail(self):
        """Test reconnect on receive fails."""

        self.connection._in_queue = Mock()
        self.connection._node_client = Mock()
        exception_future = Future()
        exception_future.set_exception(ConnectionError("oops"))
        result = Future()
        result.set_result(None)
        self.connection._node_client.read_envelope.side_effect = [
            exception_future,
            result,
        ]

        with patch.object(
            self.connection, "_perform_connection_to_node", return_value=DONE_FUTURE
        ) as connect_mock:
            assert await self.connection._read_envelope_from_node() is None
            connect_mock.assert_called()

    @pytest.mark.asyncio
    async def test_reconnect_on_send_fail(self):
        """Test reconnect on send fails."""

        self.connection._node_client = Mock()
        f = Future()
        f.set_exception(Exception("oops"))
        self.connection._node_client.send_envelope.side_effect = Exception("oops")
        with patch.object(
            self.connection, "_perform_connection_to_node", return_value=DONE_FUTURE
        ) as connect_mock, patch.object(
            self.connection, "_ensure_valid_envelope_for_external_comms"
        ):
            with pytest.raises(Exception, match="oops"):
                await self.connection._send_envelope_with_node_client(Mock())
            connect_mock.assert_called()


@pytest.mark.asyncio
async def test_acn_decode_error_on_read():
    """Test node client send fails on read."""
    f = Future()
    f.set_result(b"some_data")
    pipe = Mock()
    pipe.connect = Mock(return_value=f)

    node_client = NodeClient(pipe, Mock())
    with patch.object(node_client, "_read", lambda: f), patch.object(
        node_client, "write_acn_status_error", return_value=f
    ) as mocked_write_acn_status_error, pytest.raises(
        Exception, match=r"Error parsing acn message:"
    ):
        await node_client.read_envelope()

    mocked_write_acn_status_error.assert_called_once()


@libp2p_log_on_failure_all
class TestLibp2pClientConnectionFailureConnectionSetup(BaseP2PLibp2pTest):
    """Test that connection fails when setup incorrectly"""

    connection_cls = P2PLibp2pClientConnection

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        BaseP2PLibp2pTest.setup_class()

        crypto = cls.ethereum_crypto
        cls.node_host = "localhost"
        cls.node_port = next(ports)
        cls.identity = create_identity(crypto)
        cls.key_file = os.path.join(cls.tmp, "keyfile")
        crypto.dump(cls.key_file)
        cls.public_key = cls.default_crypto.public_key
        ledger = cls.default_crypto.identifier
        cls.cert_request = make_cert_request(
            cls.public_key, ledger, f"./{crypto.address}"
        )
        _process_cert(crypto, cls.cert_request, cls.tmp)

    def test_empty_nodes(self):
        """Test empty nodes."""

        uri = f"{self.node_host}:{self.node_port}"
        node = {"uri": uri, "public_key": self.public_key}
        configuration = ConnectionConfig(
            tcp_key_file=self.key_file,
            nodes=[node],
            connection_id=self.connection_cls.connection_id,
            cert_requests=[self.cert_request],
        )
        self.connection_cls(
            configuration=configuration, data_dir=self.tmp, identity=self.identity
        )

        configuration = ConnectionConfig(
            tcp_key_file=self.key_file,
            nodes=None,
            connection_id=self.connection_cls.connection_id,
        )
        with pytest.raises(Exception):
            self.connection_cls(
                configuration=configuration,
                data_dir=self.tmp,
                identity=self.identity,
            )


@libp2p_log_on_failure_all
class TestLibp2pClientConnectionNodeDisconnected(BaseP2PLibp2pTest):
    """Test that connection will properly handle node disconnecting"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        BaseP2PLibp2pTest.setup_class()

        delegate_port = next(ports)
        cls.connection_node = cls.make_connection(
            delegate=True,
            delegate_port=delegate_port,
        )
        cls.connection_client = cls.make_client_connection(
            peer_public_key=cls.connection_node.node.pub,
            node_port=delegate_port,
        )

    def test_node_disconnected(self):
        """Test node disconnected."""
        assert self.all_connected
        self.multiplexers[1].disconnect()
        self.multiplexers[0].disconnect()
        assert self.all_disconnected


@pytest.mark.asyncio
class TestLibp2pClientConnectionCheckSignature(BaseP2PLibp2pTest):
    """Test that TLS signature is checked properly."""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.delegate_port = next(ports)

        cls.connection_node = _make_libp2p_connection(
            delegate_port=cls.delegate_port,
            delegate=True,
        )
        cls.connection = _make_libp2p_client_connection(
            peer_public_key=cls.connection_node.node.pub,
            node_port=cls.delegate_port,
        )

    @pytest.mark.asyncio
    async def test_signature_check_fail(self):
        """Test signature check failed."""

        key = self.libp2p_crypto
        assert self.connection.is_connected is False
        await self.connection_node.connect()
        self.connection.connect_retries = 1
        try:
            self.connection.node_por._representative_public_key = key.public_key
            expected = (
                ".*Invalid TLS session key signature: Signature verification failed.*"
            )
            with pytest.raises(ValueError, match=expected):
                await self.connection.connect()
            assert self.connection.is_connected is False
        finally:
            await self.connection_node.disconnect()
