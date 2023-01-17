# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
"""This test module contains tests for aea.cli.add generic methods."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import click
import pytest

from aea.cli.add import _add_item_deps
from aea.cli.core import cli
from aea.cli.registry.settings import REMOTE_IPFS
from aea.configurations.data_types import PackageType, PublicId
from aea.test_tools.click_testing import CliRunner
from aea.test_tools.test_cases import AEATestCaseEmpty, CLI_LOG_OPTION

from tests.conftest import AUTHOR, MAX_FLAKY_RERUNS, ROOT_DIR, TEST_IPFS_REGISTRY_CONFIG
from tests.test_cli.tools_for_testing import ContextMock


class AddItemDepsTestCase(TestCase):
    """Test case for _add_item_deps method."""

    @mock.patch("aea.cli.add.add_item")
    def test__add_item_deps_missing_skills_positive(self, add_item_mock):
        """Test _add_item_deps for positive result with missing skills."""
        ctx = ContextMock(skills=[])
        item_config = mock.Mock()
        item_config.protocols = []
        item_config.contracts = []
        item_config.connections = []
        item_config.skills = ["skill-1", "skill-2"]
        _add_item_deps(ctx, "skill", item_config)


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
class BaseTestAddRemoteMode(AEATestCaseEmpty):
    """Base test case for add component, --remote mode."""

    IS_EMPTY = True
    COMPONENT_ID = PublicId(
        "valory",
        "test_abci",
        "0.1.0",
        "bafybeigb5myrmvjbfcdcwodoxn7ijdinntza3fagwwjbiho7kjdcr5lbmm",
    )
    COMPONENT_TYPE = PackageType.SKILL

    @mock.patch(
        "aea.cli.registry.utils.get_or_create_cli_config",
        return_value=TEST_IPFS_REGISTRY_CONFIG,
    )
    @mock.patch("aea.cli.add.get_default_remote_registry", return_value=REMOTE_IPFS)
    def test_add_component_remote_mode(self, *_):
        """Test add skill mixed mode."""
        self.run_cli_command(
            "add",
            "--remote",
            str(self.COMPONENT_TYPE),
            str(self.COMPONENT_ID),
            cwd=self._get_cwd(),
        )

        items_path = os.path.join(
            self.agent_name,
            "vendor",
            self.COMPONENT_ID.author,
            self.COMPONENT_TYPE.to_plural(),
        )
        items_folders = os.listdir(items_path)
        item_name = self.COMPONENT_ID.name
        assert item_name in items_folders


class BaseTestAddConnectionLocalWhenNoLocalRegistryExists:
    """Test that the command 'aea add connection' fails in local mode when the local registry does not exists."""

    COMPONENT_ID: PublicId
    COMPONENT_TYPE: PackageType

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )
        assert result.exit_code == 0, result.stdout

        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "--registry-path",
                str(Path(ROOT_DIR) / "packages"),
                "create",
                cls.agent_name,
                "--local",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0, result.stdout

        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add",
                "--local",
                str(cls.COMPONENT_TYPE),
                str(cls.COMPONENT_ID),
            ],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1."""
        assert self.result.exit_code == 1, self.result.stdout

    def test_standard_output_mentions_failure(self):
        """Test standard output contains information on failure."""
        assert (
            "Registry path not provided and local registry `packages` not found in current (.) and parent directory."
            in self.result.exception.message
        )

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class BaseTestAddSkillMixedModeFallsBack(AEATestCaseEmpty):
    """Test add skill in mixed mode that fails with local falls back to remote registry."""

    IS_EMPTY = True
    COMPONENT_ID: PublicId
    COMPONENT_TYPE: PackageType

    @mock.patch(
        "aea.cli.add.find_item_locally_or_distributed",
        side_effect=click.ClickException(""),
    )
    @mock.patch(
        "aea.cli.add.load_item_config",
    )
    @mock.patch(
        "aea.cli.add.register_item",
    )
    @mock.patch(
        "aea.cli.add.is_fingerprint_correct",
    )
    @mock.patch(
        "aea.cli.add.PublicId.from_json",
    )
    def test_add_skill_remote_mode_negative_local_positive_remote(self, *_mocks):
        """Test add skill mixed mode."""
        with mock.patch(
            "aea.cli.add.fetch_item_remote",
        ) as mock_fetch_item_remote:
            self.run_cli_command(
                "add",
                str(self.COMPONENT_TYPE),
                "--mixed",
                str(self.COMPONENT_ID),
                cwd=self._get_cwd(),
            )

        mock_fetch_item_remote.assert_called_once()
