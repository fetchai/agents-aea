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
"""This module contains the tests for the base module."""
import asyncio
import os
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest

import aea
from aea.configurations.base import (
    ComponentId,
    ComponentType,
    ConnectionConfig,
    PublicId,
)
from aea.configurations.loader import load_component_configuration
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import AEAComponentLoadException, AEAEnforceError
from aea.mail.base import Envelope

from tests.conftest import CUR_PATH


class TConnection(Connection):
    """Test class for Connection."""

    connection_id = PublicId.from_str("fetchai/some_connection:0.1.0")

    def connect(self, *args, **kwargs):
        """Connect."""
        pass

    def disconnect(self, *args, **kwargs):
        """Disconnect."""
        pass

    def from_config(self, *args, **kwargs):
        """From config."""
        pass

    def receive(self, *args, **kwargs):
        """Receive."""
        pass

    def send(self, *args, **kwargs):
        """Send."""
        pass


class TestConnectionTestCase:
    """Test case for Connection abstract class."""

    TConnection = TConnection

    @pytest.mark.asyncio
    async def test_loop_only_in_running_loop(self):
        """Test loop property positive result."""
        obj = self.TConnection(
            ConnectionConfig("some_connection", "fetchai", "0.1.0"), MagicMock()
        )
        obj.loop

    def test_loop_fails_on_non_running_loop(self):
        """Test loop property positive result."""
        obj = self.TConnection(
            ConnectionConfig("some_connection", "fetchai", "0.1.0"), MagicMock()
        )
        with pytest.raises(AEAEnforceError):
            obj.loop

    def test_excluded_protocols_positive(self):
        """Test excluded_protocols property positive result."""
        obj = self.TConnection(
            ConnectionConfig("some_connection", "fetchai", "0.1.0"), MagicMock()
        )
        obj._excluded_protocols = "excluded_protocols"
        obj.excluded_protocols


def test_loop_property():
    """Test connection's loop property."""
    connection = TConnection(
        MagicMock(public_id=TConnection.connection_id), MagicMock()
    )
    with unittest.mock.patch.object(aea.connections.base, "enforce"):
        loop = connection.loop
        assert isinstance(loop, asyncio.AbstractEventLoop)


def test_ensure_valid_envelope_for_external_comms_negative_cases():
    """Test the staticmethod '_ensure_valid_envelope_for_external_comms', negative cases."""
    protocol_specification_id = PublicId("author", "name", "0.1.0")
    wrong_sender = wrong_to = "author/name:0.1.0"
    envelope_wrong_sender = Envelope(
        to=wrong_to,
        sender=wrong_sender,
        protocol_specification_id=protocol_specification_id,
        message=b"",
    )
    with pytest.raises(
        AEAEnforceError,
        match=f"Sender and to field of envelope is public id, needs to be address. Found: sender={wrong_sender}, to={wrong_to}",
    ):
        Connection._ensure_valid_envelope_for_external_comms(envelope_wrong_sender)


def test_state():
    """Test connect context of a connection."""
    connection = TConnection(
        MagicMock(public_id=TConnection.connection_id), MagicMock()
    )
    assert connection.state == ConnectionStates.disconnected

    with connection._connect_context():
        assert connection.state == ConnectionStates.connecting

    assert connection.state == ConnectionStates.connected


def test_ensure_connected():
    """Test ensure_connected method."""
    connection = TConnection(
        MagicMock(public_id=TConnection.connection_id), MagicMock()
    )
    assert not connection.is_connected
    with pytest.raises(
        ConnectionError, match="Connection is not connected! Connect first!"
    ):
        connection._ensure_connected()

    connection._state.set(ConnectionStates.connected)
    connection._ensure_connected()


def test_from_dir():
    """Test Connection.from_dir"""
    dummy_connection_dir = os.path.join(CUR_PATH, "data", "dummy_connection")
    identity = MagicMock()
    identity.name = "agent_name"
    crypto_store = MagicMock()

    data_dir = MagicMock()
    connection = Connection.from_dir(
        dummy_connection_dir, identity, crypto_store, data_dir
    )
    assert isinstance(connection, Connection)
    assert connection.component_id == ComponentId(
        ComponentType.CONNECTION, PublicId("fetchai", "dummy", "0.1.0")
    )


def test_from_config_exception_path():
    """Test Connection.from_config with exception"""
    dummy_connection_dir = os.path.join(CUR_PATH, "data", "dummy_connection")
    configuration = cast(
        ConnectionConfig,
        load_component_configuration(
            ComponentType.CONNECTION, Path(dummy_connection_dir)
        ),
    )
    wrong_dir = os.path.join(CUR_PATH, "data", "wrong_connection")
    configuration.directory = Path(wrong_dir)
    identity = MagicMock()
    identity.name = "agent_name"
    crypto_store = MagicMock()
    data_dir = MagicMock()
    with pytest.raises(AEAComponentLoadException, match="Connection module"):
        Connection.from_config(configuration, identity, crypto_store, data_dir)


def test_from_config_exception_class():
    """Test Connection.from_config with exception"""
    dummy_connection_dir = os.path.join(CUR_PATH, "data", "dummy_connection")
    configuration = cast(
        ConnectionConfig,
        load_component_configuration(
            ComponentType.CONNECTION, Path(dummy_connection_dir)
        ),
    )
    configuration.directory = Path(dummy_connection_dir)
    configuration.class_name = "WrongName"
    identity = MagicMock()
    identity.name = "agent_name"
    crypto_store = MagicMock()
    data_dir = MagicMock()
    with pytest.raises(AEAComponentLoadException, match="Connection class"):
        Connection.from_config(configuration, identity, crypto_store, data_dir)


def test_set_base_state():
    """Check error raised on bad state set."""
    con = TConnection(
        configuration=ConnectionConfig("some_connection", "fetchai", "0.1.0"),
        data_dir=MagicMock(),
    )
    with pytest.raises(ValueError, match="Incorrect state.*"):
        con.state = "some bad state"
