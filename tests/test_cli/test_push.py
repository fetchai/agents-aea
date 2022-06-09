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
"""Test module for Registry push methods."""
import filecmp
import os
from unittest import TestCase, mock

import pytest
from click import ClickException

from aea.cli import cli
from aea.cli.push import _save_item_locally, check_package_public_id
from aea.cli.registry.settings import REMOTE_HTTP
from aea.cli.utils.constants import ITEM_TYPES
from aea.configurations.base import PublicId
from aea.test_tools.constants import DEFAULT_AUTHOR
from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.fetchai.skills.echo import PUBLIC_ID

from tests.conftest import AUTHOR, CLI_LOG_OPTION, CliRunner
from tests.test_cli.tools_for_testing import ContextMock, PublicIdMock


@mock.patch("aea.cli.push.copytree")
class SaveItemLocallyTestCase(TestCase):
    """Test case for save_item_locally method."""

    @mock.patch("aea.cli.push.try_get_item_target_path", return_value="target")
    @mock.patch("aea.cli.push.try_get_item_source_path", return_value="source")
    @mock.patch("aea.cli.push.check_package_public_id", return_value=None)
    def test_save_item_locally_positive(
        self,
        _check_package_public_id_mock,
        try_get_item_source_path_mock,
        try_get_item_target_path_mock,
        copy_tree_mock,
    ):
        """Test for save_item_locally positive result."""
        item_type = "skill"
        item_id = PublicIdMock()
        ctx_mock = ContextMock()
        _save_item_locally(ctx_mock, item_type, item_id)
        try_get_item_source_path_mock.assert_called_once_with(
            "cwd", None, "skills", item_id.name
        )
        try_get_item_target_path_mock.assert_called_once_with(
            ctx_mock.registry_path,
            item_id.author,
            item_type + "s",
            item_id.name,
        )
        _check_package_public_id_mock.assert_called_once_with(
            "source", item_type, item_id
        )
        copy_tree_mock.assert_called_once_with("source", "target")


@mock.patch("aea.cli.push.copytree")
class TestPushLocally(AEATestCaseEmpty):
    """Test case for cli push --local."""

    ITEM_PUBLIC_ID = PUBLIC_ID
    ITEM_TYPE = "skill"

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        super(TestPushLocally, cls).setup_class()
        cls.add_item(cls.ITEM_TYPE, str(cls.ITEM_PUBLIC_ID), local=True)

    def test_vendor_ok(
        self,
        copy_tree_mock,
    ):
        """Test ok for vendor's item."""

        with mock.patch("click.core._"):
            with mock.patch("os.path.exists", side_effect=[False, True, False]):
                self.invoke("push", "--local", "skill", "fetchai/echo")

        copy_tree_mock.assert_called_once()
        src_path, dst_path = copy_tree_mock.mock_calls[0][1]
        # check for correct author, type, name
        assert (
            os.path.normpath(src_path).split(os.sep)[-3:]
            == os.path.normpath(dst_path).split(os.sep)[-3:]
        )

    def test_user_ok(
        self,
        copy_tree_mock,
    ):
        """Test ok for users's item."""
        with mock.patch(
            "aea.cli.push.try_get_item_source_path",
            return_value=f"{self.author}/skills/echo",
        ), mock.patch("aea.cli.push.check_package_public_id"):
            self.invoke("push", "--local", "skill", f"{self.author}/echo")
        copy_tree_mock.assert_called_once()
        src_path, dst_path = copy_tree_mock.mock_calls[0][1]
        # check for correct author, type, name
        assert (
            os.path.normpath(src_path).split(os.sep)[-3:]
            == os.path.normpath(dst_path).split(os.sep)[-3:]
        )

    def test_fail_no_item(
        self,
        *mocks,
    ):
        """Test fail, item_not_exists ."""
        expected_path_pattern = ".*" + ".*".join(
            ["vendor", "fetchai", "skills", "not_exists"]
        )
        with pytest.raises(
            ClickException,
            match=rf'Item "fetchai/not_exists" not found in source folder "{expected_path_pattern}"\.',
        ):
            self.invoke("push", "--local", "skill", "fetchai/not_exists")


@mock.patch(
    "aea.cli.registry.push.load_yaml",
    return_value={"author": AUTHOR, "name": "name", "version": "0.1.0"},
)
class CheckPackagePublicIdTestCase(TestCase):
    """Test case for _check_package_public_id method."""

    def test__check_package_public_id_positive(self, *mocks):
        """Test for _check_package_public_id positive result."""
        check_package_public_id(
            "source-path",
            "item-type",
            PublicId.from_str(f"{AUTHOR}/name:0.1.0"),
        )

    def test__check_package_public_id_negative(self, *mocks):
        """Test for _check_package_public_id negative result."""
        with self.assertRaises(ClickException):
            check_package_public_id(
                "source-path",
                "item-type",
                PublicId.from_str(f"{AUTHOR}/name:0.1.1"),
            )


class TestPushLocalFailsArgumentNotPublicId:
    """Test the case when we try a local push with a non public id."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.runner = CliRunner()
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "push", "--local", "connection", "oef"],
            standalone_mode=False,
        )

    def test_exit_code_1(self):
        """Test the exit code is 1 (SystemExit)."""
        assert self.result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""


@mock.patch("aea.cli.utils.config.try_to_load_agent_config")
@mock.patch("aea.cli.push._save_item_locally")
@mock.patch("aea.cli.push.push_item")
@mock.patch("aea.cli.utils.decorators._check_aea_project")
class PushCommandTestCase(TestCase):
    """Test case for CLI push command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_push_connection_positive(self, *mocks):
        """Test for CLI push connection positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "push", "connection", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "push", "--local", "connection", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

    def test_push_protocol_positive(self, *mocks):
        """Test for CLI push protocol positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "push", "protocol", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "push", "--local", "protocol", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

    def test_push_skill_positive(self, *mocks):
        """Test for CLI push skill positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "push", "skill", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "push", "--local", "skill", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
class PushContractCommandTestCase(TestCase):
    """Test that the command 'aea push contract' works as expected."""

    def setUp(self):
        """Set the test up."""
        self.runner = CliRunner()

    @mock.patch("aea.cli.push._save_item_locally")
    def test_push_contract_positive(self, *mocks):
        """Test push contract command positive result."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "--skip-consistency-check",
                "push",
                "--local",
                "contract",
                "author/name:0.1.0",
            ],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("aea.cli.push.push_item")
    @mock.patch("aea.cli.push.get_default_remote_registry", return_value=REMOTE_HTTP)
    def test_push_contract_registry_positive(self, *mocks):
        """Test push contract to registry command positive result."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "--skip-consistency-check",
                "push",
                "--remote",
                "contract",
                "author/name:0.1.0",
            ],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


class TestPushLocallyWithLatest(AEATestCaseEmpty):
    """Test push locally with 'latest' as version."""

    @pytest.mark.parametrize("component_type", ITEM_TYPES)
    def test_command(self, component_type):
        """Run the test."""
        item_name = f"my_{component_type}"
        version = ":latest"
        self.scaffold_item(component_type, item_name)
        self.run_cli_command(
            "push",
            "--local",
            component_type,
            f"{self.author}/{item_name}{version}",
            cwd=self._get_cwd(),
        )

        component_type_plural = component_type + "s"
        path_to_pushed_package = (
            self.packages_dir_path / DEFAULT_AUTHOR / component_type_plural / item_name
        )
        path_to_current_package = (
            self.t / self.agent_name / component_type_plural / item_name
        )
        assert path_to_pushed_package.exists()
        comparison = filecmp.dircmp(path_to_pushed_package, path_to_current_package)
        assert comparison.diff_files == []


@mock.patch("aea.cli.utils.config.try_to_load_agent_config")
@mock.patch("aea.cli.utils.decorators._check_aea_project")
@mock.patch("os.path.exists")
class TestPushVersionsMismatch(TestCase):
    """Test that the command 'aea push contract' works as expected."""

    def setUp(self):
        """Set the test up."""
        self.runner = CliRunner()

    def test_push_local_version_check_failed(self, *mocks):
        """Test push contract command positive result."""
        with mock.patch(
            "aea.cli.registry.push.load_component_public_id",
            return_value=PublicId("author", "name", "1000.0.0"),
        ):
            with pytest.raises(
                ClickException, match="Version, name or author does not match."
            ):
                self.runner.invoke(
                    cli,
                    [
                        *CLI_LOG_OPTION,
                        "push",
                        "--local",
                        "contract",
                        "author/name:0.1.0",
                    ],
                    standalone_mode=False,
                    catch_exceptions=False,
                )

    def test_push_remote_version_check_failed(self, *mocks):
        """Test push contract command positive result."""
        with mock.patch(
            "aea.cli.registry.push.load_component_public_id",
            return_value=PublicId("author", "name", "1000.0.0"),
        ):
            with pytest.raises(
                ClickException, match="Version, name or author does not match."
            ):
                self.runner.invoke(
                    cli,
                    [*CLI_LOG_OPTION, "push", "contract", "author/name:0.1.0"],
                    standalone_mode=False,
                    catch_exceptions=False,
                )
