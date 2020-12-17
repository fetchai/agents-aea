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
import logging
import os
import shutil
import sys
import tempfile
import time
import unittest.mock
from pathlib import Path
from threading import Thread
from unittest import mock
from unittest.mock import MagicMock, call, patch

import pytest
from pexpect.exceptions import EOF  # type: ignore

import aea
from aea.cli.core import cli
from aea.configurations.base import PublicId
from aea.connections.base import ConnectionStates
from aea.exceptions import AEAEnforceError
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.identity.base import Identity
from aea.mail.base import AEAConnectionError, Envelope, EnvelopeContext
from aea.multiplexer import AsyncMultiplexer, InBox, Multiplexer, OutBox
from aea.test_tools.click_testing import CliRunner

from packages.fetchai.connections.local.connection import LocalNode
from packages.fetchai.connections.p2p_libp2p.connection import (
    PUBLIC_ID as P2P_PUBLIC_ID,
)
from packages.fetchai.protocols.default.message import DefaultMessage

from .conftest import (
    AUTHOR,
    CLI_LOG_OPTION,
    ROOT_DIR,
    UNKNOWN_CONNECTION_PUBLIC_ID,
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    _make_dummy_connection,
    _make_local_connection,
    _make_stub_connection,
    logger,
)
from tests.common.pexpect_popen import PexpectWrapper
from tests.common.utils import wait_for_condition


@pytest.mark.asyncio
async def test_receiving_loop_terminated():
    """Test that connecting twice the multiplexer behaves correctly."""
    multiplexer = Multiplexer([_make_dummy_connection()])
    multiplexer.connect()

    with unittest.mock.patch.object(multiplexer.logger, "debug") as mock_logger_debug:
        multiplexer.connection_status.set(ConnectionStates.disconnected)
        await multiplexer._receiving_loop()
        mock_logger_debug.assert_called_with("Receiving loop terminated.")
        multiplexer.connection_status.set(ConnectionStates.connected)
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


def test_disconnect_twice():
    """Test that connecting twice the multiplexer behaves correctly."""
    multiplexer = Multiplexer([_make_dummy_connection()])

    assert not multiplexer.connection_status.is_connected
    multiplexer.connect()
    assert multiplexer.connection_status.is_connected
    multiplexer.disconnect()
    multiplexer.disconnect()


def test_connect_twice_with_loop():
    """Test that connecting twice the multiplexer behaves correctly."""
    running_loop = asyncio.new_event_loop()
    thread_loop = Thread(target=running_loop.run_forever)
    thread_loop.start()

    try:
        multiplexer = Multiplexer([_make_dummy_connection()], loop=running_loop)

        with unittest.mock.patch.object(
            multiplexer.logger, "debug"
        ) as mock_logger_debug:
            assert not multiplexer.connection_status.is_connected
            multiplexer.connect()
            assert multiplexer.connection_status.is_connected
            multiplexer.connect()
            assert multiplexer.connection_status.is_connected

            mock_logger_debug.assert_called_with("Multiplexer already connected.")

            multiplexer.disconnect()
            running_loop.call_soon_threadsafe(running_loop.stop)
    finally:
        thread_loop.join()


@pytest.mark.asyncio
async def test_connect_twice_a_single_connection():
    """Test that connecting twice a single connection behaves correctly."""
    connection = _make_dummy_connection()
    multiplexer = Multiplexer([connection])

    assert not multiplexer.connection_status.is_connected
    await multiplexer._connect_one(connection.connection_id)
    with unittest.mock.patch.object(multiplexer.logger, "debug") as mock_logger_debug:
        await multiplexer._connect_one(connection.connection_id)
        mock_logger_debug.assert_called_with(
            "Connection fetchai/dummy:0.1.0 already established."
        )
        await multiplexer._disconnect_one(connection.connection_id)


@pytest.mark.asyncio
async def test_run_bad_conneect():
    """Test that connecting twice a single connection behaves correctly."""
    connection = _make_dummy_connection()
    multiplexer = AsyncMultiplexer([connection])
    f = asyncio.Future()
    f.set_result(None)
    with unittest.mock.patch.object(multiplexer, "connect", return_value=f):
        with pytest.raises(ValueError, match="Multiplexer is not connected properly."):
            await multiplexer.run()


def test_multiplexer_connect_all_raises_error():
    """Test the case when the multiplexer raises an exception while connecting."""
    multiplexer = Multiplexer([_make_dummy_connection()])

    with unittest.mock.patch.object(multiplexer, "_connect_all", side_effect=Exception):
        with pytest.raises(
            AEAConnectionError, match="Failed to connect the multiplexer."
        ):
            multiplexer.connect()
    multiplexer.disconnect()


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

    assert not connection_1.is_connected
    assert not connection_2.is_connected
    assert not connection_3.is_connected

    with unittest.mock.patch.object(connection_3, "connect", side_effect=Exception):
        with pytest.raises(
            AEAConnectionError, match="Failed to connect the multiplexer."
        ):
            multiplexer.connect()

    assert not connection_1.is_connected
    assert not connection_2.is_connected
    assert not connection_3.is_connected

    multiplexer.disconnect()
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
    with unittest.mock.patch.object(multiplexer.logger, "debug") as mock_logger_debug:
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
        multiplexer, "_disconnect_all", side_effect=Exception
    ):
        with pytest.raises(
            AEAConnectionError, match="Failed to disconnect the multiplexer."
        ):
            multiplexer.disconnect()

    # # do the true disconnection - for clean the test up
    assert multiplexer.connection_status.is_disconnecting
    multiplexer.disconnect()
    assert multiplexer.connection_status.is_disconnected


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

        assert not connection_1.is_connected
        assert not connection_2.is_connected
        assert not connection_3.is_connected

        multiplexer.connect()

        assert connection_1.is_connected
        assert connection_2.is_connected
        assert connection_3.is_connected

        with unittest.mock.patch.object(
            connection_3, "disconnect", side_effect=Exception
        ):
            with pytest.raises(
                AEAConnectionError, match="Failed to disconnect the multiplexer."
            ):
                multiplexer.disconnect()

        assert not connection_1.is_connected
        assert not connection_2.is_connected
        assert connection_3.is_connected

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

    with unittest.mock.patch.object(multiplexer.logger, "debug") as mock_logger_debug:
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
    with unittest.mock.patch.object(multiplexer.logger, "debug") as mock_logger_debug:
        multiplexer.disconnect()
        mock_logger_debug.assert_any_call("Sending loop cancelled.")


@pytest.mark.asyncio
async def test_receiving_loop_raises_exception():
    """Test the case when an error occurs when a receive is started."""
    connection = _make_dummy_connection()
    multiplexer = Multiplexer([connection])

    with unittest.mock.patch("asyncio.wait", side_effect=Exception("a weird error.")):
        with unittest.mock.patch.object(
            multiplexer.logger, "error"
        ) as mock_logger_error:
            multiplexer.connect()
            time.sleep(0.1)
            mock_logger_error.assert_called_with(
                "Error in the receiving loop: a weird error.", exc_info=True
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

    with unittest.mock.patch.object(multiplexer.logger, "error") as mock_logger_error:
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


def test_send_message_no_supported_protocol():
    """Test the case when we send an envelope with a specific connection that does not support the protocol."""
    with LocalNode() as node:
        identity_1 = Identity("", address="address_1")
        public_id = PublicId.from_str("fetchai/my_private_protocol:0.1.0")
        connection_1 = _make_local_connection(
            identity_1.address,
            node,
            restricted_to_protocols={public_id},
            excluded_protocols={public_id},
        )
        multiplexer = Multiplexer([connection_1])

        multiplexer.connect()

        with mock.patch.object(multiplexer.logger, "warning") as mock_logger_warning:
            protocol_id = UNKNOWN_PROTOCOL_PUBLIC_ID
            envelope = Envelope(
                to=identity_1.address,
                sender=identity_1.address,
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


def test_autoset_default_connection():
    """Set default connection automatically."""
    connection_1 = _make_dummy_connection()
    connection_2 = _make_dummy_connection()
    connections = [connection_1, connection_2]
    multiplexer = Multiplexer(connections)

    multiplexer._default_connection = None
    multiplexer._set_default_connection_if_none()
    assert multiplexer._default_connection == connections[0]


@pytest.mark.asyncio
async def test_disconnect_when_not_connected():
    """Test disconnect when not connected."""
    connection_1 = _make_dummy_connection()
    connections = [connection_1]
    multiplexer = AsyncMultiplexer(connections)
    with patch.object(multiplexer, "_disconnect_all") as disconnect_all_mocked:
        await multiplexer.disconnect()

    disconnect_all_mocked.assert_not_called()


@pytest.mark.asyncio
async def test_exit_on_none_envelope():
    """Test sending task exit on None envelope."""
    connection_1 = _make_dummy_connection()
    connections = [connection_1]
    multiplexer = AsyncMultiplexer(connections, loop=asyncio.get_event_loop())
    try:
        await multiplexer.connect()
        assert multiplexer.is_connected
        multiplexer.put(None)

        await asyncio.sleep(0.5)
        assert multiplexer._send_loop_task.done()
    finally:
        await multiplexer.disconnect()


@pytest.mark.asyncio
async def test_inbox_outbox():
    """Test InBox OutBox objects."""
    connection_1 = _make_dummy_connection()
    connections = [connection_1]
    multiplexer = AsyncMultiplexer(connections, loop=asyncio.get_event_loop())
    msg = DefaultMessage(performative=DefaultMessage.Performative.BYTES, content=b"",)
    msg.to = "to"
    msg.sender = "sender"
    context = EnvelopeContext(connection_id=connection_1.connection_id)
    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_id=msg.protocol_id,
        message=msg,
        context=context,
    )
    try:
        await multiplexer.connect()
        inbox = InBox(multiplexer)
        outbox = OutBox(multiplexer)

        assert inbox.empty()
        assert outbox.empty()

        outbox.put(envelope)
        received = await inbox.async_get()
        assert received == envelope

        assert inbox.empty()
        assert outbox.empty()

        outbox.put_message(msg, context=context)
        await inbox.async_wait()
        received = inbox.get_nowait()
        assert received == envelope

    finally:
        await multiplexer.disconnect()


@pytest.mark.asyncio
async def test_threaded_mode():
    """Test InBox OutBox objects in threaded mode."""
    connection_1 = _make_dummy_connection()
    connections = [connection_1]
    multiplexer = AsyncMultiplexer(connections, threaded=True)
    msg = DefaultMessage(performative=DefaultMessage.Performative.BYTES, content=b"",)
    msg.to = "to"
    msg.sender = "sender"
    context = EnvelopeContext(connection_id=connection_1.connection_id)
    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_id=msg.protocol_id,
        message=msg,
        context=context,
    )
    try:
        multiplexer.start()
        await asyncio.sleep(0.5)
        inbox = InBox(multiplexer)
        outbox = OutBox(multiplexer)

        assert inbox.empty()
        assert outbox.empty()

        outbox.put(envelope)
        received = await inbox.async_get()
        assert received == envelope

        assert inbox.empty()
        assert outbox.empty()

        outbox.put_message(msg, context=context)
        await inbox.async_wait()
        received = inbox.get_nowait()
        assert received == envelope

    finally:
        multiplexer.stop()


@pytest.mark.asyncio
async def test_outbox_negative():
    """Test InBox OutBox objects."""
    connection_1 = _make_dummy_connection()
    connections = [connection_1]
    multiplexer = AsyncMultiplexer(connections, loop=asyncio.get_event_loop())
    msg = DefaultMessage(performative=DefaultMessage.Performative.BYTES, content=b"",)
    context = EnvelopeContext(connection_id=connection_1.connection_id)
    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_id=msg.protocol_id,
        message=b"",
        context=context,
    )

    try:
        await multiplexer.connect()
        outbox = OutBox(multiplexer)

        assert outbox.empty()

        with pytest.raises(ValueError) as execinfo:
            outbox.put(envelope)
        assert (
            str(execinfo.value)
            == "Only Message type allowed in envelope message field when putting into outbox."
        )

        assert outbox.empty()

        with pytest.raises(ValueError) as execinfo:
            outbox.put_message("")
        assert str(execinfo.value) == "Provided message not of type Message."

        assert outbox.empty()

        with pytest.raises(ValueError) as execinfo:
            outbox.put_message(msg)
        assert str(execinfo.value) == "Provided message has message.to not set."

        assert outbox.empty()
        msg.to = "to"

        with pytest.raises(ValueError) as execinfo:
            outbox.put_message(msg)
        assert str(execinfo.value) == "Provided message has message.sender not set."

    finally:
        await multiplexer.disconnect()


@pytest.mark.asyncio
async def test_default_route_applied(caplog):
    """Test default route is selected automatically."""
    logger = logging.getLogger("aea.multiplexer")
    with caplog.at_level(logging.DEBUG, logger="aea.multiplexer"):
        connection_1 = _make_dummy_connection()
        connections = [connection_1]
        multiplexer = AsyncMultiplexer(connections, loop=asyncio.get_event_loop())
        multiplexer.logger = logger
        envelope = Envelope(
            to="",
            sender="",
            protocol_id=DefaultMessage.protocol_id,
            message=b"",
            context=EnvelopeContext(),
        )
        multiplexer.default_routing = {
            DefaultMessage.protocol_id: connection_1.connection_id
        }
        try:
            await multiplexer.connect()
            inbox = InBox(multiplexer)
            outbox = InBox(multiplexer)

            assert inbox.empty()
            assert outbox.empty()
            multiplexer.put(envelope)
            await outbox.async_get()
        finally:
            await multiplexer.disconnect()

            assert "Using default routing:" in caplog.text


def test_multiplexer_setup():
    """Test multiplexer setup to set connections."""
    node = LocalNode()
    tmpdir = Path(tempfile.mkdtemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "input_file.csv"

    connection_1 = _make_local_connection("my_addr", node)
    connection_2 = _make_stub_connection(input_file_path, output_file_path)
    connection_3 = _make_dummy_connection()
    connections = [connection_1, connection_2, connection_3]
    multiplexer = Multiplexer([])
    with pytest.raises(AEAEnforceError):
        multiplexer._connection_consistency_checks()
    multiplexer.setup(connections, default_routing=None)
    multiplexer._connection_consistency_checks()


class TestExceptionHandlingOnConnectionSend:
    """Test exception handling policy on connection.send."""

    def setup(self):
        """Set up test case."""
        self.connection = _make_dummy_connection()
        self.multiplexer = Multiplexer([self.connection])
        self.multiplexer.connect()

        self.envelope = Envelope(
            to="",
            sender="",
            protocol_id=DefaultMessage.protocol_id,
            message=b"",
            context=EnvelopeContext(connection_id=self.connection.connection_id),
        )
        self.exception = ValueError("expected")

    def teardown(self):
        """Tear down test case."""
        self.multiplexer.disconnect()

    def test_log_policy(self):
        """Test just log exception."""
        with patch.object(self.connection, "send", side_effect=self.exception):
            self.multiplexer._exception_policy = ExceptionPolicyEnum.just_log
            self.multiplexer.put(self.envelope)
            time.sleep(1)
            assert not self.multiplexer._send_loop_task.done()

    def test_propagate_policy(self):
        """Test propagate exception."""
        assert self.multiplexer._exception_policy == ExceptionPolicyEnum.propagate

        with patch.object(self.connection, "send", side_effect=self.exception):
            self.multiplexer.put(self.envelope)
            time.sleep(1)
            wait_for_condition(
                lambda: self.multiplexer._send_loop_task.done(), timeout=5
            )
            assert self.multiplexer._send_loop_task.exception() == self.exception

    def test_stop_policy(self):
        """Test stop multiplexer on exception."""
        with patch.object(self.connection, "send", side_effect=self.exception):
            self.multiplexer._exception_policy = ExceptionPolicyEnum.stop_and_exit
            self.multiplexer.put(self.envelope)
            time.sleep(1)
            wait_for_condition(
                lambda: self.multiplexer.connection_status.is_disconnected, timeout=5
            )

    def test_disconnect_order(self):
        """Test disconnect order: tasks first, disconnect_all next."""
        parent = MagicMock()

        async def fn():
            return

        with patch.object(
            self.multiplexer, "_stop_receive_send_loops", return_value=fn()
        ) as stop_loops, patch.object(
            self.multiplexer, "_disconnect_all", return_value=fn()
        ) as disconnect_all, patch.object(
            self.multiplexer, "_check_and_set_disconnected_state"
        ) as check_and_set_disconnected_state:
            parent.attach_mock(stop_loops, "stop_loops")
            parent.attach_mock(disconnect_all, "disconnect_all")
            parent.attach_mock(
                check_and_set_disconnected_state, "check_and_set_disconnected_state"
            )
            self.multiplexer.disconnect()
            assert parent.mock_calls == [
                call.stop_loops(),
                call.disconnect_all(),
                call.check_and_set_disconnected_state(),
            ]


class TestMultiplexerDisconnectsOnTermination:  # pylint: disable=attribute-defined-outside-init
    """Test multiplexer disconnects on  agent process keyboard interrupted."""

    def setup(self):
        """Set the test up."""
        self.proc = None
        self.runner = CliRunner()
        self.agent_name = "myagent"
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(self.t, "packages"))
        os.chdir(self.t)

        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", self.agent_name]
        )
        assert result.exit_code == 0

        os.chdir(Path(self.t, self.agent_name))

    def test_multiplexer_disconnected_on_early_interruption(self):
        """Test multiplexer disconnected properly on termination before connected."""
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "add", "--local", "connection", str(P2P_PUBLIC_ID)]
        )
        assert result.exit_code == 0, result.stdout_bytes

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "build"])
        assert result.exit_code == 0, result.stdout_bytes

        self.proc = PexpectWrapper(  # nosec
            [sys.executable, "-m", "aea.cli", "-v", "DEBUG", "run"],
            env=os.environ,
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )

        self.proc.expect_all(
            ["Starting libp2p node..."], timeout=50,
        )
        self.proc.control_c()
        self.proc.expect_all(
            ["Multiplexer .*disconnected."], timeout=20, strict=False,
        )

        self.proc.expect_all(
            [EOF], timeout=20,
        )

    def test_multiplexer_disconnected_on_termination_after_connected(self):
        """Test multiplexer disconnected properly on termination after connected."""
        self.proc = PexpectWrapper(  # nosec
            [sys.executable, "-m", "aea.cli", "-v", "DEBUG", "run"],
            env=os.environ,
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )

        self.proc.expect_all(
            ["Start processing messages..."], timeout=20,
        )
        self.proc.control_c()
        self.proc.expect_all(
            ["Multiplexer disconnecting...", "Multiplexer disconnected.", EOF],
            timeout=20,
        )

    def teardown(self):
        """Tear the test down."""
        if self.proc:
            self.proc.wait_to_complete(10)
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except (OSError, IOError):
            pass


def test_multiplexer_setup_replaces_connections():
    """Test proper connections reset on setup call."""
    m = AsyncMultiplexer([MagicMock(), MagicMock(), MagicMock()])
    assert len(m._id_to_connection) == 3
    assert len(m._connections) == 3

    m.setup([MagicMock()], MagicMock())
    assert len(m._id_to_connection) == 1
    assert len(m._connections) == 1
