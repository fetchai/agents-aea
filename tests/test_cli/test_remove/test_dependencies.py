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
"""This test module contains the tests for the `aea add connection` sub-command."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.exceptions import ClickException

from aea.cli import cli
from aea.cli.upgrade import ItemRemoveHelper
from aea.configurations.base import (
    AgentConfig,
    DEFAULT_AEA_CONFIG_FILE,
    PackageId,
    PackageType,
)
from aea.configurations.loader import ConfigLoader

from packages.fetchai.connections.http_server.connection import (
    PUBLIC_ID as HTTP_SERVER_PUBLIC_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage

from tests.conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH, CliRunner


class TestRemoveAndDependencies:  # pylint: disable=attribute-defined-outside-init
    """Test dependency remove helper and upgrade with dependency removed."""

    ITEM_TYPE = "connection"
    ITEM_PUBLIC_ID = HTTP_SERVER_PUBLIC_ID
    DEPENDENCY_TYPE = "protocol"
    DEPENDENCY_PUBLIC_ID = HttpMessage.protocol_id

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

    def setup(self):
        """Set the test up."""
        self.runner = CliRunner()
        self.agent_name = "myagent"
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(self.t, "packages"))

        os.chdir(self.t)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", self.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(self.agent_name)

        # add connection first time
        self.DEPENDENCY_PACKAGE_ID = PackageId(
            self.DEPENDENCY_TYPE, self.DEPENDENCY_PUBLIC_ID
        )
        result = self.runner.invoke(
            cli,
            ["-v", "DEBUG", "add", "--local", self.ITEM_TYPE, str(self.ITEM_PUBLIC_ID)],
            standalone_mode=False,
            catch_exceptions=False,
        )

    def teardown(self):
        """Tear the test down."""
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except (OSError, IOError):
            pass

    def check_remove(self, item_type, public_id):
        """Check remove can be performed with remove helper."""
        context_mock = MagicMock(agent_config=self.load_config())
        return ItemRemoveHelper(context_mock).check_remove(item_type, public_id)

    def test_package_can_be_removed_with_its_dependency(self):
        """Test package (soef) can be removed with its dependency (oef_search)."""
        required_by, can_be_removed, can_not_be_removed = self.check_remove(
            self.ITEM_TYPE, self.ITEM_PUBLIC_ID
        )

        assert not required_by, required_by
        assert self.DEPENDENCY_PACKAGE_ID in can_be_removed
        assert self.DEPENDENCY_PACKAGE_ID not in can_not_be_removed

    # def _install_oef(self):  # noqa: E800
    #     self.runner.invoke(  # noqa: E800
    #         cli,  # noqa: E800
    #         [  # noqa: E800
    #             "-v",  # noqa: E800
    #             "DEBUG",  # noqa: E800
    #             "add",  # noqa: E800
    #             "--local",  # noqa: E800
    #             "connection",  # noqa: E800
    #             str(oef.connection.PUBLIC_ID),  # noqa: E800
    #         ],  # noqa: E800
    #         standalone_mode=False,  # noqa: E800
    #         catch_exceptions=False,  # noqa: E800
    #     )  # noqa: E800

    # def test_package_can_be_removed_but_not_dependency(self):  # noqa: E800
    #     """Test package (soef) can be removed but not its shared dependency (oef_search) with other package (oef)."""  # noqa: E800
    #     self._install_oef()  # noqa: E800
    #     required_by, can_be_removed, can_not_be_removed = self.check_remove(  # noqa: E800
    #         self.ITEM_TYPE, self.ITEM_PUBLIC_ID  # noqa: E800
    #     )  # noqa: E800

    #     assert not required_by, required_by  # noqa: E800
    #     assert self.DEPENDENCY_PACKAGE_ID not in can_be_removed  # noqa: E800
    #     assert self.DEPENDENCY_PACKAGE_ID in can_not_be_removed  # noqa: E800

    def test_package_can_not_be_removed_cause_required_by_another_package(self):
        """Test package (oef_search) can not be removed cause required by another package (soef)."""
        required_by, can_be_removed, can_not_be_removed = self.check_remove(
            self.DEPENDENCY_TYPE, self.DEPENDENCY_PUBLIC_ID
        )

        assert PackageId(self.ITEM_TYPE, self.ITEM_PUBLIC_ID) in required_by
        assert not can_be_removed
        assert not can_not_be_removed

    def test_removed_with_dependencies(self):
        """
        Test dependency removed after upgrade.

        Done with mocking _add_item_deps to avoid dependencies installation.
        """
        assert self.DEPENDENCY_PUBLIC_ID in {
            p.without_hash() for p in self.load_config().protocols
        }

        self.runner.invoke(
            cli,
            [
                "-v",
                "DEBUG",
                "remove",
                "--with-dependencies",
                self.ITEM_TYPE,
                f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}",
            ],
            standalone_mode=False,
            catch_exceptions=False,
        )
        assert self.DEPENDENCY_PUBLIC_ID not in self.load_config().protocols

    # def test_removed_and_dependency_not_removed_caused_required_by_another_item(self):  # noqa: E800
    #     """Test dependency is not removed after upgrade cause required by another item."""  # noqa: E800
    #     assert self.DEPENDENCY_PUBLIC_ID in self.load_config().protocols  # noqa: E800
    #     # do not add dependencies for the package  # noqa: E800

    #     self._install_oef()  # noqa: E800
    #     self.runner.invoke(  # noqa: E800
    #         cli,  # noqa: E800
    #         [  # noqa: E800
    #             "-v",  # noqa: E800
    #             "DEBUG",  # noqa: E800
    #             "remove",  # noqa: E800
    #             "--with-dependencies",  # noqa: E800
    #             self.ITEM_TYPE,  # noqa: E800
    #             f"{self.ITEM_PUBLIC_ID.author}/{self.ITEM_PUBLIC_ID.name}",  # noqa: E800
    #         ],  # noqa: E800
    #         standalone_mode=False,  # noqa: E800
    #         catch_exceptions=False,  # noqa: E800
    #     )  # noqa: E800
    #     assert self.DEPENDENCY_PUBLIC_ID in self.load_config().protocols  # noqa: E800

    def test_not_removed_cause_required(self):
        """Test dependency is not removed after upgrade cause required by another item."""
        assert self.DEPENDENCY_PUBLIC_ID in {
            p.without_hash() for p in self.load_config().protocols
        }
        # do not add dependencies for the package
        with pytest.raises(
            ClickException,
            match="Package .* can not be removed because it is required by .*",
        ):
            self.runner.invoke(
                cli,
                [
                    "-v",
                    "DEBUG",
                    "remove",
                    "--with-dependencies",
                    self.DEPENDENCY_TYPE,
                    f"{self.DEPENDENCY_PUBLIC_ID.author}/{self.DEPENDENCY_PUBLIC_ID.name}",
                ],
                standalone_mode=False,
                catch_exceptions=False,
            )
        assert self.DEPENDENCY_PUBLIC_ID in {
            p.without_hash() for p in self.load_config().protocols
        }
