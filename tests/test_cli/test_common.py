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

"""This test module contains the tests for cli.common module."""

from builtins import FileNotFoundError
from unittest import TestCase, mock

from click import ClickException

from yaml import YAMLError

from aea.cli.common import (
    AUTHOR,
    # AEAConfigException,
    PublicIdParameter,
    _format_items,
    _get_or_create_cli_config,
    _init_cli_config,
    _try_get_item_source_path,
    _try_get_item_target_path,
    _update_cli_config,
)


class FormatItemsTestCase(TestCase):
    """Test case for format_items method."""

    def test_format_items_positive(self):
        """Test format_items positive result."""
        items = [
            {
                "public_id": "author/name:version",
                "name": "obj-name",
                "description": "Some description",
                "author": "author",
                "version": "1.0",
            }
        ]
        result = _format_items(items)
        expected_result = (
            "------------------------------\n"
            "Public ID: author/name:version\n"
            "Name: obj-name\n"
            "Description: Some description\n"
            "Author: author\n"
            "Version: 1.0\n"
            "------------------------------\n"
        )
        self.assertEqual(result, expected_result)


@mock.patch("aea.cli.common.os.path.join", return_value="some-path")
class TryGetItemSourcePathTestCase(TestCase):
    """Test case for try_get_item_source_path method."""

    @mock.patch("aea.cli.common.os.path.exists", return_value=True)
    def test_get_item_source_path_positive(self, exists_mock, join_mock):
        """Test for get_item_source_path positive result."""
        result = _try_get_item_source_path("cwd", AUTHOR, "skills", "skill-name")
        expected_result = "some-path"
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with("cwd", AUTHOR, "skills", "skill-name")
        exists_mock.assert_called_once_with("some-path")

    @mock.patch("aea.cli.common.os.path.exists", return_value=False)
    def test_get_item_source_path_not_exists(self, exists_mock, join_mock):
        """Test for get_item_source_path item already exists."""
        with self.assertRaises(ClickException):
            _try_get_item_source_path("cwd", AUTHOR, "skills", "skill-name")


@mock.patch("aea.cli.common.os.path.join", return_value="some-path")
class TryGetItemTargetPathTestCase(TestCase):
    """Test case for try_get_item_target_path method."""

    @mock.patch("aea.cli.common.os.path.exists", return_value=False)
    def test_get_item_target_path_positive(self, exists_mock, join_mock):
        """Test for get_item_source_path positive result."""
        result = _try_get_item_target_path("packages", AUTHOR, "skills", "skill-name")
        expected_result = "some-path"
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with("packages", AUTHOR, "skills", "skill-name")
        exists_mock.assert_called_once_with("some-path")

    @mock.patch("aea.cli.common.os.path.exists", return_value=True)
    def test_get_item_target_path_already_exists(self, exists_mock, join_mock):
        """Test for get_item_target_path item already exists."""
        with self.assertRaises(ClickException):
            _try_get_item_target_path("skills", AUTHOR, "skill-name", "packages_path")


class PublicIdParameterTestCase(TestCase):
    """Test case for PublicIdParameter class."""

    def test_get_metavar_positive(self):
        """Test for get_metavar positive result."""
        result = PublicIdParameter.get_metavar("obj", "param")
        expected_result = "PUBLIC_ID"
        self.assertEqual(result, expected_result)


@mock.patch("aea.cli.common.os.path.dirname", return_value="dir-name")
@mock.patch("aea.cli.common.os.path.exists", return_value=False)
@mock.patch("aea.cli.common.os.makedirs")
class InitConfigFolderTestCase(TestCase):
    """Test case for _init_cli_config method."""

    def test_init_cli_config_positive(self, makedirs_mock, exists_mock, dirname_mock):
        """Test for _init_cli_config method positive result."""
        _init_cli_config()
        dirname_mock.assert_called_once()
        exists_mock.assert_called_once_with("dir-name")
        makedirs_mock.assert_called_once_with("dir-name")


@mock.patch("aea.cli.common._get_or_create_cli_config")
@mock.patch("aea.cli.common.yaml.dump")
@mock.patch("builtins.open", mock.mock_open())
class UpdateCLIConfigTestCase(TestCase):
    """Test case for _update_cli_config method."""

    def test_update_cli_config_positive(self, dump_mock, icf_mock):
        """Test for _update_cli_config method positive result."""
        _update_cli_config({"some": "config"})
        icf_mock.assert_called_once()
        dump_mock.assert_called_once()


def _raise_yamlerror(*args):
    raise YAMLError()


def _raise_file_not_found_error(*args):
    raise FileNotFoundError()


@mock.patch("builtins.open", mock.mock_open())
class GetOrCreateCLIConfigTestCase(TestCase):
    """Test case for read_cli_config method."""

    @mock.patch("aea.cli.common.yaml.safe_load", return_value={"correct": "output"})
    def test_get_or_create_cli_config_positive(self, safe_load_mock):
        """Test for _get_or_create_cli_config method positive result."""
        result = _get_or_create_cli_config()
        expected_result = {"correct": "output"}
        self.assertEqual(result, expected_result)
        safe_load_mock.assert_called_once()

    @mock.patch("aea.cli.common.yaml.safe_load", _raise_yamlerror)
    def test_get_or_create_cli_config_bad_yaml(self):
        """Test for r_get_or_create_cli_config method bad yaml behavior."""
        with self.assertRaises(ClickException):
            _get_or_create_cli_config()

    # @mock.patch("aea.cli.common.yaml.safe_load", _raise_file_not_found_error)
    # def test_get_or_create_cli_config_file_not_found(self):
    #     """Test for read_cli_config method bad yaml behavior."""
    #     with self.assertRaises(AEAConfigException):
    #         _get_or_create_cli_config()
