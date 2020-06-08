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

"""This test module contains AEA cli tests for Libp2p tcp client connection."""

import functools
import os
import random
import string
import tempfile

import pytest

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

from ....conftest import (
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    libp2p_log_on_failure,
    skip_test_windows,
)

from aea.test_tools.test_cases import BaseAEATestCase

DEFAULT_PORT = 10234
DEFAULT_DELEGATE_PORT = 11234
DEFAULT_HOST = "127.0.0.1"
DEFAULT_CLIENTS_PER_NODE = 4

DEFAULT_LAUNCH_TIMEOUT = 5


def with_new_agent(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        self._create_agent()
        fn(self, *args, **kwargs)
        self.delete_agents(self.agent_name)

    return wrapper


@skip_test_windows
class TestP2PLibp2pClientConnectionAEARunning(BaseAEATestCase):
    """Test AEA with p2p_libp2p_client connection is correctly run"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set up the test class."""
        BaseAEATestCase.setup_class()

        cls.node_connection = _make_libp2p_connection(
            delegate_host=DEFAULT_HOST,
            delegate_port=DEFAULT_DELEGATE_PORT,
            delegate=True,
        )
        cls.node_multiplexer = Multiplexer([cls.node_connection])
        cls.log_files = [cls.node_connection.node.log_file]

        cls.node_multiplexer.connect()

    def test_node(self):
        assert self.node_connection.connection_status.is_connected is True

    @with_new_agent
    def test_connection(self):
        self.add_item("connection", "fetchai/p2p_libp2p_client:0.1.0")
        config_path = "vendor.fetchai.connections.p2p_libp2p_client.config"
        self.force_set_config(
            "{}.nodes".format(config_path),
            [{"uri": "{}:{}".format(DEFAULT_HOST, DEFAULT_DELEGATE_PORT)}],
        )

        process = self.run_agent()
        check_strings = "Successfully connected to libp2p node {}:{}".format(
            DEFAULT_HOST, DEFAULT_DELEGATE_PORT
        )
        self._assert_agent_running(process, check_strings)

    def _create_agent(self):
        self.agent_name = "agent-" + "".join(
            random.choices(string.ascii_lowercase, k=5)
        )
        self.set_agent_context(self.agent_name)
        self.create_agents(self.agent_name)

    def _assert_agent_running(
        self, process, check_strings="Successfully connected to libp2p node "
    ):
        is_running = self.is_running(process, timeout=DEFAULT_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        self.terminate_agents(process)
        assert self.is_successfully_terminated(
            process
        ), "AEA wasn't successfully terminated."

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        BaseAEATestCase.teardown_class()

        cls.node_multiplexer.disconnect()
