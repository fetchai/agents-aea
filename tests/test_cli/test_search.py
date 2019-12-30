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
from pathlib import Path
from unittest import mock, TestCase

import jsonschema
from jsonschema import Draft4Validator

from aea import AEA_DIR
from aea.cli import cli
from tests.test_cli.constants import FORMAT_ITEMS_SAMPLE_OUTPUT
from ..common.click_testing import CliRunner
from ..conftest import AGENT_CONFIGURATION_SCHEMA, CONFIGURATION_SCHEMA_DIR, CLI_LOG_OPTION, ROOT_DIR


class TestSearchProtocols:
    """Test that the command 'aea search protocols' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
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


class TestSearchWithRegistryInSubfolder:
    """Test the search when the registry directory is a subfolder of the current path."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.runner = CliRunner()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        # copy the packages directory in the temporary test directory.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        # remove all the skills except the echo skill (to make testing easier).
        [shutil.rmtree(p) for p in Path(cls.t, "packages", "skills").iterdir() if p.name != "echo" and p.is_dir()]

        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "skills"], standalone_mode=False)

    def test_exit_code_equal_to_zero(self):
        """Test that the exit code is equal to 0 (i.e. success)."""
        assert self.result.exit_code == 0

    def test_correct_output(self,):
        """Test that the command has printed the correct output.."""
        assert self.result.output == "Available skills:\n" \
                                     "------------------------------\n" \
                                     "Public ID: fetchai/echo:0.1.0\n" \
                                     "Name: echo\n" \
                                     "Description: The echo skill implements simple echo functionality.\n" \
                                     "Author: fetchai\n" \
                                     "Version: 0.1.0\n" \
                                     "------------------------------\n" \
                                     "------------------------------\n" \
                                     "Public ID: fetchai/error:0.1.0\n" \
                                     "Name: error\n" \
                                     "Description: The error skill implements basic error handling required by all AEAs.\n" \
                                     "Author: fetchai\n" \
                                     "Version: 0.1.0\n" \
                                     "------------------------------\n\n"

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestSearchInAgentDirectory:
    """Test the search when we are in the agent directory."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.runner = CliRunner()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        # copy the packages directory in the temporary test directory.
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))

        # remove all the skills except the echo skill (to make testing easier).
        [shutil.rmtree(p) for p in Path(cls.t, "packages", "skills").iterdir() if p.name != "echo" and p.is_dir()]

        # create an AEA proejct and enter into it.
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", "myagent"], standalone_mode=False)
        assert result.exit_code == 0
        os.chdir(Path(cls.t, "myagent"))

        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "skills"], standalone_mode=False)

    def test_exit_code_equal_to_zero(self):
        """Test that the exit code is equal to 0 (i.e. success)."""
        assert self.result.exit_code == 0

    def test_correct_output(self,):
        """Test that the command has printed the correct output.."""
        assert self.result.output == "Available skills:\n" \
                                     "------------------------------\n" \
                                     "Public ID: fetchai/echo:0.1.0\n" \
                                     "Name: echo\n" \
                                     "Description: The echo skill implements simple echo functionality.\n" \
                                     "Author: fetchai\n" \
                                     "Version: 0.1.0\n" \
                                     "------------------------------\n" \
                                     "------------------------------\n" \
                                     "Public ID: fetchai/error:0.1.0\n" \
                                     "Name: error\n" \
                                     "Description: The error skill implements basic error handling required by all AEAs.\n" \
                                     "Author: fetchai\n" \
                                     "Version: 0.1.0\n" \
                                     "------------------------------\n\n"

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
