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

"""This test module contains the tests for the `aea add connection` sub-command."""

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest
from click.exceptions import ClickException

from aea.cli import cli
from aea.cli.upgrade import ItemRemoveHelper
from aea.configurations.base import (
    AgentConfig,
    ComponentId,
    DEFAULT_AEA_CONFIG_FILE,
    PackageId,
    PackageType,
    PublicId,
)
from aea.configurations.loader import ConfigLoader
from aea.helpers.base import cd
from aea.test_tools.test_cases import BaseAEATestCase

from packages.fetchai.connections import oef
from packages.fetchai.connections.soef.connection import PUBLIC_ID as SOEF_PUBLIC_ID
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

from tests.conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH, CliRunner


class BaseTestCase:
    """Base test case class with setup and teardown and some utils."""

    ITEM_TYPE = "connection"
    ITEM_PUBLIC_ID = SOEF_PUBLIC_ID
    LOCAL: List[str] = ["--local"]
    DEPENDENCY_TYPE = "protocol"
    DEPENDENCY_PUBLIC_ID = OefSearchMessage.protocol_id

    @staticmethod
    def loader() -> ConfigLoader:
        """Return Agent config loader."""
        return ConfigLoader.from_configuration_type(PackageType.AGENT)

    def load_config(self) -> AgentConfig:
        """Load AgentConfig from current directory."""
        agent_loader = self.loader()
        path = Path(DEFAULT_AEA_CONFIG_FILE)
        with path.open(mode="r", encoding="utf-8") as fp:
            agent_config = agent_loader.load(fp)
        return agent_config

    def dump_config(self, agent_config: AgentConfig) -> None:
        """Dump AgentConfig to current directory."""
        agent_loader = self.loader()
        path = Path(DEFAULT_AEA_CONFIG_FILE)

        with path.open(mode="w", encoding="utf-8") as fp:
            agent_loader.dump(agent_config, fp)

    @classmethod
    def setup(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        # add connection first time

    @contextmanager
    def with_oef_installed(self):
        """Add and remove oef connection."""
        result = self.runner.invoke(
            cli,
            [
                "-v",
                "DEBUG",
                "add",
                "--local",
                "connection",
                str(oef.connection.PUBLIC_ID),
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        try:
            yield
        finally:
            result = self.runner.invoke(
                cli,
                ["-v", "DEBUG", "remove", "connection", str(oef.connection.PUBLIC_ID)],
                standalone_mode=False,
            )
            assert result.exit_code == 0

    @contextmanager
    def with_config_update(self):
        """Context manager to update item version to 0.0.1."""
        original_config = self.load_config()

        config_data = original_config.json
        if str(self.ITEM_PUBLIC_ID) in config_data[f"{self.ITEM_TYPE}s"]:
            config_data[f"{self.ITEM_TYPE}s"].remove(str(self.ITEM_PUBLIC_ID))
        config_data[f"{self.ITEM_TYPE}s"].append(
            f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:0.0.1"
        )
        self.dump_config(AgentConfig.from_json(config_data))
        try:
            yield
        finally:
            self.dump_config(original_config)

    @classmethod
    def teardown(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRemoveAndDependencies(BaseTestCase):
    """Test dependency remove helper and upgrade with dependency removed."""

    ITEM_TYPE = "connection"
    ITEM_PUBLIC_ID = SOEF_PUBLIC_ID
    LOCAL: List[str] = ["--local"]
    DEPENDENCY_TYPE = "protocol"
    DEPENDENCY_PUBLIC_ID = OefSearchMessage.protocol_id

    @classmethod
    def setup(cls):
        """Set the test up."""
        super(TestRemoveAndDependencies, cls).setup()
        cls.DEPENDENCY_PACKAGE_ID = PackageId(
            cls.DEPENDENCY_TYPE, cls.DEPENDENCY_PUBLIC_ID
        )
        result = cls.runner.invoke(
            cli,
            ["-v", "DEBUG", "add", "--local", cls.ITEM_TYPE, str(cls.ITEM_PUBLIC_ID)],
            standalone_mode=False,
        )
        assert result.exit_code == 0

    def test_upgrade_and_dependency_removed(self):
        """
        Test dependency removed after upgrade.

        Done with mocking _add_item_deps to avoid dependencies installation.

        Also checks dependency configuration removed with component
        """
        assert self.DEPENDENCY_PUBLIC_ID in self.load_config().protocols

        # add empty component config to aea-config.py
        agent_config = self.load_config()
        component_id = ComponentId(self.DEPENDENCY_TYPE, self.DEPENDENCY_PUBLIC_ID)
        agent_config.component_configurations[component_id] = {}  # just empty
        agent_config.component_configurations[
            ComponentId(self.ITEM_TYPE, self.ITEM_PUBLIC_ID)
        ] = {}  # just empty
        self.dump_config(agent_config)

        agent_config = self.load_config()
        assert component_id in agent_config.component_configurations

        with patch(
            "aea.cli.upgrade.ItemUpgrader.check_upgrade_is_required", return_value=True
        ), patch("aea.cli.add._add_item_deps"):
            result = self.runner.invoke(
                cli,
                [
                    "-v",
                    "DEBUG",
                    "upgrade",
                    *self.LOCAL,
                    self.ITEM_TYPE,
                    f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:latest",
                ],
                catch_exceptions=True,
            )
            try:
                assert result.exit_code == 0

                assert self.DEPENDENCY_PUBLIC_ID not in self.load_config().protocols
                agent_config = self.load_config()

                # check configuration was removed too
                assert component_id not in agent_config.component_configurations
                assert (
                    ComponentId(self.ITEM_TYPE, self.ITEM_PUBLIC_ID)
                    in agent_config.component_configurations
                )
            finally:
                # restore component removed
                result = self.runner.invoke(
                    cli,
                    [
                        "-v",
                        "DEBUG",
                        "add",
                        *self.LOCAL,
                        self.DEPENDENCY_TYPE,
                        f"{self.DEPENDENCY_PUBLIC_ID.author}/{self.DEPENDENCY_PUBLIC_ID.name}:latest",
                    ],
                    catch_exceptions=True,
                )
                assert self.DEPENDENCY_PUBLIC_ID in self.load_config().protocols

    def test_upgrade_and_dependency_not_removed_caused_required_by_another_item(self):
        """Test dependency is not removed after upgrade cause required by another item."""
        assert self.DEPENDENCY_PUBLIC_ID in self.load_config().protocols
        # do not add dependencies for the package

        with self.with_oef_installed(), self.with_config_update(), patch(
            "aea.cli.add._add_item_deps"
        ):
            result = self.runner.invoke(
                cli,
                [
                    "-v",
                    "DEBUG",
                    "upgrade",
                    *self.LOCAL,
                    self.ITEM_TYPE,
                    f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:latest",
                ],
                catch_exceptions=True,
            )
            assert result.exit_code == 0
            assert self.DEPENDENCY_PUBLIC_ID in self.load_config().protocols


class TestUpgradeProject(BaseAEATestCase, BaseTestCase):
    """Test that the command 'aea upgrade' works."""

    capture_log = True

    @classmethod
    def setup(cls):
        """Set up test case."""
        super(TestUpgradeProject, cls).setup()
        cls.agent_name = "generic_buyer_0.9.0"
        cls.latest_agent_name = "generic_buyer_latest"
        cls.run_cli_command(
            "fetch", "fetchai/generic_buyer:0.9.0", "--alias", cls.agent_name
        )
        cls.run_cli_command(
            "fetch", "fetchai/generic_buyer:latest", "--alias", cls.latest_agent_name
        )
        cls.agents.add(cls.agent_name)
        cls.set_agent_context(cls.agent_name)

    def test_upgrade(self):
        """Test upgrade project old version to latest one and compare with latest project fetched."""
        with cd(self.latest_agent_name):
            latest_agent_items = set(
                ItemRemoveHelper(self.load_config())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )

        with cd(self.agent_name):
            self.runner.invoke(  # pylint: disable=no-member
                cli, ["upgrade"], standalone_mode=False, catch_exceptions=False
            )
            agent_items = set(
                ItemRemoveHelper(self.load_config())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )
            assert latest_agent_items == agent_items

        # upgrade again to check it workd with upgraded version
        with cd(self.agent_name):
            self.runner.invoke(  # pylint: disable=no-member
                cli, ["upgrade"], standalone_mode=False, catch_exceptions=False
            )
            agent_items = set(
                ItemRemoveHelper(self.load_config())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )
            assert latest_agent_items == agent_items


class TestNonVendorProject(BaseAEATestCase, BaseTestCase):
    """Test that the command 'aea upgrade' works."""

    capture_log = True

    @classmethod
    def setup(cls):
        """Set up test case."""
        super(TestNonVendorProject, cls).setup()
        cls.agent_name = "generic_buyer_0.9.0"
        cls.run_cli_command(
            "fetch", "fetchai/generic_buyer:0.9.0", "--alias", cls.agent_name
        )
        cls.agents.add(cls.agent_name)
        cls.set_agent_context(cls.agent_name)

    @patch("aea.cli.upgrade.ItemUpgrader.is_non_vendor", True)
    @patch(
        "aea.cli.upgrade.ItemUpgrader.check_upgrade_is_required", return_value="0.99.0"
    )
    @patch("aea.cli.upgrade.ItemUpgrader.remove_item")
    @patch("aea.cli.upgrade.ItemUpgrader.add_item")
    def test_non_vendor_nothing_to_upgrade(
        self, *mocks
    ):  # pylint: disable=unused-argument
        """Test upgrade project dependencies not removed cause non vendor."""
        with cd(self.agent_name):
            base_agent_items = set(
                ItemRemoveHelper(self.load_config())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )

            self.runner.invoke(  # pylint: disable=no-member
                cli, ["upgrade"], standalone_mode=False, catch_exceptions=False
            )
            agent_items = set(
                ItemRemoveHelper(self.load_config())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )
            assert base_agent_items == agent_items


class TestUpgradeConnectionLocally(BaseTestCase):
    """Test that the command 'aea upgrade connection' works."""

    ITEM_TYPE = "connection"
    ITEM_PUBLIC_ID = SOEF_PUBLIC_ID
    LOCAL: List[str] = ["--local"]

    @classmethod
    def setup(cls):
        """Set the test up."""
        super(TestUpgradeConnectionLocally, cls).setup()

        result = cls.runner.invoke(
            cli,
            ["-v", "DEBUG", "add", "--local", cls.ITEM_TYPE, str(cls.ITEM_PUBLIC_ID)],
            standalone_mode=False,
        )
        assert result.exit_code == 0

    def test_upgrade_to_same_version(self):
        """Test do not  upgrade to version already installed."""
        with pytest.raises(
            ClickException,
            match=r"The .* with id '.*' already has version .*. Nothing to upgrade.",
        ):
            self.runner.invoke(
                cli,
                ["upgrade", *self.LOCAL, self.ITEM_TYPE, str(self.ITEM_PUBLIC_ID)],
                standalone_mode=False,
                catch_exceptions=False,
            )

    @patch("aea.cli.upgrade.ItemUpgrader.is_non_vendor", True)
    def test_upgrade_non_vendor(self):
        """Test do not upgrade non vendor package."""
        with pytest.raises(
            ClickException,
            match=r"The .* with id '.*' already has version .*. Nothing to upgrade.",
        ):
            self.runner.invoke(
                cli,
                [
                    "upgrade",
                    *self.LOCAL,
                    self.ITEM_TYPE,
                    f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:100.0.0",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_upgrade_to_latest_but_same_version(self):
        """Test no update to latest if already latest component."""
        with pytest.raises(
            ClickException,
            match=r"The .* with id '.*' already has version .*. Nothing to upgrade.",
        ):
            self.runner.invoke(
                cli,
                [
                    "upgrade",
                    *self.LOCAL,
                    self.ITEM_TYPE,
                    f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:latest",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_upgrade_to_non_registered(self):
        """Test can not upgrade not registered component."""
        with pytest.raises(
            ClickException,
            match=r".* with id .* is not registered. Please use the `add` command. Aborting...",
        ):
            self.runner.invoke(
                cli,
                [
                    "-v",
                    "DEBUG",
                    "upgrade",
                    *self.LOCAL,
                    self.ITEM_TYPE,
                    "nonexits/dummy:0.0.0",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )

    def test_upgrade_required_mock(self):
        """Test upgrade with mocking upgrade required."""
        with patch(
            "aea.cli.upgrade.ItemUpgrader.check_upgrade_is_required",
            return_value="100.0.0",
        ):
            result = self.runner.invoke(
                cli,
                [
                    "-v",
                    "DEBUG",
                    "upgrade",
                    *self.LOCAL,
                    self.ITEM_TYPE,
                    f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:latest",
                ],
                catch_exceptions=False,
            )
            assert result.exit_code == 0

    def test_do_upgrade(self):
        """Test real full upgrade."""
        with self.with_config_update():
            result = self.runner.invoke(
                cli,
                [
                    "upgrade",
                    *self.LOCAL,
                    self.ITEM_TYPE,
                    f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:latest",
                ],
                standalone_mode=False,
            )
            assert result.exit_code == 0

    def test_package_can_not_be_found_in_registry(self):
        """Test no package in registry."""
        with self.with_config_update():
            with patch(
                "aea.cli.registry.utils.get_package_meta",
                side_effects=Exception("expected!"),
            ), patch(
                "aea.cli.registry.utils.find_item_locally",
                side_effects=Exception("expected!"),
            ), pytest.raises(
                ClickException,
                match=r"Package .* details can not be fetched from the registry!",
            ):
                self.runner.invoke(
                    cli,
                    [
                        "upgrade",
                        *self.LOCAL,
                        self.ITEM_TYPE,
                        f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:latest",
                    ],
                    standalone_mode=False,
                    catch_exceptions=False,
                )

    def test_package_can_not_upgraded_cause_required(self):
        """Test no package in registry."""
        with self.with_config_update():
            with patch(
                "aea.cli.upgrade.ItemRemoveHelper.check_remove",
                return_value=(
                    set([PackageId("connection", PublicId("test", "test", "0.0.1"))]),
                    set(),
                    dict(),
                ),
            ), pytest.raises(
                ClickException,
                match=r"Can not upgrade .* because it is required by '.*'",
            ):
                self.runner.invoke(
                    cli,
                    [
                        "upgrade",
                        *self.LOCAL,
                        self.ITEM_TYPE,
                        f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:latest",
                    ],
                    standalone_mode=False,
                    catch_exceptions=False,
                )

    @classmethod
    def teardown(cls):
        """Tear the test down."""
        super(TestUpgradeConnectionLocally, cls).teardown()

        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestUpgradeConnectionRemoteRegistry(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade connection' works."""

    LOCAL: List[str] = []

    def test_upgrade_to_latest_but_same_version(self):
        """Skip."""
        pass


class TestUpgradeProtocolLocally(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade protocol --local' works."""

    ITEM_TYPE = "protocol"
    ITEM_PUBLIC_ID = PublicId.from_str("fetchai/http:0.7.0")


class TestUpgradeProtocolRemoteRegistry(TestUpgradeProtocolLocally):
    """Test that the command 'aea upgrade protocol' works."""

    LOCAL: List[str] = []

    def test_upgrade_to_latest_but_same_version(self):
        """Skip."""
        pass


class TestUpgradeSkillLocally(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade skill --local' works."""

    ITEM_TYPE = "skill"
    ITEM_PUBLIC_ID = PublicId.from_str("fetchai/echo:0.9.0")


class TestUpgradeSkillRemoteRegistry(TestUpgradeSkillLocally):
    """Test that the command 'aea upgrade skill' works."""

    LOCAL: List[str] = []

    def test_upgrade_to_latest_but_same_version(self):
        """Skip."""
        pass

    def test_upgrade_required_mock(self):
        """Skip."""
        pass

    def test_do_upgrade(self):
        """Skip."""
        pass


class TestUpgradeContractLocally(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade contract' works."""

    ITEM_TYPE = "contract"
    ITEM_PUBLIC_ID = PublicId.from_str("fetchai/erc1155:0.11.0")


class TestUpgradeContractRemoteRegistry(TestUpgradeContractLocally):
    """Test that the command 'aea upgrade contract --local' works."""

    LOCAL: List[str] = []

    def test_upgrade_to_latest_but_same_version(self):
        """Skip."""
        pass
