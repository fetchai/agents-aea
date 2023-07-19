# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
"""This test module contains the tests for CLI Registry fetch methods."""
import os
import shutil
import sys
from abc import ABC
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

import click
import pytest
from aea_cli_ipfs.ipfs_utils import DownloadError, IPFSTool
from click import ClickException

from aea.cli import cli
from aea.cli.fetch import _is_version_correct, fetch_agent_locally
from aea.cli.registry.settings import REMOTE_HTTP, REMOTE_IPFS
from aea.cli.utils.context import Context
from aea.configurations.base import PublicId
from aea.helpers.base import cd
from aea.test_tools.test_cases import (
    AEATestCaseMany,
    AEATestCaseManyFlaky,
    BaseAEATestCase,
)

from tests.conftest import (
    CLI_LOG_OPTION,
    CliRunner,
    MAX_FLAKY_RERUNS,
    MY_FIRST_AEA_PUBLIC_ID,
    PACKAGES_DIR,
    TEST_IPFS_REGISTRY_CONFIG,
)
from tests.test_cli.tools_for_testing import ContextMock, PublicIdMock


def _raise_click_exception(*args, **kwargs):
    raise ClickException("Message")


@mock.patch("builtins.open", mock.mock_open())
@mock.patch("aea.cli.utils.decorators._cast_ctx")
@mock.patch("aea.cli.fetch.os.path.join", return_value="joined-path")
@mock.patch("aea.cli.fetch.try_get_item_source_path", return_value="path")
@mock.patch("aea.cli.fetch.try_to_load_agent_config")
class FetchAgentLocallyTestCase(TestCase):
    """Test case for fetch_agent_locally method."""

    @mock.patch("aea.cli.fetch._is_version_correct", return_value=True)
    @mock.patch("aea.cli.fetch.os.path.exists", return_value=False)
    @mock.patch("aea.cli.fetch.copy_tree")
    def test_fetch_agent_locally_positive(self, copy_tree, *mocks):
        """Test for fetch_agent_locally method positive result."""
        ctx = ContextMock()
        ctx.config["is_local"] = True
        fetch_agent_locally(ctx, PublicIdMock(), alias="some-alias")
        copy_tree.assert_called_once_with("path", "joined-path")

    @mock.patch("aea.cli.fetch._is_version_correct", return_value=True)
    @mock.patch("aea.cli.fetch.os.path.exists", return_value=True)
    @mock.patch("aea.cli.fetch.copy_tree")
    def test_fetch_agent_locally_already_exists(self, *mocks):
        """Test for fetch_agent_locally method agent already exists."""
        ctx = ContextMock()
        ctx.config["is_local"] = True
        with self.assertRaises(ClickException):
            fetch_agent_locally(ctx, PublicIdMock())

    @mock.patch("aea.cli.fetch._is_version_correct", return_value=False)
    @mock.patch("aea.cli.fetch.os.path.exists", return_value=True)
    @mock.patch("aea.cli.fetch.copy_tree")
    def test_fetch_agent_locally_incorrect_version(self, *mocks):
        """Test for fetch_agent_locally method incorrect agent version."""
        ctx = ContextMock()
        ctx.config["is_local"] = True
        with self.assertRaises(ClickException):
            fetch_agent_locally(ctx, PublicIdMock())

    @mock.patch("aea.cli.fetch._is_version_correct", return_value=True)
    @mock.patch("aea.cli.fetch.add_item")
    @mock.patch("aea.cli.fetch.os.path.exists", return_value=False)
    @mock.patch("aea.cli.fetch.copy_tree")
    def test_fetch_agent_locally_with_deps_positive(self, *mocks):
        """Test for fetch_agent_locally method with deps positive result."""
        public_id = PublicIdMock.from_str("author/name:0.1.0")
        ctx_mock = ContextMock(
            connections=[public_id],
            protocols=[public_id],
            skills=[public_id],
            contracts=[public_id],
        )
        ctx_mock.config["is_local"] = True
        fetch_agent_locally(ctx_mock, PublicIdMock())

    @mock.patch("aea.cli.fetch._is_version_correct", return_value=True)
    @mock.patch("aea.cli.fetch.os.path.exists", return_value=False)
    @mock.patch("aea.cli.fetch.copy_tree")
    @mock.patch("aea.cli.fetch.add_item", _raise_click_exception)
    def test_fetch_agent_locally_with_deps_fail(self, *mocks):
        """Test for fetch_agent_locally method with deps ClickException catch."""
        public_id = PublicIdMock.from_str("author/name:0.1.0")
        ctx_mock = ContextMock(
            connections=[public_id],
            protocols=[public_id],
            skills=[public_id],
            contracts=[public_id],
        )
        ctx_mock.config["is_local"] = True
        with self.assertRaises(ClickException):
            fetch_agent_locally(ctx_mock, PublicIdMock())


@mock.patch("aea.cli.fetch.fetch_agent_remote")
@mock.patch("aea.cli.fetch.fetch_agent_locally")
class FetchCommandTestCase(TestCase):
    """Test case for CLI fetch command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_fetch_positive_mixed(self, *mocks):
        """Test for CLI push connection positive result."""
        self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fetch", "author/name:0.1.0"],
            standalone_mode=False,
        )

    def test_fetch_positive_local(self, *mocks):
        """Test for CLI push connection positive result."""
        self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fetch", "--local", "author/name:0.1.0"],
            standalone_mode=False,
        )

    def test_fetch_positive_remote(self, *mocks):
        """Test for CLI push connection positive result."""
        self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fetch", "--remote", "author/name:0.1.0"],
            standalone_mode=False,
        )


class IsVersionCorrectTestCase(TestCase):
    """Test case for _is_version_correct method."""

    def test__is_version_correct_positive(self):
        """Test for _is_version_correct method positive result."""
        public_id = PublicId("author", "package", "0.1.0")
        ctx_mock = ContextMock(version=public_id.version)
        ctx_mock.agent_config.public_id = public_id
        result = _is_version_correct(ctx_mock, public_id)
        self.assertTrue(result)

    def test__is_version_correct_negative(self):
        """Test for _is_version_correct method negative result."""
        public_id_a = PublicId("author", "package", "0.1.0")
        public_id_b = PublicId("author", "package", "0.1.1")
        ctx_mock = ContextMock(version=public_id_b.version)
        ctx_mock.agent_config.public_id = public_id_b
        result = _is_version_correct(ctx_mock, public_id_a)
        self.assertFalse(result)


@pytest.mark.skip(reason="https://agents-registry.prod.fetch-ai.com/ is down")
class TestFetchFromRemoteRegistryHTTP(AEATestCaseManyFlaky):
    """Test case for fetch agent command from Registry."""

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_fetch_agent_from_remote_registry_positive(self):
        """Test fetch agent from Registry for positive result."""

        with mock.patch(
            "aea.cli.utils.config.get_or_create_cli_config",
            return_value=TEST_IPFS_REGISTRY_CONFIG,
        ), mock.patch(
            "aea.cli.registry.utils.get_or_create_cli_config",
            return_value=TEST_IPFS_REGISTRY_CONFIG,
        ), mock.patch(
            "aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_HTTP
        ):
            self.run_cli_command(
                "--skip-consistency-check",
                "fetch",
                "fetchai/my_first_aea:0.28.4",
                "--remote",
            )
        assert "my_first_aea" in os.listdir(self.t)


class TestFetchFromRemoteRegistryIPFS(AEATestCaseManyFlaky):
    """Test case for fetch agent command from Registry."""

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_fetch_agent_from_remote_registry_positive(self):
        """Test fetch agent from Registry for positive result."""

        with mock.patch(
            "aea.cli.utils.config.get_or_create_cli_config",
            return_value=TEST_IPFS_REGISTRY_CONFIG,
        ), mock.patch(
            "aea.cli.registry.utils.get_or_create_cli_config",
            return_value=TEST_IPFS_REGISTRY_CONFIG,
        ), mock.patch(
            "aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_IPFS
        ):
            self.run_cli_command(
                "fetch",
                "open_aea/my_first_aea:0.1.0:bafybeiewms67jpwf46u4wwh6tbzedsi5jffajnywgydeo5nlvvr6pcz2zm",
                "--remote",
            )
        assert "my_first_aea" in os.listdir(self.t)


class TestFetchMixedModeFallsBackCorrectly(AEATestCaseManyFlaky):
    """Test fetch command when registry fetch fails falls back to remote fetch."""

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    @mock.patch(
        "aea.cli.fetch.fetch_agent_remote",
    )
    @mock.patch("aea.cli.fetch.fetch_agent_locally", side_effect=ClickException(""))
    def test_fetch_agent_from_local_registry_falls_back_to_remote(
        self, local_fetch, remote_fetch
    ):
        """Test fetch agent from Registry for positive result."""
        self.run_cli_command("fetch", "--mixed", str(MY_FIRST_AEA_PUBLIC_ID))
        remote_fetch.assert_called()


class TestFetchMixedModeLocalFirst(AEATestCaseManyFlaky):
    """Test fetch command when registry fetch runs local only."""

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    @mock.patch("aea.cli.fetch.fetch_agent_remote")
    @mock.patch("aea.cli.fetch.fetch_agent_locally")
    def test_fetch_agent_from_local_registry_ok_remote_not_called(
        self, local_fetch: mock.Mock, remote_fetch: mock.Mock
    ):
        """Test fetch agent from Registry for positive result."""
        self.run_cli_command("fetch", "--mixed", str(MY_FIRST_AEA_PUBLIC_ID))
        local_fetch.assert_called()
        remote_fetch.assert_not_called()


class TestFetchLatestVersion(AEATestCaseMany):
    """Test case for fetch agent, latest version."""

    def test_fetch_agent_latest(self):
        """Test fetch agent, latest version."""
        self.run_cli_command(
            "fetch", "--local", str(MY_FIRST_AEA_PUBLIC_ID.to_latest())
        )
        assert "my_first_aea" in os.listdir(self.t)


class TestFetchAgentMixed(BaseAEATestCase):
    """Test 'aea fetch' in mixed mode."""

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    @pytest.mark.integration
    @mock.patch("aea.cli.fetch.fetch_agent_remote")
    @mock.patch(
        "aea.cli.add.find_item_locally_or_distributed",
        side_effect=click.ClickException(""),
    )
    @mock.patch(
        "aea.cli.fetch.fetch_agent_locally",
        side_effect=click.ClickException(""),
    )
    def test_fetch_mixed(
        self, _mock_fetch_locally, _mock_fetch_agent_locally, mock_fetch_package
    ) -> None:
        """Test fetch in mixed mode."""
        self.run_cli_command(
            "-v", "DEBUG", "fetch", "--mixed", str(MY_FIRST_AEA_PUBLIC_ID.to_latest())
        )
        mock_fetch_package.assert_called()


class BaseTestFetchAgentError(BaseAEATestCase, ABC):
    """Test 'aea fetch' in local, remote or mixed mode when it fails."""

    ERROR_MESSAGE = "some error."
    EXPECTED_ERROR_MESSAGE = ""
    MODE = ""

    def _mock_raise_click_exception(self, ctx: Context, *args, **kwargs):
        """Mock 'add_item' so to always fail."""
        raise click.ClickException(BaseTestFetchAgentError.ERROR_MESSAGE)

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    @pytest.mark.integration
    @mock.patch("aea.cli.fetch.add_item", side_effect=_mock_raise_click_exception)
    @mock.patch("aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_HTTP)
    @mock.patch(
        "aea.cli.fetch.fetch_agent_remote", side_effect=_mock_raise_click_exception
    )
    @mock.patch(
        "aea.cli.registry.fetch.add_item", side_effect=_mock_raise_click_exception
    )
    def test_fetch_negative(self, *_mocks) -> None:
        """Test fetch in mixed mode."""
        if type(self) == BaseTestFetchAgentError:
            pytest.skip("Base test class.")
        with pytest.raises(
            Exception,
            match=self.EXPECTED_ERROR_MESSAGE,
        ):
            self.run_cli_command(
                *(
                    ["-v", "DEBUG", "fetch", str(MY_FIRST_AEA_PUBLIC_ID.to_latest())]
                    + ([self.MODE] if self.MODE else [])
                )
            )


class TestFetchAgentNonMixedErrorLocal(BaseTestFetchAgentError):
    """Test 'aea fetch' in local mode when it fails."""

    EXPECTED_ERROR_MESSAGE = f".*{BaseTestFetchAgentError.ERROR_MESSAGE}"
    MODE = "--local"


class TestFetchAgentMixedModeError(BaseTestFetchAgentError):
    """Test 'aea fetch' in mixed mode when it fails."""

    EXPECTED_ERROR_MESSAGE = f".*{BaseTestFetchAgentError.ERROR_MESSAGE}"
    MODE = ""


class TestFetchAgentRemoteModeError(BaseTestFetchAgentError):
    """Test 'aea fetch' in remote mode when it fails."""

    EXPECTED_ERROR_MESSAGE = rf".*{BaseTestFetchAgentError.ERROR_MESSAGE}"
    MODE = "--remote"


class TestFetchIPFS(BaseAEATestCase):
    """Test fetching package from the IPFS registry."""

    dummy_id = (
        "valory/dummy_agent:bafybeic6plxxhcbokxlce3grbgsm247rgvcb5arwwslm5yv6pt46byr22a"
    )

    def test_run(self) -> None:
        """Test run."""

        with mock.patch(
            "aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_IPFS
        ), mock.patch.object(
            IPFSTool,
            "download",
            return_value=self.packages_dir_path
            / "open_aea"
            / "agents"
            / "my_first_aea",
        ), mock.patch(
            "aea.cli.fetch._fetch_agent_deps"
        ) as dep_patch, cd(
            self.t
        ):
            result = self.run_cli_command(
                "fetch",
                self.dummy_id,
                "--remote",
            )

            assert result.exit_code == 0
            dep_patch.assert_called_once()


class TestFetchIPFSFailures(BaseAEATestCase):
    """Test fetching package from the IPFS registry."""

    dummy_id = (
        "valory/dummy_agent:bafybeic6plxxhcbokxlce3grbgsm247rgvcb5arwwslm5yv6pt46byr22a"
    )

    def test_download_failure(self) -> None:
        """Test run."""

        with mock.patch(
            "aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_IPFS
        ), mock.patch.object(
            IPFSTool, "download", side_effect=DownloadError
        ), mock.patch.object(
            Path, "exists", return_value=False
        ):
            with pytest.raises(
                click.ClickException,
                match="Error occured while downloading agent",
            ):
                self.run_cli_command(
                    "fetch",
                    self.dummy_id,
                    "--remote",
                )

    def test_os_error(self) -> None:
        """Test run."""

        with mock.patch(
            "aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_IPFS
        ), mock.patch.object(IPFSTool, "download", side_effect=shutil.Error):
            with pytest.raises(
                click.ClickException,
            ):
                self.run_cli_command(
                    "fetch",
                    self.dummy_id,
                    "--remote",
                )

    @pytest.mark.skipif(
        condition=(sys.version_info.major <= 3 and sys.version_info.minor <= 7),
        reason="Needs investigation",
    )
    def test_not_an_agent_error(self) -> None:
        """Test run."""

        with TemporaryDirectory() as temp_dir:
            with mock.patch(
                "aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_IPFS
            ), mock.patch.object(IPFSTool, "download", return_value=temp_dir):
                with pytest.raises(ClickException, match="is not an agent package"):
                    self.run_cli_command(
                        "fetch",
                        self.dummy_id,
                        "--remote",
                    )


class TestFetchIPFSAlias(BaseAEATestCase):
    """Test fetching package from the IPFS registry."""

    dummy_id = (
        "valory/dummy_agent:bafybeic6plxxhcbokxlce3grbgsm247rgvcb5arwwslm5yv6pt46byr22a"
    )

    def test_alias(self) -> None:
        """Test run."""

        with mock.patch(
            "aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_IPFS
        ), mock.patch.object(
            IPFSTool,
            "download",
            return_value=self.packages_dir_path
            / "open_aea"
            / "agents"
            / "my_first_aea",
        ), mock.patch(
            "aea.cli.fetch._fetch_agent_deps"
        ) as dep_patch:
            result = self.run_cli_command(
                "fetch", self.dummy_id, "--remote", "--alias", "test_alias"
            )

            assert result.exit_code == 0
            assert (self.t / "test_alias").exists()
            dep_patch.assert_called_once()


def test_fetch_mixed_no_local_registry():
    """Test that mixed becomes remote when no local registry."""
    with TemporaryDirectory() as tmp_dir:
        with cd(tmp_dir):
            runner = CliRunner()
            with mock.patch(
                "aea.cli.fetch.fetch_agent_remote"
            ) as fetch_agent_remote_mock:
                result = runner.invoke(
                    cli,
                    ["fetch", "--mixed", "fetchai/my_first_aea"],
                    catch_exceptions=False,
                )
            assert result.exit_code == 0, result.stdout
            fetch_agent_remote_mock.assert_called_once()


def test_fetch_local_no_local_registry():
    """Test that local fetch fails when no local registry."""
    with TemporaryDirectory() as tmp_dir:
        with cd(tmp_dir):
            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["fetch", "--local", "fetchai/my_first_aea"],
                catch_exceptions=False,
            )
            assert result.exit_code == 1, result.stdout
            assert (
                "Registry path not provided and local registry `packages` not found in current (.) and parent directory."
                in result.stdout
            )


def test_fetch_twice_locally():
    """Test fails on fetch if dir exists."""
    with TemporaryDirectory() as tmp_dir:
        with cd(tmp_dir):
            name = "my_first_aea"
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "--registry-path",
                    PACKAGES_DIR,
                    "fetch",
                    "--local",
                    "fetchai/my_first_aea",
                ],
                catch_exceptions=False,
            )
            assert result.exit_code == 0, result.stdout
            assert os.path.exists(name)

            with pytest.raises(
                ClickException,
                match='Item "my_first_aea" already exists in target folder.',
            ):
                result = runner.invoke(
                    cli,
                    [
                        "--registry-path",
                        PACKAGES_DIR,
                        "fetch",
                        "--local",
                        "fetchai/my_first_aea",
                    ],
                    standalone_mode=False,
                    catch_exceptions=False,
                )


def test_fetch_twice_remote():
    """Test fails on fetch if dir exists."""
    with TemporaryDirectory() as tmp_dir:
        with cd(tmp_dir):
            name = "my_first_aea"
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "--registry-path",
                    PACKAGES_DIR,
                    "fetch",
                    "--local",
                    "fetchai/my_first_aea",
                ],
                catch_exceptions=False,
            )
            assert result.exit_code == 0, result.stdout
            assert os.path.exists(name)

            with pytest.raises(
                ClickException,
                match='Item "my_first_aea" already exists in target folder.',
            ):
                result = runner.invoke(
                    cli,
                    [
                        "--registry-path",
                        PACKAGES_DIR,
                        "fetch",
                        "--local",
                        "fetchai/my_first_aea",
                    ],
                    standalone_mode=False,
                    catch_exceptions=False,
                )
