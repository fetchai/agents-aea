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

"""This test module contains Negative tests for Libp2p connection."""

import asyncio
from asyncio.futures import Future
from unittest.mock import Mock, patch

import pytest

from packages.valory.connections.p2p_libp2p.connection import Libp2pNode
from packages.valory.protocols.acn.message import AcnMessage


DEFAULT_NET_SIZE = 4


@pytest.mark.asyncio
async def test_max_restarts() -> None:
    """Test node max restarts exception."""
    node = Libp2pNode(Mock(), Mock(), "tmp", "tmp", max_restarts=0)
    with pytest.raises(ValueError, match="Max restarts attempts reached:"):
        await node.restart()


@pytest.mark.asyncio
async def test_send_acn_confirm_failed() -> None:
    """Test nodeclient send fails on confirmation from other point ."""

    node = Libp2pNode(Mock(), Mock(), "tmp", "tmp")
    f: Future = Future()
    f.set_result(None)
    node.pipe = Mock()
    node.pipe.connect = Mock(return_value=f)
    node.pipe.write = Mock(return_value=f)

    node_client = node.get_client()
    status = Mock()
    status.code = int(AcnMessage.StatusBody.StatusCode.ERROR_GENERIC)
    status_future: Future = Future()
    status_future.set_result(status)
    with patch.object(
        node_client, "make_acn_envelope_message", return_value=b"some_data"
    ), patch.object(
        node_client, "wait_for_status", lambda: status_future
    ), pytest.raises(
        Exception, match=r"failed to send envelope. got error confirmation"
    ):
        await node_client.send_envelope(Mock())


@pytest.mark.asyncio
async def test_send_acn_confirm_timeout() -> None:
    """Test node client send fails on timeout."""

    node = Libp2pNode(Mock(), Mock(), "tmp", "tmp")
    f: Future = Future()
    f.set_result(None)
    node.pipe = Mock()
    node.pipe.connect = Mock(return_value=f)
    node.pipe.write = Mock(return_value=f)

    node_client = node.get_client()
    node_client.ACN_ACK_TIMEOUT = 0.5
    with patch.object(
        node_client, "make_acn_envelope_message", return_value=b"some_data"
    ), patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()), pytest.raises(
        Exception, match=r"acn status await timeout!"
    ):
        await node_client.send_envelope(Mock())


@pytest.mark.asyncio
async def test_acn_decode_error_on_read() -> None:
    """Test ACN decode error on read."""

    node = Libp2pNode(Mock(), Mock(), "tmp", "tmp")
    f: Future = Future()
    f.set_result(b"some_data")
    node.pipe = Mock()
    node.pipe.connect = Mock(return_value=f)

    node_client = node.get_client()
    node_client.ACN_ACK_TIMEOUT = 0.5

    with patch.object(node_client, "_read", lambda: f), patch.object(
        node_client, "write_acn_status_error", return_value=f
    ) as mocked_write_acn_status_error, pytest.raises(
        Exception, match=r"Error parsing acn message:"
    ):
        await node_client.read_envelope()

    mocked_write_acn_status_error.assert_called_once()


@pytest.mark.asyncio
async def test_write_acn_error() -> None:
    """Test write ACN error."""

    node = Libp2pNode(Mock(), Mock(), "tmp", "tmp")
    f: Future = Future()
    f.set_result(b"some_data")
    node.pipe = Mock()
    node.pipe.connect = Mock(return_value=f)

    node_client = node.get_client()

    with patch.object(node_client, "_write", return_value=f) as write_mock:
        await node_client.write_acn_status_error("some error")

    write_mock.assert_called_once()
