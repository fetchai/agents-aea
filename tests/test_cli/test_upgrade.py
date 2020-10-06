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

from aea.cli import cli, upgrade
from aea.configurations.base import (
    AgentConfig,
    DEFAULT_AEA_CONFIG_FILE,
    PackageType,
    PublicId,
)
from aea.configurations.loader import ConfigLoader

from packages.fetchai.connections import oef
from packages.fetchai.connections.soef.connection import PUBLIC_ID as SOEF_PUBLIC_ID
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

from tests.conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH, CliRunner


class BaseTestCase:
    """Base test case class with setup and teardown and some utils."""

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
    def setup_class(cls):
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

    @classmethod
    def teardown_class(cls):
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
    def setup_class(cls):
        """Set the test up."""
        super(TestRemoveAndDependencies, cls).setup_class()
        cls.DEPENDENCY = (cls.DEPENDENCY_TYPE, cls.DEPENDENCY_PUBLIC_ID)
        result = cls.runner.invoke(
            cli,
            ["-v", "DEBUG", "add", "--local", cls.ITEM_TYPE, str(cls.ITEM_PUBLIC_ID)],
            standalone_mode=False,
        )
        assert result.exit_code == 0

    def setup(self):
        """Save agent config."""
        self._agent_config = self.load_config()

    def teardown(self):
        """Restore agent config."""
        self.dump_config(self._agent_config)

    def check_remove(self, item_type, public_id):
        """Check remove can be performed with remove helper."""
        return upgrade.ItemRemoveHelper(self.load_config()).check_remove(
            item_type, public_id
        )

    def test_package_can_be_removed_with_its_dependency(self):
        """Test package can be removed with its dependency."""
        required_by, can_be_removed, can_not_be_removed = self.check_remove(
            self.ITEM_TYPE, self.ITEM_PUBLIC_ID
        )

        assert not required_by, required_by
        assert self.DEPENDENCY in can_be_removed
        assert self.DEPENDENCY not in can_not_be_removed

    def test_package_can_be_removed_but_not_dependency(self):
        """Test package can be removed but not its dependency."""
        with self.with_oef_installed():
            required_by, can_be_removed, can_not_be_removed = self.check_remove(
                self.ITEM_TYPE, self.ITEM_PUBLIC_ID
            )

            assert not required_by, required_by
            assert self.DEPENDENCY not in can_be_removed
            assert self.DEPENDENCY in can_not_be_removed

    def test_package_can_not_be_removed_cause_required(self):
        """Test package can not be removed cause required by another package."""
        required_by, can_be_removed, can_not_be_removed = self.check_remove(
            self.DEPENDENCY_TYPE, self.DEPENDENCY_PUBLIC_ID
        )

        assert (self.ITEM_TYPE, self.ITEM_PUBLIC_ID) in required_by
        assert not can_be_removed
        assert not can_not_be_removed

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
        config_data[f"{self.ITEM_TYPE}s"].remove(str(self.ITEM_PUBLIC_ID))
        config_data[f"{self.ITEM_TYPE}s"].append(
            f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}:0.0.1"
        )
        self.dump_config(AgentConfig.from_json(config_data))
        try:
            yield
        finally:
            self.dump_config(original_config)

    def test_upgrade_and_dependency_removed(self):
        """
        Test dependency removed after upgrade.

        Done with mocking _add_item_deps to avoid dependencies installation.
        """
        assert self.DEPENDENCY_PUBLIC_ID in self.load_config().protocols

        with self.with_config_update(), patch("aea.cli.add._add_item_deps"):
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


class TestUpgradeProject(BaseTestCase):
    """Test that the command 'aea upgrade' works."""

    ITEM_TYPE = "connection"
    ITEM_PUBLIC_ID = SOEF_PUBLIC_ID
    LOCAL: List[str] = ["--local"]

    def test_uprgade_does_nothing(self):
        """Test project upgrade is not implemented yet."""
        result = self.runner.invoke(
            cli, ["-v", "DEBUG", "upgrade", "--local"], standalone_mode=False,
        )
        assert result.exit_code == 0


class TestUpgradeConnectionLocally(BaseTestCase):
    """Test that the command 'aea upgrade connection' works."""

    ITEM_TYPE = "connection"
    ITEM_PUBLIC_ID = SOEF_PUBLIC_ID
    LOCAL: List[str] = ["--local"]

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super(TestUpgradeConnectionLocally, cls).setup_class()

        result = cls.runner.invoke(
            cli,
            ["-v", "DEBUG", "add", "--local", cls.ITEM_TYPE, str(cls.ITEM_PUBLIC_ID)],
            standalone_mode=False,
        )
        assert result.exit_code == 0

    def test_upgrade_to_same_version(self):
        """Test do not  upgreade to version already installed."""
        result = self.runner.invoke(
            cli,
            ["upgrade", *self.LOCAL, self.ITEM_TYPE, str(self.ITEM_PUBLIC_ID)],
            standalone_mode=False,
        )
        assert result.exit_code == 1
        assert b"Nothing to upgrade." in result.stdout_bytes

    def test_upgrade_to_latest_but_same_version(self):
        """Test no update to latest if already latest component."""
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
        assert result.exit_code == 1

    def test_upgrade_to_non_registered(self):
        """Test can not upgrade not registered component."""
        result = self.runner.invoke(
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
        )

        assert result.exit_code == 1
        assert (
            "is not registered. Please use `add` command. Aborting"
            in result.exception.message
        )

    def test_upgrade_required_mock(self):
        """Test upgrade with mocking upgrade required."""
        with patch.object(upgrade, "_check_upgrade_is_required", return_value=True):
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
            with patch.object(
                upgrade, "_get_package_meta", side_effects=Exception("expected!")
            ), patch.object(
                upgrade, "find_item_locally", side_effects=Exception("expected!")
            ):
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
            assert result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestUpgradeConnectionRemoteRegistry(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade connection' works."""

    LOCAL: List[str] = []


class TestUpgradeProtocolLocally(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade protocol --local' works."""

    ITEM_TYPE = "protocol"
    ITEM_PUBLIC_ID = PublicId.from_str("fetchai/http:0.6.0")


class TestUpgradeProtocolRemoteRegistry(TestUpgradeProtocolLocally):
    """Test that the command 'aea upgrade protocol' works."""

    LOCAL: List[str] = []


class TestUpgradeSkillLocally(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade skill --local' works."""

    ITEM_TYPE = "skill"
    ITEM_PUBLIC_ID = PublicId.from_str("fetchai/echo:0.8.0")


class TestUpgradeSkillRemoteRegistry(TestUpgradeSkillLocally):
    """Test that the command 'aea upgrade skill' works."""

    LOCAL: List[str] = []


class TestUpgradeContractLocally(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade contract' works."""

    ITEM_TYPE = "contract"
    ITEM_PUBLIC_ID = PublicId.from_str("fetchai/erc1155:0.10.0")


class TestUpgradeContractRemoteRegistry(TestUpgradeContractLocally):
    """Test that the command 'aea upgrade contract --local' works."""

    LOCAL: List[str] = []
