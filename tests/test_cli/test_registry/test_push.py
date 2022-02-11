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
"""Test module for Registry push methods."""
import os
from unittest import TestCase, mock
from unittest.mock import mock_open, patch

import pytest
from click import ClickException

from aea.cli.registry.push import (
    _compress_dir,
    _remove_pycache,
    check_package_public_id,
    push_item,
)
from aea.configurations.base import PublicId

from tests.test_cli.tools_for_testing import ContextMock, PublicIdMock


@mock.patch("builtins.open", mock_open(read_data="opened_file"))
@mock.patch("aea.cli.registry.push.check_is_author_logged_in")
@mock.patch("aea.cli.registry.push.list_missing_packages", return_value=[])
@mock.patch("aea.cli.registry.utils._rm_tarfiles")
@mock.patch("aea.cli.registry.push.os.getcwd", return_value="cwd")
@mock.patch("aea.cli.registry.push._compress_dir")
@mock.patch(
    "aea.cli.registry.push.load_yaml",
    return_value={
        "description": "some-description",
        "version": PublicIdMock.DEFAULT_VERSION,
        "author": "some_author",
        "name": "some_name",
        "protocols": ["some/protocol:0.1.2"],
    },
)
@mock.patch(
    "aea.cli.registry.push.request_api", return_value={"public_id": "public-id"}
)
class PushItemTestCase(TestCase):
    """Test case for push_item method."""

    @mock.patch("aea.cli.registry.push.os.path.exists", return_value=True)
    @mock.patch("aea.cli.registry.push.is_readme_present", return_value=True)
    def test_push_item_positive(
        self,
        is_readme_present_mock,
        path_exists_mock,
        request_api_mock,
        load_yaml_mock,
        compress_mock,
        getcwd_mock,
        rm_tarfiles_mock,
        check_is_author_logged_in_mock,
        *_
    ):
        """Test for push_item positive result."""
        public_id = PublicIdMock(
            name="some_name",
            author="some_author",
            version="{}".format(PublicIdMock.DEFAULT_VERSION),
        )
        push_item(ContextMock(), "some-type", public_id)
        request_api_mock.assert_called_once_with(
            "POST",
            "/some-types/create",
            data={
                "name": "some_name",
                "description": "some-description",
                "version": PublicIdMock.DEFAULT_VERSION,
                "protocols": ["some/protocol:0.1.2"],
            },
            is_auth=True,
            files={"file": open("file.1"), "readme": open("file.2")},
        )

    @mock.patch("aea.cli.registry.push.os.path.exists", return_value=True)
    @mock.patch("aea.cli.registry.push.is_readme_present", return_value=True)
    def test_push_dependency_fail(
        self,
        is_readme_present_mock,
        path_exists_mock,
        request_api_mock,
        load_yaml_mock,
        compress_mock,
        getcwd_mock,
        rm_tarfiles_mock,
        check_is_author_logged_in_mock,
        *_
    ):
        """Test for push_item fails cause dependencies check."""
        public_id = PublicIdMock(
            name="some_name",
            author="some_author",
            version="{}".format(PublicIdMock.DEFAULT_VERSION),
        )

        with patch(
            "aea.cli.registry.push.list_missing_packages",
            return_value=[("some", PublicId.from_str("some/pack:0.1.0"))],
        ):
            with pytest.raises(
                ClickException, match="Found missing dependencies! Push canceled!"
            ):
                push_item(ContextMock(), "some-type", public_id)

    @mock.patch("aea.cli.registry.push.os.path.exists", return_value=True)
    @mock.patch("aea.cli.registry.push.is_readme_present", return_value=False)
    def test_push_item_positive_without_readme(
        self, is_readme_present_mock, path_exists_mock, request_api_mock, *mocks
    ):
        """Test for push_item without readme positive result."""
        public_id = PublicIdMock(
            name="some_name",
            author="some_author",
            version="{}".format(PublicIdMock.DEFAULT_VERSION),
        )
        push_item(ContextMock(), "some-type", public_id)
        request_api_mock.assert_called_once_with(
            "POST",
            "/some-types/create",
            data={
                "name": "some_name",
                "description": "some-description",
                "version": PublicIdMock.DEFAULT_VERSION,
                "protocols": ["some/protocol:0.1.2"],
            },
            is_auth=True,
            files={"file": open("opened_file", "r")},
        )

    @mock.patch("aea.cli.registry.push.os.path.exists", return_value=False)
    def test_push_item_item_not_found(
        self,
        path_exists_mock,
        request_api_mock,
        load_yaml_mock,
        compress_mock,
        getcwd_mock,
        rm_tarfiles_mock,
        check_is_author_logged_in_mock,
        *_
    ):
        """Test for push_item - item not found."""
        with self.assertRaises(ClickException):
            push_item(ContextMock(), "some-type", PublicIdMock())

        request_api_mock.assert_not_called()


@mock.patch("aea.cli.registry.push.shutil.rmtree")
class RemovePycacheTestCase(TestCase):
    """Test case for _remove_pycache method."""

    @mock.patch("aea.cli.registry.push.os.path.exists", return_value=True)
    def test_remove_pycache_positive(self, path_exists_mock, rmtree_mock):
        """Test for _remove_pycache positive result."""
        source_dir = "somedir"
        pycache_path = os.path.join(source_dir, "__pycache__")

        _remove_pycache(source_dir)
        rmtree_mock.assert_called_once_with(pycache_path)

    @mock.patch("aea.cli.registry.push.os.path.exists", return_value=False)
    def test_remove_pycache_no_pycache(self, path_exists_mock, rmtree_mock):
        """Test for _remove_pycache if there's no pycache."""
        source_dir = "somedir"
        _remove_pycache(source_dir)
        rmtree_mock.assert_not_called()


@mock.patch("aea.cli.registry.push.tarfile")
@mock.patch("aea.cli.registry.push._remove_pycache")
class CompressDirTestCase(TestCase):
    """Test case for _compress_dir method."""

    def test__compress_dir_positive(self, _remove_pycache_mock, tarfile_mock):
        """Test for _compress_dir positive result."""
        tar_obj_mock = mock.MagicMock()
        open_mock = mock.MagicMock(return_value=tar_obj_mock)
        tarfile_mock.open = open_mock

        _compress_dir("output_filename", "source_dir")
        _remove_pycache_mock.assert_called_once_with("source_dir")
        open_mock.assert_called_once_with("output_filename", "w:gz")


def test_check_package_public_id():
    """Test check_package_public_id."""
    public_id = PublicId("test", "test", "10.0.1")

    with mock.patch(
        "aea.cli.registry.push.load_component_public_id", return_value=public_id
    ):
        check_package_public_id(mock.Mock(), mock.Mock(), public_id)

    with mock.patch(
        "aea.cli.registry.push.load_component_public_id", return_value=public_id
    ):
        with pytest.raises(
            ClickException, match="Version, name or author does not match"
        ):
            check_package_public_id(
                mock.Mock(), mock.Mock(), PublicId("test", "test", "10.0.2")
            )
