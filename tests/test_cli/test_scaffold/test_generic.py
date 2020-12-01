# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This test module contains the tests for CLI scaffold generic methods and commands."""

from unittest import TestCase, mock

from aea.cli import cli

from tests.conftest import CLI_LOG_OPTION, CliRunner


@mock.patch("aea.cli.scaffold.scaffold_item")
@mock.patch("aea.cli.utils.decorators._check_aea_project")
class ScaffoldContractCommandTestCase(TestCase):
    """Test case for CLI scaffold contract command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_scaffold_contract_command_positive(self, *mocks):
        """Test for CLI scaffold contract command for positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "contract", "contract_name"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
