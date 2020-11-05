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
"""Test module for Registry publish methods."""

from unittest import TestCase, mock

import click
import pytest
from click import ClickException

from aea.cli import cli
from aea.cli.publish import (
    _check_is_item_in_local_registry,
    _check_is_item_in_registry_mixed,
    _check_is_item_in_remote_registry,
    _save_agent_locally,
    _validate_pkp,
)
from aea.configurations.base import PublicId
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import CLI_LOG_OPTION, CliRunner
from tests.test_cli.tools_for_testing import (
    ContextMock,
    PublicIdMock,
    raise_click_exception,
)


@mock.patch("aea.cli.publish.PublicId", PublicIdMock)
@mock.patch("aea.cli.publish._check_is_item_in_local_registry")
@mock.patch("aea.cli.publish.copyfile")
@mock.patch("aea.cli.publish.os.makedirs")
@mock.patch("aea.cli.publish.os.path.exists", return_value=False)
@mock.patch("aea.cli.publish.try_get_item_target_path", return_value="target-dir")
@mock.patch("aea.cli.publish.os.path.join", return_value="joined-path")
class SaveAgentLocallyTestCase(TestCase):
    """Test case for _save_agent_locally method."""

    def test_save_agent_locally_positive(
        self,
        path_join_mock,
        try_get_item_target_path_mock,
        path_exists_mock,
        makedirs_mock,
        copyfile_mock,
        _check_is_item_in_local_registry_mock,
    ):
        """Test for save_agent_locally positive result."""
        _save_agent_locally(
            ContextMock(
                connections=["author/default_connection:version", "author/name:version"]
            )
        )
        makedirs_mock.assert_called_once_with("target-dir", exist_ok=True)
        copyfile_mock.assert_called_once_with("joined-path", "joined-path")


class CheckIsItemInLocalRegistryTestCase(TestCase):
    """Test case for _check_is_item_in_local_registry method."""

    @mock.patch("aea.cli.publish.try_get_item_source_path")
    def test__check_is_item_in_local_registry_positive(self, get_path_mock):
        """Test for _check_is_item_in_local_registry positive result."""
        public_id = PublicIdMock.from_str("author/name:version")
        registry_path = "some-registry-path"
        item_type_plural = "items"
        _check_is_item_in_local_registry(public_id, item_type_plural, registry_path)
        get_path_mock.assert_called_once_with(
            registry_path, public_id.author, item_type_plural, public_id.name
        )

    @mock.patch("aea.cli.publish.try_get_item_source_path", raise_click_exception)
    def test__check_is_item_in_local_registry_negative(self):
        """Test for _check_is_item_in_local_registry negative result."""
        public_id = PublicIdMock.from_str("author/name:version")
        registry_path = "some-registry-path"
        item_type_plural = "items"
        with self.assertRaises(ClickException):
            _check_is_item_in_local_registry(public_id, item_type_plural, registry_path)


@mock.patch("aea.cli.utils.decorators._check_aea_project")
@mock.patch("aea.cli.publish._save_agent_locally")
@mock.patch("aea.cli.publish.publish_agent")
@mock.patch("aea.cli.publish._validate_pkp")
@mock.patch("aea.cli.publish._validate_config")
@mock.patch("aea.cli.publish.cast", return_value=ContextMock())
class PublishCommandTestCase(TestCase):
    """Test case for CLI publish command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_publish_positive(self, *mocks):
        """Test for CLI publish positive result."""
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "publish", "--local"], standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "publish", "--remote"], standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "publish"], standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


class ValidatePkpTestCase(TestCase):
    """Test case for _validate_pkp method."""

    def test__validate_pkp_positive(self):
        """Test _validate_pkp for positive result."""
        private_key_paths = mock.Mock()
        private_key_paths.read_all = mock.Mock(return_value=[])
        _validate_pkp(private_key_paths)
        private_key_paths.read_all.assert_called_once()

    def test__validate_pkp_negative(self):
        """Test _validate_pkp for negative result."""
        private_key_paths = mock.Mock()
        private_key_paths.read_all = mock.Mock(return_value=[1, 2])
        with self.assertRaises(ClickException):
            _validate_pkp(private_key_paths)
        private_key_paths.read_all.assert_called_once()


@mock.patch("aea.cli.publish._check_is_item_in_registry_mixed")
@mock.patch("aea.cli.publish._check_is_item_in_local_registry")
class TestPublishMixedMode(AEATestCaseEmpty):
    """Test the execution branch with in mixed mode."""

    def test_publish_positive(self, *mocks):
        """Test for CLI publish positive result."""
        self.set_config("agent.description", "some-description")
        self.run_cli_command("publish", cwd=self._get_cwd())


def test_negative_check_is_item_in_remote_registry():
    """Test the utility function (negative) to check if an item is in the remote registry"""
    with pytest.raises(click.ClickException, match="Not found in Registry."):
        _check_is_item_in_remote_registry(
            PublicId("nonexisting_package_author", "nonexisting_package_name", "0.0.0"),
            "protocol",
        )


def test_negative_check_is_item_in_registry_mixed():
    """Check if item in registry, mixed mode."""
    with pytest.raises(
        click.ClickException,
        match="Package not found neither in local nor in remote registry: Not found in Registry.",
    ):
        _check_is_item_in_registry_mixed(
            PublicId("nonexisting_package_author", "nonexisting_package_name", "0.0.0"),
            "protocol",
            "nonexisting_packages_path",
        )


def test_positive_check_is_item_in_registry_mixed_not_locally_but_remotely():
    """Check if item in registry, mixed mode, when not in local registry but only in remote."""
    _check_is_item_in_registry_mixed(
        PublicId.from_str("fetchai/default:0.8.0"),
        "protocols",
        "nonexisting_packages_path",
    )
