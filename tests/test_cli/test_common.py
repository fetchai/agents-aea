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

from unittest import TestCase, mock

from click import ClickException

from aea.cli.common import (
    PublicIdParameter,
    _format_items,
    _format_skills,
    _try_get_item_source_path,
    _try_get_vendorized_item_target_path,
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


class FormatSkillsTestCase(TestCase):
    """Test case for format_skills method."""

    def test_format_skills_positive(self):
        """Test format_skills positive result."""
        items = [
            {
                "public_id": "author/name:version",
                "name": "obj-name",
                "description": "Some description",
                "version": "1.0",
                "protocol_names": ["p1", "p2", "p3"],
            }
        ]
        result = _format_skills(items)
        expected_result = (
            "------------------------------\n"
            "Public ID: author/name:version\n"
            "Name: obj-name\n"
            "Description: Some description\n"
            "Protocols: p1 | p2 | p3 | \n"
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
        result = _try_get_item_source_path("cwd", "author", "skills", "skill-name")
        expected_result = "some-path"
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with("cwd", "author", "skills", "skill-name")
        exists_mock.assert_called_once_with("some-path")

    @mock.patch("aea.cli.common.os.path.exists", return_value=False)
    def test_get_item_source_path_not_exists(self, exists_mock, join_mock):
        """Test for get_item_source_path item already exists."""
        with self.assertRaises(ClickException):
            _try_get_item_source_path("cwd", "author", "skills", "skill-name")


@mock.patch("aea.cli.common.os.path.join", return_value="some-path")
class TryGetItemTargetPathTestCase(TestCase):
    """Test case for try_get_vendorized_item_target_path method."""

    @mock.patch("aea.cli.common.os.path.exists", return_value=False)
    def test_get_item_target_path_positive(self, exists_mock, join_mock):
        """Test for get_item_source_path positive result."""
        result = _try_get_vendorized_item_target_path(
            "packages", "author", "skills", "skill-name"
        )
        expected_result = "some-path"
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with(
            "packages", "vendor", "author", "skills", "skill-name"
        )
        exists_mock.assert_called_once_with("some-path")

    @mock.patch("aea.cli.common.os.path.exists", return_value=True)
    def test_get_item_target_path_already_exists(self, exists_mock, join_mock):
        """Test for get_item_target_path item already exists."""
        with self.assertRaises(ClickException):
            _try_get_vendorized_item_target_path(
                "skills", "author", "skill-name", "packages_path"
            )


class PublicIdParameterTestCase(TestCase):
    """Test case for PublicIdParameter class."""

    def test_get_metavar_positive(self):
        """Test for get_metavar positive result."""
        result = PublicIdParameter.get_metavar("obj", "param")
        expected_result = "PUBLIC_ID"
        self.assertEqual(result, expected_result)
