# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This test module contains the tests for the stub connection."""
# type: ignore # noqa: E800
# pylint: skip-file

import asyncio
import base64
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

from aea.configurations.base import ConnectionConfig, PublicId
from aea.crypto.wallet import CryptoStore
from aea.helpers.file_io import write_with_lock
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.stub.connection import (
    StubConnection,
    envelope_from_bytes,
    lock_file,
    write_envelope,
)
from packages.fetchai.protocols.default.message import DefaultMessage


SEPARATOR = ","
PACKAGE_DIR = Path(__file__).parent.parent
MAX_FLAKY_RERUNS = 3


def _make_stub_connection(input_file_path: str, output_file_path: str):
    configuration = ConnectionConfig(
        input_file=input_file_path,
        output_file=output_file_path,
        connection_id=StubConnection.connection_id,
    )
    connection = StubConnection(configuration=configuration, data_dir=mock.MagicMock())
    return connection


def make_test_envelope() -> Envelope:
    """Create a test envelope."""
    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    msg.to = "any"
    envelope = Envelope(
        to="any",
        sender="any",
        message=msg,
    )
    return envelope


class TestStubConnectionReception:
    """Test that the stub connection is implemented correctly."""

    def setup(self):
        """Set the test up."""
        self.cwd = os.getcwd()
        self.tmpdir = Path(tempfile.mkdtemp())
        d = self.tmpdir / "test_stub"
        d.mkdir(parents=True)
        self.input_file_path = d / "input_file.csv"
        self.output_file_path = d / "output_file.csv"
        self.connection = _make_stub_connection(
            self.input_file_path, self.output_file_path
        )

        self.multiplexer = Multiplexer([self.connection])
        self.multiplexer.connect()
        os.chdir(self.tmpdir)

    def test_reception_a(self):
        """Test that the connection receives what has been enqueued in the input file."""
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        expected_envelope = Envelope(
            to="any",
            sender="anys",
            message=msg,
        )

        with open(self.input_file_path, "ab+") as f:
            write_envelope(expected_envelope, f)

        actual_envelope = self.multiplexer.get(block=True, timeout=3.0)
        assert expected_envelope.to == actual_envelope.to
        assert expected_envelope.sender == actual_envelope.sender
        assert (
            expected_envelope.protocol_specification_id
            == actual_envelope.protocol_specification_id
        )
        msg = DefaultMessage.serializer.decode(actual_envelope.message)
        msg.to = actual_envelope.to
        msg.sender = actual_envelope.sender
        assert expected_envelope.message == msg

    def test_reception_b(self):
        """Test that the connection receives what has been enqueued in the input file."""
        # a message containing delimiters and newline characters
        msg = b"\x08\x02\x12\x011\x1a\x011 \x01:,\n*0x32468d\n,\nB8Ab795\n\n49B49C88DC991990E7910891,,dbd\n"
        protocol_specification_id = PublicId.from_str("some_author/some_name:0.1.0")
        encoded_envelope = "{}{}{}{}{}{}{}{}".format(
            "any",
            SEPARATOR,
            "any",
            SEPARATOR,
            protocol_specification_id,
            SEPARATOR,
            msg.decode("utf-8"),
            SEPARATOR,
        )
        encoded_envelope = encoded_envelope.encode("utf-8")

        with open(self.input_file_path, "ab+") as f:
            write_with_lock(f, encoded_envelope)

        actual_envelope = self.multiplexer.get(block=True, timeout=3.0)
        assert "any" == actual_envelope.to
        assert "any" == actual_envelope.sender
        assert protocol_specification_id == actual_envelope.protocol_specification_id
        assert msg == actual_envelope.message

    def test_reception_c(self):
        """Test that the connection receives what has been enqueued in the input file."""
        encoded_envelope = b"0x5E22777dD831A459535AA4306AceC9cb22eC4cB5,default_oef,fetchai/default:1.0.0,\x08\x02\x12\x011\x1a\x011 \x01:,\n*0x32468dB8Ab79549B49C88DC991990E7910891dbd,"
        expected_envelope = Envelope(
            to="0x5E22777dD831A459535AA4306AceC9cb22eC4cB5",
            sender="default_oef",
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=b"\x08\x02\x12\x011\x1a\x011 \x01:,\n*0x32468dB8Ab79549B49C88DC991990E7910891dbd",
        )
        with open(self.input_file_path, "ab+") as f:
            write_with_lock(f, encoded_envelope)

        actual_envelope = self.multiplexer.get(block=True, timeout=3.0)
        assert expected_envelope == actual_envelope

    def teardown(self):
        """Tear down the test."""
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.tmpdir)
        except (OSError, IOError):
            pass
        self.multiplexer.disconnect()


class TestStubConnectionSending:
    """Test that the stub connection is implemented correctly."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.tmpdir = Path(tempfile.mkdtemp())
        d = cls.tmpdir / "test_stub"
        d.mkdir(parents=True)
        cls.input_file_path = d / "input_file.csv"
        cls.output_file_path = d / "output_file.csv"
        cls.connection = _make_stub_connection(
            cls.input_file_path, cls.output_file_path
        )

        cls.multiplexer = Multiplexer([cls.connection])
        cls.multiplexer.connect()
        os.chdir(cls.tmpdir)

    def test_connection_is_established(self):
        """Test the stub connection is established and then bad formatted messages."""
        assert self.connection.is_connected
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        encoded_envelope = "{}{}{}{}{}{}{}{}".format(
            "any",
            SEPARATOR,
            "any",
            SEPARATOR,
            DefaultMessage.protocol_specification_id,
            SEPARATOR,
            DefaultMessage.serializer.encode(msg).decode("utf-8"),
            SEPARATOR,
        )
        encoded_envelope = base64.b64encode(encoded_envelope.encode("utf-8"))
        envelope = envelope_from_bytes(encoded_envelope)
        if envelope is not None:
            self.connection._put_envelopes([envelope])

        assert (
            self.connection.in_queue.empty()
        ), "The inbox must be empty due to bad encoded message"

    def test_send_message(self):
        """Test that the messages in the outbox are posted on the output file."""
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        expected_envelope = Envelope(
            to="any",
            sender="anys",
            message=msg,
        )

        self.multiplexer.put(expected_envelope)
        time.sleep(0.1)

        with open(self.output_file_path, "rb+") as f:
            lines = f.readlines()

        assert len(lines) == 2
        line = lines[0] + lines[1]
        to, sender, protocol_specification_id, message, end = line.strip().split(
            "{}".format(SEPARATOR).encode("utf-8"), maxsplit=4
        )
        to = to.decode("utf-8")
        sender = sender.decode("utf-8")
        protocol_specification_id = PublicId.from_str(
            protocol_specification_id.decode("utf-8")
        )
        assert end in [b"", b"\n"]

        actual_envelope = Envelope(
            to=to,
            sender=sender,
            protocol_specification_id=protocol_specification_id,
            message=message,
        )
        assert expected_envelope.to == actual_envelope.to
        assert expected_envelope.sender == actual_envelope.sender
        assert (
            expected_envelope.protocol_specification_id
            == actual_envelope.protocol_specification_id
        )
        msg = DefaultMessage.serializer.decode(actual_envelope.message)
        msg.to = actual_envelope.to
        msg.sender = actual_envelope.sender
        assert expected_envelope.message == msg

    @classmethod
    def teardown_class(cls):
        """Tear down the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.tmpdir)
        except (OSError, IOError):
            pass
        cls.multiplexer.disconnect()


@pytest.mark.asyncio
async def test_disconnection_when_already_disconnected():
    """Test the case when disconnecting a connection already disconnected."""
    tmpdir = Path(tempfile.mkdtemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "output_file.csv"
    connection = _make_stub_connection(input_file_path, output_file_path)

    assert not connection.is_connected
    await connection.disconnect()
    assert not connection.is_connected


@pytest.mark.asyncio
async def test_connection_when_already_connected():
    """Test the case when connecting a connection already connected."""
    tmpdir = Path(tempfile.mkdtemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "output_file.csv"
    connection = _make_stub_connection(input_file_path, output_file_path)

    assert not connection.is_connected
    await connection.connect()
    assert connection.is_connected
    await connection.connect()
    assert connection.is_connected

    await connection.disconnect()


@pytest.mark.asyncio
async def test_receiving_returns_none_when_error_occurs():
    """Test that when we try to receive an envelope and an error occurs we return None."""
    tmpdir = Path(tempfile.mkdtemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "output_file.csv"
    connection = _make_stub_connection(input_file_path, output_file_path)

    await connection.connect()
    with mock.patch.object(connection.in_queue, "get", side_effect=Exception):
        ret = await connection.receive()
        assert ret is None

    await connection.disconnect()


@pytest.mark.asyncio
async def test_multiple_envelopes():
    """Test many envelopes received."""
    tmpdir = Path(tempfile.mkdtemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "output_file.csv"
    connection = _make_stub_connection(input_file_path, output_file_path)

    num_envelopes = 5
    await connection.connect()
    assert connection.is_connected

    async def wait_num(num):
        for _ in range(num):
            assert await connection.receive()

    task = asyncio.get_event_loop().create_task(wait_num(num_envelopes))

    with open(input_file_path, "ab+") as f:
        for _ in range(num_envelopes):
            write_envelope(make_test_envelope(), f)
            await asyncio.sleep(0.01)  # spin asyncio loop

    await asyncio.wait_for(task, timeout=3)
    await connection.disconnect()


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.asyncio
async def test_bad_envelope():
    """Test bad format envelop."""
    tmpdir = Path(tempfile.mkdtemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "output_file.csv"
    connection = _make_stub_connection(input_file_path, output_file_path)

    await connection.connect()

    with open(input_file_path, "ab+") as f:
        f.write(b"1,2,3,4,5,")
        f.flush()

    with pytest.raises(asyncio.TimeoutError):
        f = asyncio.ensure_future(connection.receive())
        await asyncio.wait_for(f, timeout=0.1)

    await connection.disconnect()


@pytest.mark.asyncio
async def test_load_from_dir():
    """Test stub connection can be loaded from dir."""
    with mock.patch.object(
        Path, "touch"
    ) as touch_mock:  # to prevent this test from creating the input_file file
        StubConnection.from_dir(
            str(PACKAGE_DIR),
            Identity("name", "address", "public_key"),
            CryptoStore(),
            os.getcwd(),
        )
        touch_mock.assert_any_call()


class TestFileLock:
    """Test for filelocks."""

    def test_lock_file_ok(self):
        """Work ok ok for random file."""
        with tempfile.TemporaryFile() as fp:
            with lock_file(fp):
                pass

    def test_lock_file_error(self):
        """Fail on closed file."""
        with tempfile.TemporaryFile() as fp:
            fp.close()
            with pytest.raises(ValueError):
                with lock_file(fp):
                    pass
