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

from unittest import TestCase

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection


class ConnectionTestCase(TestCase):
    """Test case for Connection abstract class."""

    def setUp(self):
        """Set the tst up."""

        class TestConnection(Connection):
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

        self.TestConnection = TestConnection

    def test_loop_positive(self):
        """Test loop property positive result."""
        obj = self.TestConnection(
            ConnectionConfig("some_connection", "fetchai", "0.1.0")
        )
        obj._loop = "loop"
        obj.loop

    def test_excluded_protocols_positive(self):
        """Test excluded_protocols property positive result."""
        obj = self.TestConnection(
            ConnectionConfig("some_connection", "fetchai", "0.1.0")
        )
        obj._excluded_protocols = "excluded_protocols"
        obj.excluded_protocols
