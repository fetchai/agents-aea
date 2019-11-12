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
from pathlib import Path

import jsonschema
from click.testing import CliRunner
from jsonschema import Draft4Validator

from aea import AEA_DIR
from aea.cli import cli
from aea.cli.common import DEFAULT_REGISTRY_PATH
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

    def _generated_expected_output(self):
        expected_output = "Available protocols:\n"
        expected_output += "default\t[The default protocol allows for any bytes message.]\n"
        expected_output += "fipa\t[The fipa protocol implements the FIPA ACL.]\n"
        expected_output += "gym\t[The gym protocol implements the messages an agent needs to engage with a gym connection.]\n"
        expected_output += "oef\t[The oef protocol implements the OEF specific messages.]\n"
        expected_output += "scaffold\t[The scaffold protocol scaffolds a protocol to be implemented by the developer.]\n"
        expected_output += "tac\t[The tac protocol implements the messages an AEA needs to participate in the TAC.]\n"
        return expected_output

    def test_correct_output_default_registry(self):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "protocols"])

        assert self.result.output == self._generated_expected_output()

    def test_correct_output_custom_registry(self):
        """Test that the command has printed the correct output when using a custom registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "--registry", DEFAULT_REGISTRY_PATH, "protocols"])
        test = self._generated_expected_output()
        assert self.result.output == test

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


    def _generated_expected_output(self):
        expected_output = "Available connections:\n"
        expected_output += "gym\t[The gym connection wraps an OpenAI gym.]\n"
        expected_output += "local\t[The local connection provides a stub for an OEF node.]\n"
        expected_output += "oef\t[The oef connection provides a wrapper around the OEF sdk.]\n"
        expected_output += "p2p\t[The p2p connection provides a connection with the fetch.ai mail provider.]\n"
        expected_output += "scaffold\t[The scaffold connection provides a scaffold for a connection to be implemented by the developer.]\n"
        expected_output += "stub\t[The stub connection implements a connection stub which reads/writes messages from/to file.]\n"
        expected_output += "tcp\t[None]\n"
        return expected_output

    def test_correct_output_default_registry(self):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "connections"])
        assert self.result.output == self._generated_expected_output()

    def test_correct_output_custom_registry(self):
        """Test that the command has printed the correct output when using a custom registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "--registry", DEFAULT_REGISTRY_PATH, "connections"])
        assert self.result.output == self._generated_expected_output()

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

    def _generated_expected_output(self):
        expected_output = "Available skills:\n"
        expected_output += "carpark_client\t[None]\n"
        expected_output += "carpark_detection\t[None]\n"
        expected_output += "echo\t[The echo skill implements simple echo functionality.]\n"
        expected_output += "error\t[The error skill implements basic error handling required by all AEAs.]\n"
        expected_output += "fipa_negotiation\t[The fipa skill implements the logic for an AEA to do fipa negotiation.]\n"
        expected_output += "gym\t[The gym skill wraps an RL agent.]\n"
        expected_output += "scaffold\t[The scaffold skill is a scaffold for your own skill implementation.]\n"
        expected_output += "tac\t[The tac skill implements the logic for an AEA to participate in the TAC.]\n"
        expected_output += "weather_client\t[None]\n"
        expected_output += "weather_client_ledger\t[None]\n"
        expected_output += "weather_station\t[None]\n"
        expected_output += "weather_station_ledger\t[None]\n"

        return expected_output

    def test_correct_output_default_registry(self):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "skills"])

        test = self._generated_expected_output()
        assert self.result.output == self._generated_expected_output()

    def test_correct_output_custom_registry(self):
        """Test that the command has printed the correct output when using a custom registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "--registry", DEFAULT_REGISTRY_PATH, "skills"])

        assert self.result.output == self._generated_expected_output()

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
