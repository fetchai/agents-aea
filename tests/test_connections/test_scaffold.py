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
"""This test module contains the tests for the scaffold connection."""
import pytest

from aea.configurations.base import ConnectionConfig
from aea.connections.scaffold.connection import MyScaffoldConnection


class TestScaffoldConnectionReception:
    """Test that the stub connection is implemented correctly."""

    def setup(self):
        """Set case up."""
        configuration = ConnectionConfig(
            connection_id=MyScaffoldConnection.connection_id,
        )
        self.connection = MyScaffoldConnection(configuration=configuration)

    @pytest.mark.asyncio
    async def test_methods_not_implemented(self):
        """Test methods not implemented."""
        with pytest.raises(NotImplementedError):
            await self.connection.connect()

        with pytest.raises(NotImplementedError):
            await self.connection.disconnect()

        with pytest.raises(NotImplementedError):
            await self.connection.send(None)

        with pytest.raises(NotImplementedError):
            await self.connection.receive()
