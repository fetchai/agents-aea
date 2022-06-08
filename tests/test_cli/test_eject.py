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
"""This test module contains the tests for commands in aea.cli.eject module."""

import os
from pathlib import Path
from unittest import mock

import click
import pytest

from aea.cli.utils.config import get_or_create_cli_config
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

        # the order must be kept as is, because of recursive ejects
        self.eject_item("skill", str(GYM_SKILL_PUBLIC_ID))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "skills"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "skills")))
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

        self.eject_item("contract", str(ERC1155_PUBLIC_ID))
        assert "erc1155" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "contracts"))
        )
        assert "erc1155" in os.listdir((os.path.join(cwd, "contracts")))


class TestRecursiveEject(AEATestCaseEmpty):
    """Test that eject is recursive."""

    def test_recursive_eject_commands_positive(self):
        """Test eject commands for positive result."""
        agent_name = "test_aea"
        self.create_agents(agent_name)

        self.set_agent_context(agent_name)
        cwd = os.path.join(self.t, agent_name)
        self.add_item("connection", str(GYM_CONNECTION_PUBLIC_ID))
        self.add_item("skill", str(GYM_SKILL_PUBLIC_ID))
        self.add_item("contract", str(ERC1155_PUBLIC_ID))

        # ejecting the gym protocol will cause the ejection of
        # all the other packages that depend on it,
        # that is, gym connection and gym skill.
        self.eject_item("protocol", str(GymMessage.protocol_id))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "protocols"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "protocols")))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "connections"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "connections")))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "skills"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "skills")))


class TestRecursiveEjectIsAborted(AEATestCaseEmpty):
    """Test that recursive eject is aborted in non-quiet mode."""

    @mock.patch("click.confirm", return_value=False)
    def test_recursive_eject_commands_non_quiet_negative(self, *_mocks):
        """Test eject command for negative result in interactive mode."""
        agent_name = "test_aea"
        self.create_agents(agent_name)

        self.set_agent_context(agent_name)
        cwd = os.path.join(self.t, agent_name)
        self.add_item("connection", str(GYM_CONNECTION_PUBLIC_ID))
        self.add_item("skill", str(GYM_SKILL_PUBLIC_ID))
        self.add_item("contract", str(ERC1155_PUBLIC_ID))

        self.run_cli_command(
            "eject", "protocol", str(GymMessage.protocol_id), cwd=self._get_cwd()
        )
        # assert packages not ejected
        assert "gym" in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "protocols"))
        )
        assert "gym" not in os.listdir((os.path.join(cwd, "protocols")))
        assert "gym" in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "connections"))
        )
        assert "gym" not in os.listdir((os.path.join(cwd, "connections")))
        assert "gym" in os.listdir((os.path.join(cwd, "vendor", "fetchai", "skills")))
        assert "gym" not in os.listdir((os.path.join(cwd, "skills")))


class BaseTestEjectCommand(AEATestCaseEmpty):
    """Replace CLI author with a known author."""

    EXPECTED_AUTHOR = ""

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()
        config = get_or_create_cli_config()
        cls.EXPECTED_AUTHOR = config.get("author", "")


class TestEjectCommandCliConfigNotAvailable(AEATestCaseEmpty):
    """Test that 'aea eject' cannot be run if CLI configuration not provided."""

    IS_EMPTY = True

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()
        cls.add_item("protocol", str(DefaultMessage.protocol_id))

    @mock.patch("aea.cli.utils.config.get_or_create_cli_config", return_value={})
    def test_error(self, *_mocks):
        """Test that without CLI configuration, 'aea eject' won't work."""
        with pytest.raises(
            click.ClickException,
            match="The AEA configurations are not initialized. Use `aea init` before continuing.",
        ):
            self.invoke(
                "eject",
                "--quiet",
                "protocol",
                str(DefaultMessage.protocol_id),
            )


class TestEjectCommandReplacesReferences(BaseTestEjectCommand):
    """Test that eject command replaces the right references to the new package."""

    IS_EMPTY = True

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()
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
        assert component_configuration.name == DefaultMessage.protocol_id.name
        assert component_configuration.version == DEFAULT_VERSION

    def test_aea_config_references_updated_correctly(self):
        """Test that the references in the AEA configuration is updated correctly."""
        agent_config = self.load_agent_config(self.agent_name)
        assert {p.without_hash() for p in agent_config.protocols} == {
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
        assert {p.without_hash() for p in agent_config.skills} == {
            PublicId(self.EXPECTED_AUTHOR, ERROR_PUBLIC_ID.name, DEFAULT_VERSION)
        }


class TestEjectWithLatest(AEATestCaseEmpty):
    """Test the eject command when a public id 'latest' is provided."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        super(TestEjectWithLatest, cls).setup_class()
        cls.add_item("skill", str(ERROR_PUBLIC_ID.to_latest()))

    def test_command(self):
        """Run the test."""
        latest_public_id = ERROR_PUBLIC_ID.to_latest()
        self.eject_item("skill", str(latest_public_id))
        cwd = os.path.join(self.t, self.agent_name)
        # assert packages ejected
        assert "error" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "skills"))
        )
        assert "error" in os.listdir((os.path.join(cwd, "skills")))


class TestEjectWithSymlink(AEATestCaseEmpty):
    """Test the eject command with symlinks flag."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        super(TestEjectWithSymlink, cls).setup_class()
        cls.add_item("skill", str(ERROR_PUBLIC_ID.to_latest()))

    def test_command(self):
        """Run the test."""
        latest_public_id = ERROR_PUBLIC_ID.to_latest()
        self.run_cli_command(
            "eject",
            "--with-symlinks",
            "skill",
            str(latest_public_id),
            cwd=self._get_cwd(),
        )
        cwd = os.path.join(self.t, self.agent_name)
        # assert packages ejected
        assert "error" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "skills"))
        )
        assert "error" in os.listdir((os.path.join(cwd, "skills")))
        assert "error" in os.listdir(
            (os.path.join(cwd, "vendor", self.author, "skills"))
        )
