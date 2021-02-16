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


"""This test module contains the tests for the `aea add skill` sub-command."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import click
import pytest
import yaml
from jsonschema import ValidationError

import aea
from aea.cli import cli
from aea.configurations.base import (
    AgentConfig,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PublicId,
)
from aea.test_tools.test_cases import AEATestCaseEmpty, AEATestCaseEmptyFlaky

from packages.fetchai.skills.echo import PUBLIC_ID as ECHO_PUBLIC_ID
from packages.fetchai.skills.erc1155_client import PUBLIC_ID as ERC1155_CLIENT_PUBLIC_ID
from packages.fetchai.skills.error import PUBLIC_ID as ERROR_PUBLIC_ID

from tests.conftest import (
    AUTHOR,
    CLI_LOG_OPTION,
    CUR_PATH,
    CliRunner,
    MAX_FLAKY_RERUNS,
    ROOT_DIR,
    double_escape_windows_path_separator,
)


class TestAddSkillFailsWhenSkillAlreadyExists:
    """Test that the command 'aea add skill' fails when the skill already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_id = ERROR_PUBLIC_ID
        cls.skill_name = cls.skill_id.name
        cls.skill_author = cls.skill_id.author
        cls.skill_version = cls.skill_id.version

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        # this also by default adds the stub connection
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", str(cls.skill_id)],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # add the error skill again
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", str(cls.skill_id)],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_skill_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A skill with id '{skill_id}' already exists. Aborting...'
        """
        s = f"A skill with id '{self.skill_id}' already exists. Aborting..."
        assert self.result.exception.message == s

    @mock.patch("aea.cli.add.get_package_path", return_value="dest/path")
    @mock.patch("aea.cli.add.fetch_package")
    def test_add_skill_from_registry_positive(self, fetch_package_mock, *mocks):
        """Test add from registry positive result."""
        fetch_package_mock.return_value = Path(
            "vendor/{}/skills/{}".format(self.skill_author, self.skill_name)
        )
        public_id = "{}/{}:{}".format(AUTHOR, self.skill_name, self.skill_version)
        obj_type = "skill"
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "add", obj_type, public_id], standalone_mode=False,
        )
        assert result.exit_code == 0
        public_id_obj = PublicId.from_str(public_id)
        fetch_package_mock.assert_called_once_with(
            obj_type, public_id=public_id_obj, cwd=".", dest="dest/path"
        )

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillFailsWhenSkillWithSameAuthorAndNameButDifferentVersion:
    """Test that the command 'aea add skill' fails when the skill already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_id = ECHO_PUBLIC_ID
        cls.skill_name = cls.skill_id.name
        cls.skill_author = cls.skill_id.author
        cls.skill_version = cls.skill_id.version

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        # this also by default adds the stub connection
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", str(cls.skill_id)],
            standalone_mode=False,
        )
        assert cls.result.exit_code == 0

        # add skill again, but with different version number
        # first, change version number to package
        different_version = "0.1.1"
        different_id = cls.skill_author + "/" + cls.skill_name + ":" + different_version
        config_path = Path(
            cls.t,
            "packages",
            cls.skill_author,
            "skills",
            cls.skill_name,
            DEFAULT_SKILL_CONFIG_FILE,
        )
        config = yaml.safe_load(config_path.open())
        config["version"] = different_version
        yaml.safe_dump(config, config_path.open(mode="w"))
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", different_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_skill_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A skill with id '{skill_id}' already exists. Aborting...'
        """
        s = f"A skill with id '{self.skill_id}' already exists. Aborting..."
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillFailsWhenSkillNotInRegistry:
    """Test that the command 'aea add skill' fails when the skill is not in the registry."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_id = "author/unknown_skill:0.1.0"
        cls.skill_name = "unknown_skill"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", cls.skill_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_skill_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find skill: '{skill_name}''
        """
        s = "Cannot find skill: '{}'.".format(self.skill_id)
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillFailsWhenDifferentPublicId:
    """Test that the command 'aea add skill' fails when the skill has not the same public id."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_id = "different_author/error:0.1.0"
        cls.skill_name = "unknown_skill"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", cls.skill_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_skill_wrong_public_id(self):
        """Test that the log error message is fixed."""
        s = "Cannot find skill: '{}'.".format(self.skill_id)
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillFailsWhenConfigFileIsNotCompliant:
    """Test that the command 'aea add skill' fails when the configuration file is not compliant with the schema."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_id = str(ECHO_PUBLIC_ID)
        cls.skill_name = "echo"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)

        # change default registry path
        config = AgentConfig.from_json(yaml.safe_load(open(DEFAULT_AEA_CONFIG_FILE)))
        config.registry_path = os.path.join(ROOT_DIR, "packages")
        yaml.safe_dump(dict(config.json), open(DEFAULT_AEA_CONFIG_FILE, "w"))

        # change the serialization of the AgentConfig class so to make the parsing to fail.
        cls.patch = mock.patch.object(
            aea.configurations.base.SkillConfig,
            "from_json",
            side_effect=ValidationError("test error message"),
        )
        cls.patch.start()

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", cls.skill_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_configuration_file_not_valid(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find skill: '{skill_name}''
        """
        s = "Skill configuration file not valid: test error message"
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillFailsWhenDirectoryAlreadyExists:
    """Test that the command 'aea add skill' fails when the destination directory already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_id = str(ECHO_PUBLIC_ID)
        cls.skill_name = "echo"

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)

        # change default registry path
        config = AgentConfig.from_json(yaml.safe_load(open(DEFAULT_AEA_CONFIG_FILE)))
        config.registry_path = os.path.join(ROOT_DIR, "packages")
        yaml.safe_dump(dict(config.json), open(DEFAULT_AEA_CONFIG_FILE, "w"))

        Path(
            cls.t, cls.agent_name, "vendor", "fetchai", "skills", cls.skill_name
        ).mkdir(parents=True, exist_ok=True)
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", cls.skill_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_file_exists_error(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find skill: '{skill_name}''
        """
        missing_path = os.path.join("vendor", "fetchai", "skills", self.skill_name)
        missing_path = double_escape_windows_path_separator(missing_path)
        assert missing_path in self.result.exception.message

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillWithContractsDeps(AEATestCaseEmpty):
    """Test add skill with contract dependencies."""

    def test_add_skill_with_contracts_positive(self):
        """Test add skill with contract dependencies positive result."""
        self.add_item("skill", str(ERC1155_CLIENT_PUBLIC_ID))

        contracts_path = os.path.join(self.agent_name, "vendor", "fetchai", "contracts")
        contracts_folders = os.listdir(contracts_path)
        contract_dependency_name = "erc1155"
        assert contract_dependency_name in contracts_folders


class TestAddSkillFromRemoteRegistry(AEATestCaseEmptyFlaky):
    """Test case for add skill from Registry command."""

    IS_LOCAL = False
    IS_EMPTY = True

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_add_skill_from_remote_registry_positive(self):
        """Test add skill from Registry positive result."""
        self.add_item("skill", str(ECHO_PUBLIC_ID.to_latest()), local=self.IS_LOCAL)

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "skills")
        items_folders = os.listdir(items_path)
        item_name = "echo"
        assert item_name in items_folders


class TestAddSkillWithLatestVersion(AEATestCaseEmpty):
    """Test case for add skill with latest version."""

    def test_add_skill_latest_version(self):
        """Test add skill with latest version."""
        self.add_item("skill", str(ECHO_PUBLIC_ID.to_latest()), local=True)

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "skills")
        items_folders = os.listdir(items_path)
        item_name = "echo"
        assert item_name in items_folders


class TestAddSkillMixedModeFallsBack(AEATestCaseEmpty):
    """Test add skill in mixed mode that fails with local falls back to remote registry."""

    IS_EMPTY = True

    @mock.patch(
        "aea.cli.add.find_item_locally_or_distributed",
        side_effect=click.ClickException(""),
    )
    def test_add_skill_remote_mode_negative_local_positive_remote(self, *_mocks):
        """Test add skill mixed mode."""
        self.run_cli_command(
            "add", "skill", str(ECHO_PUBLIC_ID.to_latest()), cwd=self._get_cwd()
        )

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "skills")
        items_folders = os.listdir(items_path)
        item_name = "echo"
        assert item_name in items_folders


class TestAddSkillRemoteMode(AEATestCaseEmpty):
    """Test case for add skill, --remote mode."""

    IS_EMPTY = True

    def test_add_skill_remote_mode(self):
        """Test add skill mixed mode."""
        self.run_cli_command(
            "add",
            "--remote",
            "skill",
            str(ECHO_PUBLIC_ID.to_latest()),
            cwd=self._get_cwd(),
        )

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "skills")
        items_folders = os.listdir(items_path)
        item_name = "echo"
        assert item_name in items_folders
