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
"""This test module contains the tests for the scaffold connection."""
import os
import sys
from unittest.mock import MagicMock

import pytest

from aea.configurations.base import ConnectionConfig
from aea.connections.scaffold.connection import MyScaffoldAsyncConnection
from aea.helpers.base import cd
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.common.pexpect_popen import PexpectWrapper
from tests.conftest import ROOT_DIR


class TestScaffoldConnectionReception:
    """Test that the stub connection is implemented correctly."""

    def setup(self):
        """Set case up."""
        configuration = ConnectionConfig(
            connection_id=MyScaffoldAsyncConnection.connection_id,
        )
        self.connection = MyScaffoldAsyncConnection(
            configuration=configuration, data_dir=MagicMock()
        )

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


class TestScaffoldConnectionAndRun(AEATestCaseEmpty):
    """Test that the scaffold connection created."""

    def setup(self):
        """Set case up."""
        result = self.invoke("scaffold", "connection", "my_con")
        assert result.exit_code == 0

    def test_run_and_not_implemented_error(self):
        """Test aea run crashes with connect not implemented for scaffolded connection."""
        self.generate_private_key()
        self.add_private_key()
        with cd(self._get_cwd()):
            proc = PexpectWrapper(  # nosec
                [sys.executable, "-m", "aea.cli", "-v", "DEBUG", "run"],
                env={
                    **os.environ,
                    "PYTHONPATH": ROOT_DIR + ":" + os.environ.get("PYTHONPATH", ""),
                },
                maxread=10000,
                encoding="utf-8",
                logfile=sys.stdout,
            )
            try:
                proc.expect_all(
                    [
                        "Error while connecting <class 'connection_module.MyScaffoldAsyncConnection'>: NotImplementedError()"
                    ],
                    timeout=50,
                )
            finally:
                proc.terminate()
                proc.wait_to_complete(timeout=50)
