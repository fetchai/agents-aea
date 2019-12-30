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

"""This test module contains the tests for the `aea search` sub-command."""
import json
import os
import shutil
import tempfile
from unittest import mock, TestCase
from pathlib import Path

import jsonschema
from ..common.click_testing import CliRunner
from jsonschema import Draft4Validator

from aea import AEA_DIR
from aea.cli import cli
from ..conftest import AGENT_CONFIGURATION_SCHEMA, CONFIGURATION_SCHEMA_DIR, CLI_LOG_OPTION
from tests.test_cli.constants import FORMAT_ITEMS_SAMPLE_OUTPUT


class TestSearchProtocols:
    """Test that the command 'aea search protocols' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver("file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema)
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.cwd = os.getcwd()
        cls.runner = CliRunner()

    @mock.patch('aea.cli.search.format_items', return_value=FORMAT_ITEMS_SAMPLE_OUTPUT)
    def test_correct_output_default_registry(self, _):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "protocols"], standalone_mode=False)
        assert self.result.output == "Available protocols:\n{}\n".format(FORMAT_ITEMS_SAMPLE_OUTPUT)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)


class TestSearchConnections:
    """Test that the command 'aea search connections' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver("file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema)
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.cwd = os.getcwd()
        cls.runner = CliRunner()

    @mock.patch(
        'aea.cli.search.format_items',
        return_value=FORMAT_ITEMS_SAMPLE_OUTPUT
    )
    def test_correct_output_default_registry(self, _):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "connections"], standalone_mode=False)
        assert self.result.output == "Available connections:\n{}\n".format(
            FORMAT_ITEMS_SAMPLE_OUTPUT
        )

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)


class TestSearchSkills:
    """Test that the command 'aea search skills' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver("file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema)
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.cwd = os.getcwd()
        cls.runner = CliRunner()

    @mock.patch(
        'aea.cli.search.format_items',
        return_value=FORMAT_ITEMS_SAMPLE_OUTPUT
    )
    def test_correct_output_default_registry(self, _):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "skills"], standalone_mode=False)
        assert self.result.output == "Available skills:\n{}\n".format(FORMAT_ITEMS_SAMPLE_OUTPUT)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)


class TestSearchWithCustomLocalRegistry:
    """Test that the command 'aea search --local-registry-path' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver("file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema)
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.cwd = os.getcwd()
        cls.runner = CliRunner()

        # copy packages into another folder.
        cls.t = tempfile.mkdtemp()
        shutil.copytree("packages/", Path(cls.t, "new_packages"))

    @mock.patch(
        'aea.cli.search.format_items',
        return_value=FORMAT_ITEMS_SAMPLE_OUTPUT
    )
    def test_correct_output_default_registry(self, _):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        result = self.runner.invoke(cli,
                                    [
                                        *CLI_LOG_OPTION,
                                        "search",
                                        "--local-registry-dir",
                                        os.path.join(self.t, "new_packages"),
                                        "skills"],
                                    standalone_mode=False)
        assert result.output == "Available skills:\n{}\n".format(FORMAT_ITEMS_SAMPLE_OUTPUT)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)


@mock.patch(
    'aea.cli.search.request_api',
    return_value=['correct', 'results']
)
@mock.patch(
    'aea.cli.search.format_items',
    return_value=FORMAT_ITEMS_SAMPLE_OUTPUT
)
class RegistrySearchTestCase(TestCase):
    """Test case for search --registry CLI command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_search_connections_positive(
        self, format_items_mock, request_api_mock
    ):
        """Test for CLI search --registry connections positive result."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "search",
                "--registry",
                "connections",
                "--query=some"
            ],
            standalone_mode=False
        )
        expected_output = (
            'Searching for "some"...\n'
            'Connections found:\n\n'
            '{}\n'.format(FORMAT_ITEMS_SAMPLE_OUTPUT)
        )
        self.assertEqual(result.output, expected_output)
        request_api_mock.assert_called_once_with(
            'GET', '/connections', params={'search': 'some'}
        )
        format_items_mock.assert_called_once_with(['correct', 'results'])

    def test_search_protocols_positive(
        self, format_items_mock, request_api_mock
    ):
        """Test for CLI search --registry protocols positive result."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "search",
                "--registry",
                "protocols",
                "--query=some"
            ],
            standalone_mode=False
        )
        expected_output = (
            'Searching for "some"...\n'
            'Protocols found:\n\n'
            '{}\n'.format(FORMAT_ITEMS_SAMPLE_OUTPUT)
        )
        self.assertEqual(result.output, expected_output)
        request_api_mock.assert_called_once_with(
            'GET', '/protocols', params={'search': 'some'}
        )
        format_items_mock.assert_called_once_with(['correct', 'results'])

    @mock.patch(
        'aea.cli.search.format_skills',
        return_value=FORMAT_ITEMS_SAMPLE_OUTPUT
    )
    def test_search_skills_positive(
        self, format_skills_mock, format_items_mock, request_api_mock
    ):
        """Test for CLI search --registry skills positive result."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "search",
                "--registry",
                "skills",
                "--query=some"
            ],
            standalone_mode=False
        )
        expected_output = (
            'Searching for "some"...\n'
            'Skills found:\n\n'
            '{}\n'.format(FORMAT_ITEMS_SAMPLE_OUTPUT)
        )
        self.assertEqual(result.output, expected_output)
        request_api_mock.assert_called_once_with(
            'GET', '/skills', params={'search': 'some'}
        )
        format_skills_mock.assert_called_once_with(['correct', 'results'])
        format_items_mock.assert_not_called()
