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
"""This test module contains the tests for CLI Registry fetch methods."""

import os
import shutil
import tempfile
from abc import ABC
from unittest import TestCase, mock

import click
import pytest
from click import ClickException

from aea.cli.add import add_item
from aea.cli.registry.add import fetch_package
from aea.cli.registry.fetch import fetch_agent
from aea.cli.utils.context import Context
from aea.test_tools.test_cases import BaseAEATestCase

from tests.test_cli.tools_for_testing import ContextMock, PublicIdMock


def _raise_exception():
    raise Exception()


@mock.patch("builtins.open", mock.mock_open())
@mock.patch("aea.cli.utils.decorators._cast_ctx")
@mock.patch("aea.cli.registry.fetch.PublicId", PublicIdMock)
@mock.patch("aea.cli.registry.fetch.os.rename")
@mock.patch("aea.cli.registry.fetch.os.makedirs")
@mock.patch("aea.cli.registry.fetch.try_to_load_agent_config")
@mock.patch("aea.cli.registry.fetch.download_file", return_value="filepath")
@mock.patch("aea.cli.registry.fetch.extract")
class TestFetchAgent(TestCase):
    """Test case for fetch_package method."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    @mock.patch(
        "aea.cli.registry.fetch.request_api",
        return_value={
            "file": "url",
            "connections": [],
            "contracts": [],
            "protocols": [],
            "skills": [],
        },
    )
    def test_fetch_agent_positive(
        self, request_api_mock, extract_mock, download_file_mock, *mocks
    ):
        """Test for fetch_agent method positive result."""
        public_id_mock = PublicIdMock()
        fetch_agent(ContextMock(), public_id_mock, alias="alias")
        request_api_mock.assert_called_with(
            "GET",
            "/agents/{}/{}/{}".format(
                public_id_mock.author, public_id_mock.name, public_id_mock.version
            ),
        )
        download_file_mock.assert_called_once_with("url", "cwd")
        extract_mock.assert_called_once_with("filepath", "cwd")

    @mock.patch("aea.cli.registry.fetch.add_item")
    @mock.patch(
        "aea.cli.registry.fetch.request_api",
        return_value={
            "file": "url",
            "connections": ["public/id:{}".format(PublicIdMock.DEFAULT_VERSION)],
            "contracts": ["public/id:{}".format(PublicIdMock.DEFAULT_VERSION)],
            "protocols": ["public/id:{}".format(PublicIdMock.DEFAULT_VERSION)],
            "skills": ["public/id:{}".format(PublicIdMock.DEFAULT_VERSION)],
        },
    )
    def test_fetch_agent_with_dependencies_positive(
        self, request_api_mock, add_item_mock, extract_mock, download_file_mock, *mocks
    ):
        """Test for fetch_agent method with dependencies positive result."""
        public_id_mock = PublicIdMock()
        ctx_mock = ContextMock(
            connections=["public/id:{}".format(PublicIdMock.DEFAULT_VERSION)]
        )
        fetch_agent(ctx_mock, public_id_mock)
        request_api_mock.assert_called_with(
            "GET",
            "/agents/{}/{}/{}".format(
                public_id_mock.author, public_id_mock.name, public_id_mock.version
            ),
        )
        download_file_mock.assert_called_once_with("url", "cwd")
        extract_mock.assert_called_once_with("filepath", "cwd")
        add_item_mock.assert_called()

    @mock.patch("aea.cli.registry.fetch.add_item", _raise_exception)
    @mock.patch(
        "aea.cli.registry.fetch.request_api",
        return_value={
            "file": "url",
            "connections": ["public/id:{}".format(PublicIdMock.DEFAULT_VERSION)],
            "contracts": [],
            "protocols": [],
            "skills": [],
        },
    )
    def test_fetch_agent_with_dependencies_unable_to_fetch(self, *mocks):
        """Test for fetch_agent method unable to fetch."""
        ctx_mock = ContextMock(
            connections=["public/id:{}".format(PublicIdMock.DEFAULT_VERSION)]
        )
        with self.assertRaises(ClickException):
            fetch_agent(ctx_mock, PublicIdMock())

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestFetchAgentMixed(BaseAEATestCase):
    """Test 'aea fetch' in --mixed mode."""

    @staticmethod
    def _mock_add_item(ctx: Context, *args, **kwargs):
        """
        Mock 'add_item'.

        Make add_item to fail only when is in local mode.
        """
        if ctx.config["is_local"]:
            raise click.ClickException("some error.")
        return add_item(ctx, *args, **kwargs)

    @pytest.mark.integration
    @mock.patch("aea.cli.fetch.add_item")
    @mock.patch("aea.cli.add.fetch_package", side_effect=fetch_package)
    def test_fetch_mixed(self, mock_fetch_package, mock_add_item) -> None:
        """Test fetch in mixed mode."""
        mock_add_item.side_effect = self._mock_add_item
        self.run_cli_command("-v", "DEBUG", "fetch", "fetchai/my_first_aea", "--mixed")
        mock_fetch_package.assert_called()


class BaseTestFetchAgentError(BaseAEATestCase, ABC):
    """Test 'aea fetch' in --local or --mixed mode when it fails."""

    EXPECTED_ERROR_MESSAGE = "some error."
    MODE = ""

    @staticmethod
    def _mock_add_item(ctx: Context, *args, **kwargs):
        """Mock 'add_item' so to always fail."""
        raise click.ClickException(BaseTestFetchAgentError.EXPECTED_ERROR_MESSAGE)

    @pytest.mark.integration
    @mock.patch("aea.cli.fetch.add_item")
    def test_fetch_mixed(self, mock_add_item) -> None:
        """Test fetch in mixed mode."""
        if not self.MODE:
            pytest.skip("Base test class.")
        mock_add_item.side_effect = self._mock_add_item
        with pytest.raises(
            Exception,
            match=f"Failed to add .* dependency.*: {self.EXPECTED_ERROR_MESSAGE}",
        ):
            self.run_cli_command(
                "-v", "DEBUG", "fetch", "fetchai/my_first_aea", self.MODE
            )


class TestFetchAgentNonMixedErrorLocal(BaseTestFetchAgentError):
    """Test 'aea fetch' in --local or --mixed mode when it fails."""

    MODE = "--local"


class TestFetchAgentNonMixedErrorMixed(BaseTestFetchAgentError):
    """Test 'aea fetch' in --local or --mixed mode when it fails."""

    MODE = "--mixed"
