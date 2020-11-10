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
"""This test module contains the tests for commands in aea.cli.eject module."""

import os
import shutil
from pathlib import Path

import click
import pytest

from aea.cli.utils.constants import CLI_CONFIG_PATH
from aea.configurations.base import ComponentType, DEFAULT_VERSION, PublicId
from aea.configurations.loader import load_component_configuration
from aea.test_tools.test_cases import AEATestCaseEmpty, AEATestCaseMany

from packages.fetchai.connections.gym.connection import (
    PUBLIC_ID as GYM_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.contracts.erc1155.contract import PUBLIC_ID as ERC1155_PUBLIC_ID
from packages.fetchai.protocols.default import DefaultMessage
from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.error import PUBLIC_ID as ERROR_PUBLIC_ID
from packages.fetchai.skills.gym import PUBLIC_ID as GYM_SKILL_PUBLIC_ID


class TestEjectCommands(AEATestCaseMany):
    """End-to-end test case for CLI eject commands."""

    def test_eject_commands_positive(self):
        """Test eject commands for positive result."""
        agent_name = "test_aea"
        self.create_agents(agent_name)

        self.set_agent_context(agent_name)
        cwd = os.path.join(self.t, agent_name)
        self.add_item("connection", str(GYM_CONNECTION_PUBLIC_ID))
        self.add_item("skill", str(GYM_SKILL_PUBLIC_ID))
        self.add_item("contract", str(ERC1155_PUBLIC_ID))

        self.eject_item("connection", str(GYM_CONNECTION_PUBLIC_ID))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "connections"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "connections")))

        self.eject_item("protocol", str(GymMessage.protocol_id))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "protocols"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "protocols")))

        self.eject_item("skill", str(GYM_SKILL_PUBLIC_ID))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "skills"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "skills")))

        self.eject_item("contract", str(ERC1155_PUBLIC_ID))
        assert "erc1155" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "contracts"))
        )
        assert "erc1155" in os.listdir((os.path.join(cwd, "contracts")))


class BaseTestEjectCommand(AEATestCaseEmpty):
    """Replace CLI author with a known author."""

    EXPECTED_AUTHOR = "some_author_name"

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()
        # copy file temporarily - it will be restored in the teardown
        cls.aea_cli_config = Path(CLI_CONFIG_PATH).expanduser()
        shutil.copy(cls.aea_cli_config, Path(cls.t, cls.aea_cli_config.name))
        os.remove(cls.aea_cli_config)

    @classmethod
    def teardown_class(cls):
        """Tear down the class."""
        shutil.copy(Path(cls.t, cls.aea_cli_config.name), cls.aea_cli_config)
        super().teardown_class()


class TestEjectCommandCliConfigNotAvailable(BaseTestEjectCommand):
    """Test that 'aea eject' cannot be run if CLI configuration not provided."""

    IS_EMPTY = True

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()
        # we don't set the CLI configuration
        cls.add_item("protocol", str(DefaultMessage.protocol_id))

    def test_error(self):
        """Test that without CLI configuration, 'aea eject' won't work."""
        with pytest.raises(
            click.ClickException,
            match="The AEA configurations are not initialized. Use `aea init` before continuing.",
        ):
            self.invoke(
                "eject", "protocol", str(DefaultMessage.protocol_id),
            )


class TestEjectCommandReplacesReferences(BaseTestEjectCommand):
    """Test that eject command replaces the right references to the new package."""

    IS_EMPTY = True

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()
        cls.run_cli_command(
            "init", "--local", "--reset", "--author", cls.EXPECTED_AUTHOR, cwd=cls.t
        )
        cls.add_item("protocol", str(DefaultMessage.protocol_id))
        cls.eject_item("protocol", str(DefaultMessage.protocol_id))

    def test_username_is_correct(self):
        """Test that the author name in the ejected component configuration is updated correctly."""
        package_path = Path(
            self.current_agent_context, "protocols", DefaultMessage.protocol_id.name
        )
        assert (
            package_path.exists()
        ), f"Expected ejected package in '{package_path}', but not found."
        component_configuration = load_component_configuration(
            ComponentType.PROTOCOL, package_path
        )
        assert component_configuration.author == self.EXPECTED_AUTHOR

    def test_aea_config_references_updated_correctly(self):
        """Test that the references in the AEA configuration is updated correctly."""
        agent_config = self.load_agent_config(self.agent_name)
        assert agent_config.protocols == {
            PublicId(
                self.EXPECTED_AUTHOR, DefaultMessage.protocol_id.name, DEFAULT_VERSION
            )
        }


class TestEjectCommandReplacesCustomConfigurationReference(BaseTestEjectCommand):
    """Test that eject command replaces references in AEA configuration."""

    IS_EMPTY = True

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()
        cls.run_cli_command(
            "init", "--local", "--reset", "--author", cls.EXPECTED_AUTHOR, cwd=cls.t
        )
        cls.add_item("skill", str(ERROR_PUBLIC_ID))
        # add a custom configuration to the error skill
        cls.run_cli_command(
            "--skip-consistency-check",
            "config",
            "set",
            "vendor.fetchai.skills.error.is_abstract",
            "--type",
            "bool",
            "true",
            cwd=cls._get_cwd(),
        )

        cls.eject_item("skill", str(ERROR_PUBLIC_ID))

    def test_username_is_correct(self):
        """Test that the author name in the ejected component configuration is updated correctly."""
        package_path = Path(self.current_agent_context, "skills", ERROR_PUBLIC_ID.name)
        assert (
            package_path.exists()
        ), f"Expected ejected package in '{package_path}', but not found."
        component_configuration = load_component_configuration(
            ComponentType.SKILL, package_path
        )
        assert component_configuration.author == self.EXPECTED_AUTHOR

    def test_aea_config_references_updated_correctly(self):
        """Test that the references in the AEA configuration is updated correctly."""
        agent_config = self.load_agent_config(self.agent_name)
        assert agent_config.skills == {
            PublicId(self.EXPECTED_AUTHOR, ERROR_PUBLIC_ID.name, DEFAULT_VERSION)
        }
