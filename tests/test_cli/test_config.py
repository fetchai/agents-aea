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
"""This test module contains the tests for the `aea config` sub-command."""
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from click.exceptions import ClickException

from aea.aea_builder import AEABuilder
from aea.cli import cli
from aea.cli.config import AgentConfigManager
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE, PackageType
from aea.configurations.loader import ConfigLoader
from aea.configurations.manager import ALLOWED_PATH_ROOTS
from aea.helpers.yaml_utils import yaml_load

from tests.conftest import CLI_LOG_OPTION, CUR_PATH, CliRunner, ROOT_DIR


class TestConfigGet:
    """Test that the command 'aea config get' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
        shutil.copytree(Path(CUR_PATH, "data", "dummy_aea"), Path(cls.t, "dummy_aea"))
        os.chdir(Path(cls.t, "dummy_aea"))
        cls.runner = CliRunner()

    def test_get_agent_name(self):
        """Test getting the agent name."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", "agent.agent_name"],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert result.output == "Agent0\n"

    def test_get_agent_default_routing(self):
        """Test getting the agent name."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", "agent.default_routing"],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert result.output == "{}\n"

    def test_get_skill_name(self):
        """Test getting the 'dummy' skill name."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", "skills.dummy.name"],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        assert result.output == "dummy\n"

    def test_get_nested_attribute(self):
        """Test getting the 'dummy' skill name."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "get",
                "skills.dummy.behaviours.dummy.class_name",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        assert result.output == "DummyBehaviour\n"

    def test_no_recognized_root(self):
        """Test that the 'get' fails because the root is not recognized."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", "wrong_root.agent_name"],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "The root of the dotted path must be one of: {}".format(
                ALLOWED_PATH_ROOTS
            )
        )

    def test_too_short_path_but_root_correct(self):
        """Test that the 'get' fails because the path is too short but the root is correct."""
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "config", "get", "agent"], standalone_mode=False
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "The path is too short. Please specify a path up to an attribute name."
        )

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", "skills.dummy"],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "The path is too short. Please specify a path up to an attribute name."
        )

    def test_resource_not_existing(self):
        """Test that the 'get' fails because the resource does not exist."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "get",
                "connections.non_existing_connection.name",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "Resource connections/non_existing_connection does not exist."
        )

    def test_attribute_not_found(self):
        """Test that the 'get' fails because the attribute is not found."""
        with pytest.raises(
            ClickException, match=r"Attribute `.* for .* config does not exist"
        ):
            self.runner.invoke(
                cli,
                [
                    *CLI_LOG_OPTION,
                    "config",
                    "get",
                    "skills.dummy.non_existing_attribute",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_get_whole_dict(self):
        """Test that getting the 'dummy' skill behaviours works."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", "skills.dummy.behaviours"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        actual_object = json.loads(result.output)
        expected_object = {
            "dummy": {
                "args": {"behaviour_arg_1": 1, "behaviour_arg_2": "2"},
                "class_name": "DummyBehaviour",
            },
            "dummy_behaviour_same_classname": {
                "args": {"behaviour_arg_1": 1, "behaviour_arg_2": "2"},
                "class_name": "DummyBehaviour",
                "file_path": "dummy_subpackage/foo.py",
            },
        }
        assert actual_object == expected_object

    # def test_get_list(self):  # noqa: E800
    #     """Test that getting the 'dummy' skill behaviours works."""  # noqa: E800
    #     result = self.runner.invoke(  # noqa: E800
    #         cli,  # noqa: E800
    #         [  # noqa: E800
    #             *CLI_LOG_OPTION,  # noqa: E800
    #             "config",  # noqa: E800
    #             "get",  # noqa: E800
    #             "vendor.fetchai.connections.p2p_libp2p.config.entry_peers",  # noqa: E800
    #         ],  # noqa: E800
    #         standalone_mode=False,  # noqa: E800
    #     )  # noqa: E800
    #     assert result.exit_code == 0  # noqa: E800
    #     assert result.output == "[]\n"  # noqa: E800

    def test_get_fails_when_getting_nested_object(self):
        """Test that getting a nested object in 'dummy' skill fails because path is not valid."""
        with pytest.raises(
            ClickException, match=r"Attribute `.* for .* config does not exist"
        ):
            self.runner.invoke(
                cli,
                [
                    *CLI_LOG_OPTION,
                    "config",
                    "get",
                    "skills.dummy.non_existing_attribute.dummy",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_get_fails_when_getting_non_dict_attribute(self):
        """Test that the get fails because the path point to a non-dict object."""
        attribute = "protocols"
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", f"skills.dummy.{attribute}.protocol"],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        s = f"Attribute '{attribute}' is not a dictionary."
        assert result.exception.message == s

    def test_get_fails_when_getting_non_dict_attribute_in_between(self):
        """Test that the get fails because an object in between is not a dictionary."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", "agent.skills.some_attribute"],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        s = "Attribute 'skills' is not a dictionary."
        assert result.exception.message == s

    def test_get_fails_when_getting_vendor_dependency_with_wrong_component_type(self):
        """Test that getting a vendor component with wrong component type raises error."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "get",
                "vendor.fetchai.component_type_not_correct.error.non_existing_attribute",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        s = "'component_type_not_correct' is not a valid component type. Please use one of ['protocols', 'connections', 'skills', 'contracts']."
        assert result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestConfigSet:
    """Test that the command 'aea config set' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
        shutil.copytree(Path(CUR_PATH, "data", "dummy_aea"), Path(cls.t, "dummy_aea"))
        os.chdir(Path(cls.t, "dummy_aea"))
        cls.runner = CliRunner()

    def test_set_agent_logging_options(self):
        """Test setting the agent name."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.logging_config.disable_existing_loggers",
                "True",
                "--type=bool",
            ],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "get",
                "agent.logging_config.disable_existing_loggers",
            ],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert result.output == "True\n"

    def test_set_agent_incorrect_value(self):
        """Test setting the agent name."""
        with pytest.raises(
            ClickException,
            match="Attribute `not_agent_name` is not allowed to be updated!",
        ):
            self.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, "config", "set", "agent.not_agent_name", "new_name"],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_set_type_bool(self):
        """Test setting the agent name."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.logging_config.disable_existing_loggers",
                "true",
                "--type=bool",
            ],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0

    def test_set_type_none(self):
        """Test setting the agent name."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.logging_config.some_value",
                "",
                "--type=none",
            ],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0

    def test_set_type_dict(self):
        """Test setting the default routing."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.default_routing",
                '{"fetchai/contract_api:any": "fetchai/ledger:any"}',
                "--type=dict",
            ],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0

    # def test_set_type_list(self):  # noqa: E800
    #     """Test setting the default routing."""  # noqa: E800
    #     result = self.runner.invoke(  # noqa: E800
    #         cli,  # noqa: E800
    #         [  # noqa: E800
    #             *CLI_LOG_OPTION,  # noqa: E800
    #             "config",  # noqa: E800
    #             "set",  # noqa: E800
    #             "vendor.fetchai.connections.p2p_libp2p.config.entry_peers",  # noqa: E800
    #             '["peer1", "peer2"]',  # noqa: E800
    #             "--type=list",  # noqa: E800
    #         ],  # noqa: E800
    #         standalone_mode=False,  # noqa: E800
    #         catch_exceptions=False,  # noqa: E800
    #     )  # noqa: E800
    #     assert result.exit_code == 0  # noqa: E800

    def test_set_invalid_value(self):
        """Test setting the agent name."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.agent_name",
                "true",
                "--type=bool",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 1

    def test_set_skill_name_should_fail(self):
        """Test setting the 'dummy' skill name."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "set", "skills.dummy.name", "new_dummy_name"],
            standalone_mode=False,
        )
        assert result.exit_code == 1

    def test_set_nested_attribute(self):
        """Test setting a nested attribute."""
        path = "skills.dummy.behaviours.dummy.args.behaviour_arg_1"
        new_value = "10"  # cause old value is int
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "set", path, new_value],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", path],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert new_value in result.output

    def test_set_nested_attribute_not_allowed(self):
        """Test setting a nested attribute."""
        path = "skills.dummy.behaviours.dummy.config.behaviour_arg_1"
        new_value = "new_dummy_name"
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "set", path, new_value],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "Attribute `behaviours.dummy.config.behaviour_arg_1` is not allowed to be updated!"
        )

    def test_no_recognized_root(self):
        """Test that the 'get' fails because the root is not recognized."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "set", "wrong_root.agent_name", "value"],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "The root of the dotted path must be one of: {}".format(
                ALLOWED_PATH_ROOTS
            )
        )

    def test_too_short_path_but_root_correct(self):
        """Test that the 'get' fails because the path is too short but the root is correct."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "set", "agent", "data"],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "The path is too short. Please specify a path up to an attribute name."
        )

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "set", "skills.dummy", "value"],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "The path is too short. Please specify a path up to an attribute name."
        )

    def test_resource_not_existing(self):
        """Test that the 'get' fails because the resource does not exist."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "connections.non_existing_connection.name",
                "value",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert (
            result.exception.message
            == "Resource connections/non_existing_connection does not exist."
        )

    def test_attribute_not_found(self):
        """Test that the 'set' fails because the attribute is not found."""
        with pytest.raises(
            ClickException,
            match="Attribute `non_existing_attribute` is not allowed to be updated!",
        ):
            self.runner.invoke(
                cli,
                [
                    *CLI_LOG_OPTION,
                    "config",
                    "set",
                    "skills.dummy.non_existing_attribute",
                    "value",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_set_fails_when_setting_non_primitive_type(self):
        """Test that setting the 'dummy' skill behaviours fails because not a primitive type."""
        with pytest.raises(
            ClickException, match="Attribute `behaviours` is not allowed to be updated!"
        ):
            self.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, "config", "set", "skills.dummy.behaviours", "value"],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_get_fails_when_setting_nested_object(self):
        """Test that setting a nested object in 'dummy' skill fails because path is not valid."""
        with pytest.raises(
            ClickException,
            match=r"Attribute `non_existing_attribute.dummy` is not allowed to be updated!",
        ):
            self.runner.invoke(
                cli,
                [
                    *CLI_LOG_OPTION,
                    "config",
                    "set",
                    "skills.dummy.non_existing_attribute.dummy",
                    "new_value",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_get_fails_when_setting_non_dict_attribute(self):
        """Test that the set fails because the path point to a non-dict object."""
        behaviour_arg_1 = "behaviour_arg_1"
        path = f"skills.dummy.behaviours.dummy.args.{behaviour_arg_1}.over_the_string"
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "set", path, "new_value"],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        s = f"Attribute '{behaviour_arg_1}' is not a dictionary."
        assert result.exception.message == s

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestConfigNestedGetSet:
    """Test that the command 'aea config set' works as expected."""

    PATH = "skills.dummy.behaviours.dummy.args.behaviour_arg_1"
    INCORRECT_PATH = "skills.dummy.behaviours.dummy.args.behaviour_arg_100500"
    INITIAL_VALUE = 1
    NEW_VALUE = 100

    def setup(self):
        """Set the test up."""
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = self.t / dir_path
        src_dir = self.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
        shutil.copytree(Path(CUR_PATH, "data", "dummy_aea"), Path(self.t, "dummy_aea"))
        os.chdir(Path(self.t, "dummy_aea"))
        self.runner = CliRunner()

    def teardown(self):
        """Tear dowm the test."""
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except (OSError, IOError):
            pass

    def test_set_get_incorrect_path(self):
        """Fail on incorrect attribute tryed to be updated."""
        with pytest.raises(
            ClickException, match="Attribute `.*` for .* config does not exist"
        ):
            self.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, "config", "get", self.INCORRECT_PATH],
                standalone_mode=False,
                catch_exceptions=False,
            )

        with pytest.raises(
            ClickException,
            match="Attribute `behaviours.dummy.args.behaviour_arg_100500` is not allowed to be updated!",
        ):
            self.runner.invoke(
                cli,
                [
                    *CLI_LOG_OPTION,
                    "config",
                    "set",
                    self.INCORRECT_PATH,
                    str(self.NEW_VALUE),
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def load_agent_config(self) -> AgentConfig:
        """Load agent config for current dir."""
        agent_loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
        with open(DEFAULT_AEA_CONFIG_FILE, "r") as fp:
            agent_config = agent_loader.load(fp)
        return agent_config

    def get_component_config_value(self) -> dict:
        """Get component variable value."""
        package_type, package_name, *path = self.PATH.split(".")
        file_path = Path(f"{package_type}") / package_name / f"{package_type[:-1]}.yaml"

        with open(file_path, "r") as fp:
            data = yaml_load(fp)

        value = data
        for i in path:
            value = value[i]
        return value

    def test_set_get_correct_path(self):
        """Test component value updated in agent config not in component config."""
        agent_config = self.load_agent_config()
        config_value = self.get_component_config_value()
        assert config_value == self.INITIAL_VALUE

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", self.PATH],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert str(self.INITIAL_VALUE) in result.output

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "set", self.PATH, str(self.NEW_VALUE)],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        config_value = self.get_component_config_value()
        assert config_value == self.INITIAL_VALUE

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "config", "get", self.PATH],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert str(self.NEW_VALUE) in result.output

        agent_config = self.load_agent_config()
        assert agent_config.component_configurations


def test_AgentConfigManager_get_overridables():
    """Test agent config manager get_overridables."""
    path = Path(CUR_PATH, "data", "dummy_aea")
    agent_config = AEABuilder.try_to_load_agent_configuration_file(path)
    config_manager = AgentConfigManager(agent_config, path)
    agent_overridables, component_overridables = config_manager.get_overridables()
    assert "description" in agent_overridables
    assert "is_abstract" in list(component_overridables.values())[0]
