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
from typing import List, Set, cast
from unittest.mock import MagicMock, patch

import pytest
from click.exceptions import ClickException
from click.testing import Result

from aea.cli import cli
from aea.cli.upgrade import ItemRemoveHelper
from aea.cli.utils.config import load_item_config
from aea.configurations.base import (
    AgentConfig,
    ComponentId,
    ComponentType,
    DEFAULT_AEA_CONFIG_FILE,
    PackageId,
    PackageType,
    PublicId,
)
from aea.configurations.loader import ConfigLoader, load_component_configuration
from aea.helpers.base import cd
from aea.test_tools.test_cases import AEATestCaseEmpty, BaseAEATestCase

from packages.fetchai.connections import oef
from packages.fetchai.connections.oef.connection import PUBLIC_ID as OEF_PUBLIC_ID
from packages.fetchai.connections.soef.connection import PUBLIC_ID as SOEF_PUBLIC_ID
from packages.fetchai.connections.stub.connection import StubConnection
from packages.fetchai.contracts.erc1155.contract import PUBLIC_ID as ERC1155_PUBLIC_ID
from packages.fetchai.protocols.default import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.echo import PUBLIC_ID as ECHO_SKILL_PUBLIC_ID
from packages.fetchai.skills.error import PUBLIC_ID as ERROR_SKILL_PUBLIC_ID

from tests.common.utils import are_dirs_equal
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

    def load_mock_context(self) -> MagicMock:
        """Load mock context."""
        context_mock = MagicMock(agent_config=self.load_config())
        return context_mock

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
            "aea.cli.upgrade.ItemUpgrader.check_upgrade_is_required",
            return_value=self.ITEM_PUBLIC_ID.version,
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


class TestUpgradeSharedDependencies(AEATestCaseEmpty):
    """
    Test removal of shared dependency.

    The shared dependency in this test case is 'fetchai/oef_search:0.9.0'.
    """

    IS_EMPTY = True
    OLD_SOEF_ID = PublicId.from_str("fetchai/soef:0.11.0")
    OLD_OEF_SEARCH_ID = PublicId.from_str("fetchai/oef_search:0.9.0")
    OLD_OEF_ID = PublicId.from_str("fetchai/oef:0.12.0")

    @classmethod
    def setup_class(cls):
        """
        Set the test up.

        Skip consistency checks to avoid aea version compatibility checks.
        """
        super().setup_class()
        result = cls.run_cli_command(
            "-s", "add", "connection", str(cls.OLD_SOEF_ID), cwd=cls._get_cwd()
        )
        assert result.exit_code == 0
        result = cls.run_cli_command(
            "-s", "add", "connection", str(cls.OLD_OEF_ID), cwd=cls._get_cwd()
        )
        assert result.exit_code == 0

    def test_upgrade_shared_dependencies(self):
        """Test upgrade shared dependencies."""
        result = self.run_cli_command("-s", "upgrade", cwd=self._get_cwd())
        assert result.exit_code == 0

        agent_config: AgentConfig = cast(
            AgentConfig,
            load_item_config(PackageType.AGENT.value, Path(self.current_agent_context)),
        )
        assert OefSearchMessage.protocol_id in agent_config.protocols
        assert SOEF_PUBLIC_ID in agent_config.connections
        assert OEF_PUBLIC_ID in agent_config.connections


class TestUpgradeProject(BaseAEATestCase, BaseTestCase):
    """Test that the command 'aea upgrade' works."""

    capture_log = True

    @classmethod
    def setup(cls):
        """Set up test case."""
        super(TestUpgradeProject, cls).setup()
        cls.change_directory(Path(".."))
        cls.agent_name = "generic_buyer_0.12.0"
        cls.latest_agent_name = "generic_buyer_latest"
        cls.run_cli_command(
            "--skip-consistency-check",
            "fetch",
            "fetchai/generic_buyer:0.17.0",
            "--alias",
            cls.agent_name,
        )
        cls.run_cli_command(
            "--skip-consistency-check",
            "fetch",
            "fetchai/generic_buyer:latest",
            "--alias",
            cls.latest_agent_name,
        )
        cls.agents.add(cls.agent_name)
        cls.set_agent_context(cls.agent_name)

    def test_upgrade(self):
        """Test upgrade project old version to latest one and compare with latest project fetched."""
        with cd(self.latest_agent_name):
            latest_agent_items = set(
                ItemRemoveHelper(self.load_mock_context())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )

        with cd(self.agent_name):
            self.runner.invoke(  # pylint: disable=no-member
                cli,
                ["--skip-consistency-check", "upgrade", "--local"],
                standalone_mode=False,
                catch_exceptions=False,
            )
            agent_items = set(
                ItemRemoveHelper(self.load_mock_context())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )
            assert latest_agent_items == agent_items

        # upgrade again to check it workd with upgraded version
        with cd(self.agent_name):
            self.runner.invoke(  # pylint: disable=no-member
                cli,
                ["--skip-consistency-check", "upgrade", "--local"],
                standalone_mode=False,
                catch_exceptions=False,
            )
            agent_items = set(
                ItemRemoveHelper(self.load_mock_context())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )
            assert latest_agent_items == agent_items

        # compare both configuration files, except the agent name
        upgraded_agent_dir = Path(self.agent_name)
        latest_agent_dir = Path(self.latest_agent_name)
        lines_upgraded_agent_config = (
            (upgraded_agent_dir / DEFAULT_AEA_CONFIG_FILE).read_text().splitlines()[1:]
        )
        lines_latest_agent_config = (
            (latest_agent_dir / DEFAULT_AEA_CONFIG_FILE).read_text().splitlines()[1:]
        )
        assert lines_upgraded_agent_config == lines_latest_agent_config

        # compare vendor folders.
        assert are_dirs_equal(
            upgraded_agent_dir / "vendor", latest_agent_dir / "vendor"
        )


class TestNonVendorProject(BaseAEATestCase, BaseTestCase):
    """Test that the command 'aea upgrade' works."""

    capture_log = True

    @classmethod
    def setup(cls):
        """Set up test case."""
        super(TestNonVendorProject, cls).setup()
        cls.change_directory(Path(".."))
        cls.agent_name = "generic_buyer_0.12.0"
        cls.run_cli_command(
            "fetch", "fetchai/generic_buyer:0.17.0", "--alias", cls.agent_name
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
                ItemRemoveHelper(self.load_mock_context())
                .get_agent_dependencies_with_reverse_dependencies()
                .keys()
            )

            self.runner.invoke(  # pylint: disable=no-member
                cli,
                ["--skip-consistency-check", "upgrade"],
                standalone_mode=False,
                catch_exceptions=False,
            )
            agent_items = set(
                ItemRemoveHelper(self.load_mock_context())
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
    ITEM_PUBLIC_ID = HttpMessage.protocol_id


class TestUpgradeProtocolRemoteRegistry(TestUpgradeProtocolLocally):
    """Test that the command 'aea upgrade protocol' works."""

    LOCAL: List[str] = []

    def test_upgrade_to_latest_but_same_version(self):
        """Skip."""
        pass


class TestUpgradeSkillLocally(TestUpgradeConnectionLocally):
    """Test that the command 'aea upgrade skill --local' works."""

    ITEM_TYPE = "skill"
    ITEM_PUBLIC_ID = ECHO_SKILL_PUBLIC_ID


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
    ITEM_PUBLIC_ID = ERC1155_PUBLIC_ID


class TestUpgradeContractRemoteRegistry(TestUpgradeContractLocally):
    """Test that the command 'aea upgrade contract --local' works."""

    LOCAL: List[str] = []

    def test_upgrade_to_latest_but_same_version(self):
        """Skip."""
        pass


@pytest.mark.integration
class TestUpgradeNonVendorDependencies(AEATestCaseEmpty):
    """
    Test that the command 'aea upgrade' correctly updates non-vendor package data.

    In particular, check that 'aea upgrade' updates the public ids of
    the package dependencies and the 'aea_version' field.

    The test works as follows:
    - scaffold a package, one for each possible package type;
    - add the protocol "fetchai/default:0.7.0" as dependency to each of them.
    - add the skill "fetchai/error:0.7.0"; this will also add the default protocol.
      add it also as dependency of non-vendor skill.
    - run 'aea upgrade'
    - check that the reference to "fetchai/default" in each scaffolded package
      has the new version.
    """

    capture_log = True
    IS_EMPTY = True
    old_default_protocol_id = PublicId(
        DefaultMessage.protocol_id.author, DefaultMessage.protocol_id.name, "0.7.0"
    )
    old_error_skill_id = PublicId(
        ERROR_SKILL_PUBLIC_ID.author, ERROR_SKILL_PUBLIC_ID.name, "0.7.0"
    )

    @classmethod
    def scaffold_item(cls, item_type: str, name: str) -> Result:
        """Override default behaviour by adding a custom dependency to the scaffolded item."""
        result = super(TestUpgradeNonVendorDependencies, cls).scaffold_item(
            item_type, name
        )
        # add custom dependency (a protocol) to each package
        # that supports dependencies (only connections and skills)
        if item_type in {ComponentType.CONNECTION.value, ComponentType.SKILL.value}:
            cls.nested_set_config(
                f"{ComponentType(item_type).to_plural()}.{name}.protocols",
                [str(cls.old_default_protocol_id)],
            )

        # add the vendor skill as dependency of the non-vendor skill
        if item_type == ComponentType.SKILL.value:
            cls.nested_set_config(
                f"{ComponentType(item_type).to_plural()}.{name}.skills",
                [str(cls.old_error_skill_id)],
            )
        return result

    @classmethod
    def setup_class(cls):
        """Set up test case."""
        super(TestUpgradeNonVendorDependencies, cls).setup_class()
        cls.scaffold_item("protocol", "my_protocol")
        cls.scaffold_item("connection", "my_connection")
        cls.scaffold_item("contract", "my_contract")
        cls.scaffold_item("skill", "my_skill")
        cls.run_cli_command(
            "--skip-consistency-check",
            "add",
            "skill",
            str(cls.old_error_skill_id),
            cwd=cls._get_cwd(),
        )
        cls.run_cli_command(
            "--skip-consistency-check", "upgrade", "--local", cwd=cls._get_cwd()
        )

    def test_agent_config_updated(self):
        """Test the agent configuration is updated."""
        loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
        with Path(self._get_cwd(), DEFAULT_AEA_CONFIG_FILE).open() as fp:
            agent_config = loader.load(fp)
        assert DefaultMessage.protocol_id in agent_config.protocols
        assert ERROR_SKILL_PUBLIC_ID in agent_config.skills

    def test_non_vendor_update_references_to_upgraded_packages(
        self,
    ):  # pylint: disable=unused-argument
        """Test that dependencies in non-vendor packages are updated correctly after upgrade."""
        self.assert_dependency_updated(
            ComponentType.CONNECTION,
            "my_connection",
            "protocols",
            {DefaultMessage.protocol_id},
        )
        self.assert_dependency_updated(
            ComponentType.SKILL, "my_skill", "protocols", {DefaultMessage.protocol_id}
        )
        self.assert_dependency_updated(
            ComponentType.SKILL, "my_skill", "skills", {ERROR_SKILL_PUBLIC_ID}
        )

    def assert_dependency_updated(
        self,
        item_type: ComponentType,
        package_name: str,
        package_type: str,
        expected: Set[PublicId],
    ):
        """Assert dependency is updated."""
        package_path = Path(self._get_cwd(), item_type.to_plural(), package_name)
        component_config = load_component_configuration(item_type, package_path)
        assert hasattr(component_config, package_type), "Test is not well-written."
        assert getattr(component_config, package_type) == expected  # type: ignore


class TestUpdateReferences(AEATestCaseEmpty):
    """
    Test that references are updated correctly after 'aea upgrade'.

    In particular, 'default_routing', 'default_connection' and custom component configurations in AEA configuration.

    How the test works:
    - add fetchai/error:0.7.0, that requires fetchai/default:0.7.0
    - add fetchai/stub:0.13.0
    - add 'fetchai/default:0.7.0: fetchai/stub:0.13.0' to default routing
    - add custom configuration to stub connection.
    - run 'aea upgrade'. This will upgrade `stub` connection and `error` skill, and in turn `default` protocol.
    """

    IS_EMPTY = True

    OLD_DEFAULT_PROTOCOL_PUBLIC_ID = PublicId.from_str("fetchai/default:0.7.0")
    OLD_ERROR_SKILL_PUBLIC_ID = PublicId.from_str("fetchai/error:0.7.0")
    OLD_STUB_CONNECTION_PUBLIC_ID = PublicId.from_str("fetchai/stub:0.13.0")

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        super().setup_class()
        cls.run_cli_command(
            "--skip-consistency-check",
            "add",
            "skill",
            str(cls.OLD_ERROR_SKILL_PUBLIC_ID),
            cwd=cls._get_cwd(),
        )
        cls.run_cli_command(
            "--skip-consistency-check",
            "add",
            "connection",
            str(cls.OLD_STUB_CONNECTION_PUBLIC_ID),
            cwd=cls._get_cwd(),
        )

        cls.nested_set_config(
            "agent.default_routing",
            {cls.OLD_DEFAULT_PROTOCOL_PUBLIC_ID: cls.OLD_STUB_CONNECTION_PUBLIC_ID},
        )
        cls.nested_set_config(
            "agent.default_connection", cls.OLD_STUB_CONNECTION_PUBLIC_ID,
        )
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

        cls.run_cli_command(
            "--skip-consistency-check", "upgrade", "--local", cwd=cls._get_cwd()
        )

    def test_default_routing_updated_correctly(self):
        """Test default routing has been updated correctly."""
        result = self.run_cli_command(
            "--skip-consistency-check",
            "config",
            "get",
            "agent.default_routing",
            cwd=self._get_cwd(),
        )
        assert (
            result.stdout
            == f"{{'{DefaultMessage.protocol_id}': '{StubConnection.connection_id}'}}\n"
        )

    def test_default_connection_updated_correctly(self):
        """Test default routing has been updated correctly."""
        result = self.run_cli_command(
            "--skip-consistency-check",
            "config",
            "get",
            "agent.default_connection",
            cwd=self._get_cwd(),
        )
        assert result.stdout == "fetchai/stub:0.13.0\n"

    def test_custom_configuration_updated_correctly(self):
        """Test default routing has been updated correctly."""
        result = self.run_cli_command(
            "--skip-consistency-check",
            "config",
            "get",
            "vendor.fetchai.skills.error.is_abstract",
            cwd=self._get_cwd(),
        )
        assert result.stdout == "True\n"


class TestNothingToUpgrade(AEATestCaseEmpty):
    """Test the upgrade command when there's nothing t upgrade."""

    def test_nothing_to_upgrade(self):
        """Test nothing to upgrade."""
        result = self.run_cli_command("upgrade", cwd=self._get_cwd())
        assert (
            result.stdout
            == "Starting project upgrade...\nEverything is already up to date!\n"
        )
