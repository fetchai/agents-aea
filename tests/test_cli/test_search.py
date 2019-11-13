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
from unittest import mock
from pathlib import Path

import jsonschema
from click.testing import CliRunner
from jsonschema import Draft4Validator

from aea import AEA_DIR
from aea.cli import cli
from tests.conftest import AGENT_CONFIGURATION_SCHEMA, CONFIGURATION_SCHEMA_DIR, CLI_LOG_OPTION


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

    def test_correct_output_default_registry(self):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "protocols"])
        expected_output = "Available protocols:\n- " + "\n- ".join(["default", "fipa", "gym", "oef", "tac"]) + "\n"
        assert self.result.output == expected_output

    def test_correct_output_custom_registry(self):
        """Test that the command has printed the correct output when using a custom registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "protocols"])
        expected_output = "Available protocols:\n- " + "\n- ".join(["default", "fipa", "gym", "oef", "tac"]) + "\n"
        assert self.result.output == expected_output

    def test_correct_output_registry_api(self):
        """Test that the command has printed the correct output when using Registry API."""
        resp = [
            {
                "name": "protocol-1",
                "description": "Protocol 1",
                "version": "1",
            },
            {
                "name": "protocol-2",
                "description": "Protocol 2",
                "version": "2",
            }
        ]
        with mock.patch('aea.cli.registry.utils.request_api', return_value=resp):
            self.result = self.runner.invoke(
                cli, [*CLI_LOG_OPTION, "search", "--registry", "protocols", "--query=1"]
            )
        expected_output = "any"
        # for some reason self.result.output equals only the first line of output
        assert self.result.output == expected_output

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
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

    def test_correct_output_default_registry(self):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "connections"])
        expected_output = "Available connections:\n- " + "\n- ".join(["gym", "local", "oef", "stub"]) + "\n"
        assert self.result.output == expected_output

    def test_correct_output_custom_registry(self):
        """Test that the command has printed the correct output when using a custom registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "connections"])
        expected_output = "Available connections:\n- " + "\n- ".join(["gym", "local", "oef", "stub"]) + "\n"
        assert self.result.output == expected_output

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
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

    def test_correct_output_default_registry(self):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "skills"])
        expected_output = """Available skills:
- carpark_client
- carpark_detection
- echo
- error
- fipa_negotiation
- gym
- tac
- weather_client
- weather_client_ledger
- weather_station
- weather_station_ledger
"""
        assert self.result.output == expected_output

    def test_correct_output_custom_registry(self):
        """Test that the command has printed the correct output when using a custom registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "skills"])
        expected_output = """Available skills:
- carpark_client
- carpark_detection
- echo
- error
- fipa_negotiation
- gym
- tac
- weather_client
- weather_client_ledger
- weather_station
- weather_station_ledger
"""
        assert self.result.output == expected_output

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
