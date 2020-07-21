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
"""This test module contains the tests for the `aea add contract` sub-command."""

import os
from unittest import TestCase, mock

import pytest

from aea.cli import cli
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import CLI_LOG_OPTION, CliRunner, MAX_FLAKY_RERUNS


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.utils.decorators._validate_config_consistency")
class AddContractCommandTestCase(TestCase):
    """Test that the command 'aea add contract' works as expected."""

    def setUp(self):
        """Set the test up."""
        self.runner = CliRunner()

    @mock.patch("aea.cli.add.add_item")
    def test_add_contract_positive(self, *mocks):
        """Test add contract command positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "contract", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "contract", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


class TestAddContractFromRemoteRegistry(AEATestCaseEmpty):
    """Test case for add contract from Registry command."""

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_add_contract_from_remote_registry_positive(self):
        """Test add contract from Registry positive result."""
        self.add_item("contract", "fetchai/erc1155:0.1.0", local=False)

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "contracts")
        items_folders = os.listdir(items_path)
        item_name = "erc1155"
        assert item_name in items_folders
