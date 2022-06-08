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
"""Test module for aea.cli.remove.remove_item method."""
import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, mock
from unittest.mock import patch

import pytest
from click import ClickException

from aea.cli.core import cli
from aea.cli.remove import remove_item
from aea.configurations.base import (
    AgentConfig,
    DEFAULT_AEA_CONFIG_FILE,
    PackageType,
    PublicId,
)
from aea.configurations.loader import ConfigLoader
from aea.helpers.base import cd
from aea.test_tools.click_testing import CliRunner
from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.connections.local.connection import PUBLIC_ID as LOCAL_PUBLIC_ID
from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH
from tests.test_cli.tools_for_testing import ContextMock, PublicIdMock


@mock.patch("aea.cli.remove.shutil.rmtree")
@mock.patch("aea.cli.remove.Path.exists", return_value=False)
@mock.patch("aea.cli.remove.try_to_load_agent_config")
class RemoveItemTestCase(TestCase):
    """Test case for remove_item method."""

    def test_remove_item_item_folder_not_exists(
        self, *mocks
    ):  # pylint: disable=unused-argument
        """Test for save_agent_locally item folder not exists."""
        public_id = PublicIdMock.from_str("author/name:0.1.0")
        with pytest.raises(ClickException, match="Can not find folder for the package"):
            remove_item(ContextMock(protocols=[public_id]), "protocol", public_id)


@mock.patch("aea.cli.remove.shutil.rmtree")
@mock.patch("aea.cli.remove.Path.exists", return_value=True)
@mock.patch("aea.cli.remove.ItemRemoveHelper.get_component_directory")
@mock.patch("aea.cli.remove.load_item_config")
@mock.patch("aea.cli.remove.try_to_load_agent_config")
class RemoveItemBadConfigurationTestCase(TestCase):
    """Test case for remove_item method."""

    def test_remove_item_item_folder_not_exists(
        self, *mocks
    ):  # pylint: disable=unused-argument
        """Test for component bad configuration load."""
        public_id = PublicIdMock.from_str("author/name:0.1.0")
        with pytest.raises(
            ClickException,
            match="Error loading .* configuration, author/name do not match: .*",
        ):
            remove_item(ContextMock(protocols=[public_id]), "protocol", public_id)


class TestRemovePackageWithLatestVersion(AEATestCaseEmpty):
    """Test case for remove package with latest version."""

    @pytest.mark.skip  # need remote registry
    @pytest.mark.parametrize(
        ["type_", "public_id"],
        [
            ("protocol", DefaultMessage.protocol_id),
            ("connection", PublicId("fetchai", "stub").to_latest()),
            ("contract", PublicId("fetchai", "erc1155").to_latest()),
        ],
    )
    def test_remove_pacakge_latest_version(self, type_, public_id):
        """Test remove protocol with latest version."""
        assert public_id.package_version.is_latest
        # we need this because there isn't a default contract/connection
        if type_ == "connection":
            self.add_item("connection", str(public_id))
        if type_ == "contract":
            self.add_item("contract", str(public_id))

        # first, check the package is present
        items_path = os.path.join(self.agent_name, "vendor", "fetchai", type_ + "s")
        items_folders = os.listdir(items_path)
        item_name = public_id.name
        assert item_name in items_folders

        # remove the package
        with patch("aea.cli.remove.RemoveItem.is_required_by", False):
            self.run_cli_command(
                *["remove", type_, str(public_id)], cwd=self._get_cwd()
            )

        # check that the 'aea remove' took effect.
        items_folders = os.listdir(items_path)
        assert item_name not in items_folders


class TestRemoveConfig(
    AEATestCaseEmpty
):  # pylint: disable=attribute-defined-outside-init
    """Test component configuration also removed from agent config."""

    ITEM_TYPE = "connection"
    ITEM_PUBLIC_ID = LOCAL_PUBLIC_ID

    @staticmethod
    def loader() -> ConfigLoader:
        """Return Agent config loader."""
        return ConfigLoader.from_configuration_type(PackageType.AGENT)

    def load_config(self) -> AgentConfig:
        """Load AgentConfig from current directory."""
        with cd(self._get_cwd()):
            agent_loader = self.loader()
            path = Path(DEFAULT_AEA_CONFIG_FILE)
            with path.open(mode="r", encoding="utf-8") as fp:
                agent_config = agent_loader.load(fp)
            return agent_config

    # def test_component_configuration_removed_from_agent_config(self):  # noqa: E800
    #     """Test component configuration removed from agent config."""  # noqa: E800
    #     with cd(self._get_cwd()):  # noqa: E800
    #         self.run_cli_command(  # noqa: E800
    #             "add", "--local", self.ITEM_TYPE, str(self.ITEM_PUBLIC_ID)  # noqa: E800
    #         )  # noqa: E800
    #         self.run_cli_command("add", "--local", "connection", "fetchai/http_server")  # noqa: E800

    #         self.runner.invoke(  # noqa: E800
    #             cli,  # noqa: E800
    #             [  # noqa: E800
    #                 "config",  # noqa: E800
    #                 "set",  # noqa: E800
    #                 "vendor.fetchai.connections.local.config.api_key",  # noqa: E800
    #                 "some_api_key",  # noqa: E800
    #             ],  # noqa: E800
    #             standalone_mode=False,  # noqa: E800
    #             catch_exceptions=False,  # noqa: E800
    #         )  # noqa: E800
    #         self.runner.invoke(  # noqa: E800
    #             cli,  # noqa: E800
    #             [  # noqa: E800
    #                 "config",  # noqa: E800
    #                 "set",  # noqa: E800
    #                 "vendor.fetchai.connections.http_server.config.port",  # noqa: E800
    #                 "9000",  # noqa: E800
    #             ],  # noqa: E800
    #             standalone_mode=False,  # noqa: E800
    #             catch_exceptions=False,  # noqa: E800
    #         )  # noqa: E800
    #         config = self.load_config()  # noqa: E800
    #         assert config.component_configurations  # noqa: E800
    #         assert (  # noqa: E800
    #             PackageId(self.ITEM_TYPE, self.ITEM_PUBLIC_ID)  # noqa: E800
    #             in config.component_configurations  # noqa: E800
    #         )  # noqa: E800

    #         self.run_cli_command("remove", self.ITEM_TYPE, str(self.ITEM_PUBLIC_ID))  # noqa: E800

    #         config = self.load_config()  # noqa: E800
    #         assert (  # noqa: E800
    #             PackageId(self.ITEM_TYPE, self.ITEM_PUBLIC_ID)  # noqa: E800
    #             not in config.component_configurations  # noqa: E800
    #         )  # noqa: E800
    #         assert config.component_configurations  # noqa: E800


class TestRemoveWithIncompatibleAEAVersion:
    """Test remove command when agent/package has incompatible aea version."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "..", "packages"), Path(cls.t, "packages"))
        cls.connection_id = str(HTTP_CLIENT_PUBLIC_ID)
        cls.connection_name = "http_client"

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
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", cls.connection_id],
            standalone_mode=False,
        )
        assert result.exit_code == 0

    def test_exit_code_equal_to_zero(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""

        with patch("aea.configurations.base.__aea_version__", "2.0.0"):
            result = self.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, "remove", "connection", self.connection_id],
                standalone_mode=False,
                catch_exceptions=False,
            )

            assert result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
