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
"""This test module contains the tests for the p2p_stub connection."""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.p2p_stub.connection import P2PStubConnection
from packages.fetchai.protocols.default.message import DefaultMessage


SEPARATOR = ","


def make_test_envelope(to_="any", sender_="sender") -> Envelope:
    """Create a test envelope."""
    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    msg.to = to_
    msg.sender = sender_
    envelope = Envelope(to=to_, sender=sender_, message=msg,)
    return envelope


class Testp2pStubConnectionReception:
    """Test that the stub connection is implemented correctly."""

    def setup(self):
        """Set the test up."""
        self.cwd = os.getcwd()
        self.tmpdir = Path(tempfile.mkdtemp())
        d = self.tmpdir / "test_p2p_stub"
        d.mkdir(parents=True)

        configuration = ConnectionConfig(
            namespace_dir=d, connection_id=P2PStubConnection.connection_id,
        )
        self.loop = asyncio.get_event_loop()
        self.identity1 = Identity("test", "con1", "public_key_1")
        self.identity2 = Identity("test", "con2", "public_key_2")
        self.connection1 = P2PStubConnection(
            configuration=configuration, data_dir=MagicMock(), identity=self.identity1
        )
        self.connection2 = P2PStubConnection(
            configuration=configuration, data_dir=MagicMock(), identity=self.identity2
        )
        os.chdir(self.tmpdir)

    @pytest.mark.asyncio
    async def test_send(self):
        """Test that the connection receives what has been enqueued in the input file."""
        await self.connection1.connect()
        assert self.connection1.is_connected

        await self.connection2.connect()
        assert self.connection2.is_connected

        envelope = make_test_envelope(to_="con2")
        await self.connection1.send(envelope)

        received_envelope = await asyncio.wait_for(
            self.connection2.receive(), timeout=5
        )
        assert received_envelope
        assert received_envelope.message == envelope.message.encode()

    def teardown(self):
        """Clean up after tests."""
        os.chdir(self.cwd)
        self.loop.run_until_complete(self.connection1.disconnect())
        self.loop.run_until_complete(self.connection2.disconnect())
        try:
            shutil.rmtree(self.tmpdir)
        except (OSError, IOError):
            pass
