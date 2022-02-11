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
"""This test module contains the tests for CLI fingerprint command."""
from pathlib import Path
from unittest import TestCase, mock
from unittest.mock import MagicMock

import pytest
from click import ClickException

from aea.cli import cli
from aea.cli.fingerprint import fingerprint_item
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import _check_aea_project
from aea.configurations.constants import (
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import CLI_LOG_OPTION, CliRunner
from tests.test_cli.tools_for_testing import ConfigLoaderMock, ContextMock, PublicIdMock


@mock.patch("aea.cli.fingerprint.fingerprint_package")
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

    def _run_fingerprint_by_path(self):
        """Call fingerprint by-path cli command."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fingerprint", "by-path", "some_dir"],
            standalone_mode=False,
            catch_exceptions=False,
        )
        self.assertEqual(result.exit_code, 0, result.exception)

    def test_by_path_ok(self, fingerprint_mock):
        """Test fingerprint by_path works ok."""
        with mock.patch("os.listdir", return_value=[DEFAULT_CONNECTION_CONFIG_FILE]):
            self._run_fingerprint_by_path()
            fingerprint_mock.assert_called()

    def test_by_path_exceptions(self, *mocks):
        """Test fingerprint by_path works raises exceptions."""
        with pytest.raises(
            ClickException,
            match="No package config file found in `.*`. Incorrect directory?",
        ):
            with mock.patch("os.listdir", return_value=[]):
                self._run_fingerprint_by_path()

        with pytest.raises(
            ClickException,
            match="Too many config files in the directory, only one has to present!",
        ):
            with mock.patch(
                "os.listdir",
                return_value=[
                    DEFAULT_CONNECTION_CONFIG_FILE,
                    DEFAULT_SKILL_CONFIG_FILE,
                ],
            ):
                self._run_fingerprint_by_path()


def _raise_exception(*args, **kwargs):
    raise Exception()


@mock.patch("aea.cli.fingerprint.open_file", mock.mock_open())
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


class TestFingerprintAgent(AEATestCaseEmpty):
    """Check fingerprint for agent."""

    def test_fingerprint(self):
        """Check fingerprint calculated and checked properly."""
        r = self.invoke("fingerprint")
        assert "calculated" in r.stdout

        click_context = MagicMock()
        click_context.obj = Context(self._get_cwd(), "", registry_path=None)
        click_context.obj.config["skip_consistency_check"] = True

        _check_aea_project([click_context], check_finger_prints=True)

        (Path(self._get_cwd()) / "some_file.txt").write_text("sdfds")
        with pytest.raises(
            ClickException, match=r"Fingerprints for package .* do not match"
        ):
            _check_aea_project([click_context], check_finger_prints=True)

        self.invoke("fingerprint")
        _check_aea_project([click_context], check_finger_prints=True)
