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

"""This module contains the tests for the Multiplexer."""

import asyncio
import shutil
import tempfile
import time
import unittest.mock
from pathlib import Path
from threading import Thread
from unittest import mock

import pytest

import aea
from aea.configurations.base import PublicId
from aea.mail.base import AEAConnectionError, Envelope, EnvelopeContext, Multiplexer
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

from packages.fetchai.connections.local.connection import LocalNode, OEFLocalConnection

from .conftest import (
    UNKNOWN_CONNECTION_PUBLIC_ID,
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    _make_dummy_connection,
    _make_local_connection,
    _make_stub_connection,
    logger,
)


@pytest.mark.asyncio
async def test_receiving_loop_terminated():
    """Test that connecting twice the multiplexer behaves correctly."""
    multiplexer = Multiplexer([_make_dummy_connection()])
    multiplexer.connect()

    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        multiplexer.connection_status.is_connected = False
        await multiplexer._receiving_loop()
        mock_logger_debug.assert_called_with("Receiving loop terminated.")
        multiplexer.connection_status.is_connected = True
        multiplexer.disconnect()


def test_connect_twice():
    """Test that connecting twice the multiplexer behaves correctly."""
    multiplexer = Multiplexer([_make_dummy_connection()])

    assert not multiplexer.connection_status.is_connected
    multiplexer.connect()
    assert multiplexer.connection_status.is_connected
    multiplexer.connect()
    assert multiplexer.connection_status.is_connected

    multiplexer.disconnect()


def test_connect_twice_with_loop():
    """Test that connecting twice the multiplexer behaves correctly."""
    running_loop = asyncio.new_event_loop()
    thread_loop = Thread(target=running_loop.run_forever)
    thread_loop.start()

    try:
        multiplexer = Multiplexer([_make_dummy_connection()], loop=running_loop,)

        with unittest.mock.patch.object(
            aea.mail.base.logger, "debug"
        ) as mock_logger_debug:
            assert not multiplexer.connection_status.is_connected
            multiplexer.connect()
            assert multiplexer.connection_status.is_connected
            multiplexer.connect()
            assert multiplexer.connection_status.is_connected

            mock_logger_debug.assert_called_with("Multiplexer already connected.")

    finally:
        multiplexer.disconnect()
        running_loop.call_soon_threadsafe(running_loop.stop)
        thread_loop.join()


@pytest.mark.asyncio
async def test_connect_twice_a_single_connection():
    """Test that connecting twice a single connection behaves correctly."""
    connection = _make_dummy_connection()
    multiplexer = Multiplexer([connection])

    assert not multiplexer.connection_status.is_connected
    await multiplexer._connect_one(connection.connection_id)
    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        await multiplexer._connect_one(connection.connection_id)
        mock_logger_debug.assert_called_with(
            "Connection fetchai/dummy:0.1.0 already established."
        )
        await multiplexer._disconnect_one(connection.connection_id)


def test_multiplexer_connect_all_raises_error():
    """Test the case when the multiplexer raises an exception while connecting."""
    multiplexer = Multiplexer([_make_dummy_connection()])

    with unittest.mock.patch.object(multiplexer, "_connect_all", side_effect=Exception):
        with pytest.raises(
            AEAConnectionError, match="Failed to connect the multiplexer."
        ):
            multiplexer.connect()


def test_multiplexer_connect_one_raises_error_many_connections():
    """Test the case when the multiplexer raises an exception while attempting the connection of one connection."""
    node = LocalNode()
    tmpdir = Path(tempfile.mkdtemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "input_file.csv"

    connection_1 = _make_local_connection("my_addr", node)
    connection_2 = _make_stub_connection(input_file_path, output_file_path)
    connection_3 = _make_dummy_connection()
    multiplexer = Multiplexer([connection_1, connection_2, connection_3])

    assert not connection_1.connection_status.is_connected
    assert not connection_2.connection_status.is_connected
    assert not connection_3.connection_status.is_connected

    with unittest.mock.patch.object(connection_3, "connect", side_effect=Exception):
        with pytest.raises(
            AEAConnectionError, match="Failed to connect the multiplexer."
        ):
            multiplexer.connect()

    assert not connection_1.connection_status.is_connected
    assert not connection_2.connection_status.is_connected
    assert not connection_3.connection_status.is_connected

    try:
        shutil.rmtree(tmpdir)
    except OSError as e:
        logger.warning("Couldn't delete {}".format(tmpdir))
        logger.exception(e)


@pytest.mark.asyncio
async def test_disconnect_twice_a_single_connection():
    """Test that connecting twice a single connection behaves correctly."""
    connection = _make_dummy_connection()
    multiplexer = Multiplexer([_make_dummy_connection()])

    assert not multiplexer.connection_status.is_connected
    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        await multiplexer._disconnect_one(connection.connection_id)
        mock_logger_debug.assert_called_with(
            "Connection fetchai/dummy:0.1.0 already disconnected."
        )


def test_multiplexer_disconnect_all_raises_error():
    """Test the case when the multiplexer raises an exception while disconnecting."""
    multiplexer = Multiplexer([_make_dummy_connection()])
    multiplexer.connect()

    assert multiplexer.connection_status.is_connected

    with unittest.mock.patch.object(
        multiplexer, "_disconnect_all", side_effect=Exception()
    ):
        with pytest.raises(
            AEAConnectionError  # , match="Failed to disconnect the multiplexer."
        ):
            multiplexer.disconnect()

        assert not multiplexer.connection_status.is_connected


@pytest.mark.asyncio
async def test_multiplexer_disconnect_one_raises_error_many_connections():
    """Test the case when the multiplexer raises an exception while attempting the disconnection of one connection."""
    with LocalNode() as node:
        tmpdir = Path(tempfile.mkdtemp())
        d = tmpdir / "test_stub"
        d.mkdir(parents=True)
        input_file_path = d / "input_file.csv"
        output_file_path = d / "input_file.csv"

        connection_1 = _make_local_connection("my_addr", node)
        connection_2 = _make_stub_connection(input_file_path, output_file_path)
        connection_3 = _make_dummy_connection()
        multiplexer = Multiplexer([connection_1, connection_2, connection_3])

        assert not connection_1.connection_status.is_connected
        assert not connection_2.connection_status.is_connected
        assert not connection_3.connection_status.is_connected

        multiplexer.connect()

        assert connection_1.connection_status.is_connected
        assert connection_2.connection_status.is_connected
        assert connection_3.connection_status.is_connected

        with unittest.mock.patch.object(
            connection_3, "disconnect", side_effect=Exception
        ):
            multiplexer.disconnect()

        assert not connection_1.connection_status.is_connected
        assert not connection_2.connection_status.is_connected
        assert connection_3.connection_status.is_connected

        # clean the test up.
        await connection_3.disconnect()
        multiplexer.disconnect()
        try:
            shutil.rmtree(tmpdir)
        except OSError as e:
            logger.warning("Couldn't delete {}".format(tmpdir))
            logger.exception(e)


@pytest.mark.asyncio
async def test_sending_loop_does_not_start_if_multiplexer_not_connected():
    """Test that the sending loop is stopped does not start if the multiplexer is not connected."""
    multiplexer = Multiplexer([_make_dummy_connection()])

    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        await multiplexer._send_loop()
        mock_logger_debug.assert_called_with(
            "Sending loop not started. The multiplexer is not connected."
        )


@pytest.mark.asyncio
async def test_sending_loop_cancelled():
    """Test the case when the sending loop is cancelled."""
    multiplexer = Multiplexer([_make_dummy_connection()])

    multiplexer.connect()
    await asyncio.sleep(0.1)
    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        multiplexer.disconnect()
        mock_logger_debug.assert_any_call("Sending loop cancelled.")


@pytest.mark.asyncio
async def test_receiving_loop_raises_exception():
    """Test the case when an error occurs when a receive is started."""
    connection = _make_dummy_connection()
    multiplexer = Multiplexer([connection])

    with unittest.mock.patch.object(
        connection, "receive", side_effect=Exception("a weird error.")
    ):
        with unittest.mock.patch.object(
            aea.mail.base.logger, "error"
        ) as mock_logger_error:
            multiplexer.connect()
            time.sleep(0.1)
            mock_logger_error.assert_called_with(
                "Error in the receiving loop: a weird error."
            )
    multiplexer.disconnect()


@pytest.mark.asyncio
async def test_send_envelope_with_non_registered_connection():
    """Test that sending an envelope with an unregistered connection raises an exception."""
    connection = _make_dummy_connection()
    multiplexer = Multiplexer([connection])
    multiplexer.connect()

    envelope = Envelope(
        to="",
        sender="",
        protocol_id=DefaultMessage.protocol_id,
        message=b"",
        context=EnvelopeContext(connection_id=UNKNOWN_CONNECTION_PUBLIC_ID),
    )

    with pytest.raises(AEAConnectionError, match="No connection registered with id:.*"):
        await multiplexer._send(envelope)

    multiplexer.disconnect()


def test_send_envelope_error_is_logged_by_send_loop():
    """Test that the AEAConnectionError in the '_send' method is logged by the '_send_loop'."""
    connection = _make_dummy_connection()
    multiplexer = Multiplexer([connection])
    multiplexer.connect()
    fake_connection_id = UNKNOWN_CONNECTION_PUBLIC_ID

    envelope = Envelope(
        to="",
        sender="",
        protocol_id=DefaultMessage.protocol_id,
        message=b"",
        context=EnvelopeContext(connection_id=fake_connection_id),
    )

    with unittest.mock.patch.object(aea.mail.base.logger, "error") as mock_logger_error:
        multiplexer.put(envelope)
        time.sleep(0.1)
        mock_logger_error.assert_called_with(
            "No connection registered with id: {}.".format(fake_connection_id)
        )

    multiplexer.disconnect()


def test_get_from_multiplexer_when_empty():
    """Test that getting an envelope from the multiplexer when the input queue is empty raises an exception."""
    connection = _make_dummy_connection()
    multiplexer = Multiplexer([connection])

    with pytest.raises(aea.mail.base.Empty):
        multiplexer.get()


def test_multiple_connection():
    """Test that we can send a message with two different connections."""
    with LocalNode() as node:
        address_1 = "address_1"
        address_2 = "address_2"
        connection_1_id = PublicId.from_str("author/local_1:0.1.0")
        connection_2_id = PublicId.from_str("author/local_2:0.1.0")

        connection_1 = OEFLocalConnection(
            node, address=address_1, connection_id=connection_1_id
        )

        connection_2 = OEFLocalConnection(
            node, address=address_2, connection_id=connection_2_id
        )

        multiplexer = Multiplexer([connection_1, connection_2])

        assert not connection_1.connection_status.is_connected
        assert not connection_2.connection_status.is_connected

        multiplexer.connect()

        assert connection_1.connection_status.is_connected
        assert connection_2.connection_status.is_connected

        message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope_from_1_to_2 = Envelope(
            to=address_2,
            sender=address_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(message),
            context=EnvelopeContext(connection_id=connection_1_id),
        )
        multiplexer.put(envelope_from_1_to_2)

        actual_envelope = multiplexer.get(block=True, timeout=2.0)
        assert envelope_from_1_to_2 == actual_envelope

        envelope_from_2_to_1 = Envelope(
            to=address_1,
            sender=address_2,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(message),
            context=EnvelopeContext(connection_id=connection_2_id),
        )
        multiplexer.put(envelope_from_2_to_1)

        actual_envelope = multiplexer.get(block=True, timeout=2.0)
        assert envelope_from_2_to_1 == actual_envelope

        multiplexer.disconnect()


def test_send_message_no_supported_protocol():
    """Test the case when we send an envelope with a specific connection that does not support the protocol."""
    with LocalNode() as node:
        address_1 = "address_1"
        public_id = PublicId.from_str("fetchai/my_private_protocol:0.1.0")
        connection_1 = _make_local_connection(
            address_1,
            node,
            restricted_to_protocols={public_id},
            excluded_protocols={public_id},
        )
        multiplexer = Multiplexer([connection_1])

        multiplexer.connect()

        with mock.patch.object(aea.mail.base.logger, "warning") as mock_logger_warning:
            protocol_id = UNKNOWN_PROTOCOL_PUBLIC_ID
            envelope = Envelope(
                to=address_1,
                sender=address_1,
                protocol_id=protocol_id,
                message=b"some bytes",
            )
            multiplexer.put(envelope)
            time.sleep(0.5)
            mock_logger_warning.assert_called_with(
                "Connection {} cannot handle protocol {}. Cannot send the envelope.".format(
                    connection_1.connection_id, protocol_id
                )
            )

        multiplexer.disconnect()
