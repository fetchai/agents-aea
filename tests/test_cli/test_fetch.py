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
"""This test module contains the tests for CLI Registry fetch methods."""
import os
from abc import ABC
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

import click
import pytest
from click import ClickException

import aea
from aea.cli import cli
from aea.cli.fetch import _is_version_correct, fetch_agent_locally
from aea.cli.registry.settings import REMOTE_HTTP
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


@mock.patch("aea.cli.fetch.fetch_agent")
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


@pytest.mark.skip  # need remote registry
class TestFetchFromRemoteRegistry(AEATestCaseManyFlaky):
    """Test case for fetch agent command from Registry."""

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_fetch_agent_from_remote_registry_positive(self):
        """Test fetch agent from Registry for positive result."""
        self.run_cli_command(
            "fetch", str(MY_FIRST_AEA_PUBLIC_ID.to_latest()), "--remote"
        )
        assert "my_first_aea" in os.listdir(self.t)


class TestFetchMixedModeFallsBackCorrectly(AEATestCaseManyFlaky):
    """Test fetch command when registry fetch fails falls back to local fetch."""

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    @mock.patch("aea.cli.fetch.fetch_agent", side_effect=ClickException(""))
    @mock.patch("aea.cli.fetch.fetch_agent_locally", wraps=fetch_agent_locally)
    def test_fetch_agent_from_remote_registry_falls_back_to_local(
        self, local_fetch, _remote_fetch
    ):
        """Test fetch agent from Registry for positive result."""
        self.run_cli_command("fetch", str(MY_FIRST_AEA_PUBLIC_ID))
        local_fetch.assert_called()
        assert "my_first_aea" in os.listdir(self.t)


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

    @pytest.mark.skip  # need remote registry
    @pytest.mark.integration
    @mock.patch(
        "aea.cli.registry.add.fetch_package", wraps=aea.cli.registry.add.fetch_package
    )
    @mock.patch(
        "aea.cli.add.find_item_locally_or_distributed",
        side_effect=click.ClickException(""),
    )
    @mock.patch(
        "aea.cli.fetch.fetch_agent_locally",
        side_effect=click.ClickException(""),
    )
    def test_fetch_mixed(
        self, mock_fetch_package, _mock_fetch_locally, _mock_fetch_agent_locally
    ) -> None:
        """Test fetch in mixed mode."""
        self.run_cli_command(
            "-v", "DEBUG", "fetch", str(MY_FIRST_AEA_PUBLIC_ID.to_latest())
        )
        assert "my_first_aea" in os.listdir(self.t)
        mock_fetch_package.assert_called()


class BaseTestFetchAgentError(BaseAEATestCase, ABC):
    """Test 'aea fetch' in local, remote or mixed mode when it fails."""

    ERROR_MESSAGE = "some error."
    EXPECTED_ERROR_MESSAGE = ""
    MODE = ""

    def _mock_raise_click_exception(self, ctx: Context, *args, **kwargs):
        """Mock 'add_item' so to always fail."""
        raise click.ClickException(BaseTestFetchAgentError.ERROR_MESSAGE)

    @pytest.mark.integration
    @mock.patch("aea.cli.fetch.add_item", side_effect=_mock_raise_click_exception)
    @mock.patch("aea.cli.fetch.get_default_remote_registry", return_value=REMOTE_HTTP)
    @mock.patch("aea.cli.fetch.fetch_agent", side_effect=_mock_raise_click_exception)
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


@pytest.mark.skip  # need remote registry
def test_fetch_mixed_no_local_registry():
    """Test that mixed becomes remote when no local registry."""
    with TemporaryDirectory() as tmp_dir:
        with cd(tmp_dir):
            name = "my_first_aea"
            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["fetch", "fetchai/my_first_aea"],
                catch_exceptions=False,
            )
            assert result.exit_code == 0, result.stdout
            assert os.path.exists(name)
            assert "Trying remote registry (`--remote`)." in result.stdout


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
