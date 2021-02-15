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
"""This module contains the tests for the sync connection module."""
import asyncio
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from aea.configurations.data_types import PublicId
from aea.connections.base import BaseSyncConnection
from aea.mail.base import Envelope


class SampleConnection(BaseSyncConnection):
    """Sample connection for testing."""

    MAX_WORKER_THREADS = 3

    connection_id = PublicId("test", "test", "0.1.0")
    PAUSE = 0.5

    def __init__(self, *args, **kwargs):
        """Init connection."""
        super().__init__(*args, **kwargs)
        self.main_called = False
        self.send_counter = 0
        self.on_connect_called = False
        self.on_disconnect_called = False

    def main(self):
        """Run main."""
        self.main_called = True
        envelope = Mock()
        envelope.message = "main"
        self.put_envelope(envelope)

    def on_send(self, envelope: Envelope) -> None:
        """Run on send."""
        time.sleep(self.PAUSE)
        resp_envelope = Mock()
        resp_envelope.message = f"resp for {str(envelope.message)}"
        self.put_envelope(resp_envelope)
        self.send_counter += 1

    def on_connect(self):
        """Run on connect."""
        self.on_connect_called = True

    def on_disconnect(self):
        """Run on disconnect."""
        self.on_disconnect_called = True


@pytest.mark.asyncio
async def test_sync_connection():
    """Test sync connection example."""
    conf = Mock()
    conf.public_id = SampleConnection.connection_id
    conf.config = {}
    con = SampleConnection(conf, MagicMock())
    await asyncio.wait_for(con.connect(), timeout=10)
    assert con.is_connected
    envelope = Mock()

    for i in range(10):
        envelope.message = str(i)
        await asyncio.wait_for(con.send(envelope), timeout=10)

    await asyncio.sleep(con.PAUSE * 1.5)
    await asyncio.wait_for(con.disconnect(), timeout=10)
    assert con.is_disconnected

    assert con.on_connect_called
    assert con.on_disconnect_called
    assert con.main_called
    assert con.send_counter == con.MAX_WORKER_THREADS

    with patch.object(con, "_ensure_connected"):
        envelope = await con.receive()
        assert envelope.message == "main"
