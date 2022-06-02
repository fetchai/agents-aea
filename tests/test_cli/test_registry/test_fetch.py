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
"""This test module contains the tests for CLI Registry fetch methods."""

import os
import shutil
import tempfile
from unittest import TestCase, mock

from click import ClickException

from aea.cli.registry.fetch import fetch_agent

from tests.test_cli.tools_for_testing import ContextMock, PublicIdMock


def _raise_exception():
    raise Exception()


@mock.patch("aea.cli.registry.fetch.open_file", mock.mock_open())
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
