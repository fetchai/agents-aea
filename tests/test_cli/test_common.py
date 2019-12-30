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
from unittest import TestCase

from aea.cli.common import format_items, format_skills


class FormatItemsTestCase(TestCase):
    """Test case for format_items method."""

    def test_format_items_positive(self):
        """Test format_items positive result."""
        items = [
            {
                'public_id': 'owner/name:version',
                'name': 'obj-name',
                'description': 'Some description',
                'author': 'owner',
                'version': '1.0'
            }
        ]
        result = format_items(items)
        expected_result = (
            '------------------------------\n'
            'Public ID: owner/name:version\n'
            'Name: obj-name\n'
            'Description: Some description\n'
            'Author: owner\n',
            'Version: 1.0\n'
            '------------------------------\n'
        )
        self.assertEqual(result, expected_result)


class FormatSkillsTestCase(TestCase):
    """Test case for format_skills method."""

    def test_format_skills_positive(self):
        """Test format_skills positive result."""
        items = [
            {
                'public_id': 'owner/name:version',
                'name': 'obj-name',
                'description': 'Some description',
                'version': '1.0',
                'protocol_names': ['p1', 'p2', 'p3']
            }
        ]
        result = format_skills(items)
        expected_result = (
            '------------------------------\n'
            'Public ID: owner/name:version\n'
            'Name: obj-name\n'
            'Description: Some description\n'
            'Protocols: p1 | p2 | p3 | \n'
            'Version: 1.0\n'
            '------------------------------\n'
        )
        self.assertEqual(result, expected_result)
