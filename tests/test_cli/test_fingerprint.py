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
"""This test module contains the tests for CLI fingerprint command."""

from unittest import TestCase, mock

from click import ClickException

from aea.cli import cli
from aea.cli.fingerprint import fingerprint_item

from tests.conftest import CLI_LOG_OPTION, CliRunner
from tests.test_cli.tools_for_testing import ConfigLoaderMock, ContextMock, PublicIdMock


@mock.patch("aea.cli.fingerprint.fingerprint_item")
class FingerprintCommandTestCase(TestCase):
    """Test case for CLI fingerprint command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_fingerprint_positive(self, *mocks):
        """Test for CLI fingerprint positive result."""
        public_id = "author/name:0.1.0"
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fingerprint", "connection", public_id],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fingerprint", "contract", public_id],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fingerprint", "protocol", public_id],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fingerprint", "skill", public_id],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


def _raise_exception(*args, **kwargs):
    raise Exception()


@mock.patch("aea.cli.fingerprint.Path.open", mock.mock_open())
class FingerprintItemTestCase(TestCase):
    """Test case for fingerprint_item method."""

    @mock.patch("aea.cli.fingerprint.Path.exists", return_value=False)
    @mock.patch(
        "aea.cli.fingerprint.ConfigLoader.from_configuration_type",
        return_value=ConfigLoaderMock(),
    )
    def test_fingerprint_item_package_not_found(self, *mocks):
        """Test for fingerprint_item package not found result."""
        public_id = PublicIdMock()
        with self.assertRaises(ClickException) as cm:
            fingerprint_item(ContextMock(), "skill", public_id)
        self.assertIn("Package not found at path", cm.exception.message)

    @mock.patch(
        "aea.cli.fingerprint.ConfigLoader.from_configuration_type", _raise_exception
    )
    def test_fingerprint_item_exception(self, *mocks):
        """Test for fingerprint_item exception raised."""
        public_id = PublicIdMock()
        with self.assertRaises(ClickException):
            fingerprint_item(ContextMock(), "skill", public_id)
