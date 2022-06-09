# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This test module contains the tests for the `aea remove skill` sub-command."""

import os
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import yaml

import aea
import aea.configurations.base
from aea.cli import cli
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE

from packages.fetchai.skills.gym import PUBLIC_ID as GYM_SKILL_PUBLIC_ID

from tests.conftest import AUTHOR, CLI_LOG_OPTION, CliRunner, ROOT_DIR


class TestRemoveSkillWithPublicId:
    """Test that the command 'aea remove skill' works correctly when using the public id."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
        cls.skill_id = str(GYM_SKILL_PUBLIC_ID)
        cls.skill_name = "gym"

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
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

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", cls.skill_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "remove", "skill", cls.skill_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_zero(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 0

    def test_directory_does_not_exist(self):
        """Test that the directory of the removed skill does not exist."""
        assert not Path("skills", self.skill_name).exists()

    def test_skill_not_present_in_agent_config(self):
        """Test that the name of the removed skill is not present in the agent configuration file."""
        agent_config = aea.configurations.base.AgentConfig.from_json(
            yaml.safe_load(open(DEFAULT_AEA_CONFIG_FILE))
        )
        assert self.skill_id not in agent_config.skills

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRemoveSkillFailsWhenSkillIsNotSupported:
    """Test that the command 'aea remove skill' fails when the skill is not supported."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
        cls.skill_id = str(GYM_SKILL_PUBLIC_ID)

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
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
            [*CLI_LOG_OPTION, "remove", "skill", cls.skill_id],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_skill_not_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'The skill '{skill_name}' is not supported.'
        """
        s = "The skill '{}' is not supported.".format(self.skill_id)
        assert self.result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRemoveSkillFailsWhenExceptionOccurs:
    """Test that the command 'aea remove skill' fails when an exception occurs while removing the directory."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
        cls.skill_id = str(GYM_SKILL_PUBLIC_ID)
        cls.skill_name = "gym"

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
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

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", cls.skill_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        cls.patch = unittest.mock.patch(
            "shutil.rmtree", side_effect=BaseException("an exception")
        )
        cls.patch.start()

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "remove", "skill", cls.skill_name],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.patch.stop()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
