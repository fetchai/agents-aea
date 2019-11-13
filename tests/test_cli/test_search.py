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
        return """Available protocols:
------------------------------
Name: default
Description: The default protocol allows for any bytes message.
Version: 0.1.0
------------------------------
------------------------------
Name: fipa
Description: The fipa protocol implements the FIPA ACL.
Version: 0.1.0
------------------------------
------------------------------
Name: gym
Description: The gym protocol implements the messages an agent needs to engage with a gym connection.
Version: 0.1.0
------------------------------
------------------------------
Name: oef
Description: The oef protocol implements the OEF specific messages.
Version: 0.1.0
------------------------------
------------------------------
Name: tac
Description: The tac protocol implements the messages an AEA needs to participate in the TAC.
Version: 0.1.0
------------------------------

"""

    def test_correct_output_default_registry(self):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "protocols"])
        assert self.result.output == self._generated_expected_output()

    def test_correct_output_custom_registry(self):
        """Test that the command has printed the correct output when using a custom registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "--registry", DEFAULT_REGISTRY_PATH, "protocols"])
        assert self.result.output == self._generated_expected_output()

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
        return """Available connections:
------------------------------
Name: gym
Description: The gym connection wraps an OpenAI gym.
Version: 0.1.0
------------------------------
------------------------------
Name: local
Description: The local connection provides a stub for an OEF node.
Version: 0.1.0
------------------------------
------------------------------
Name: oef
Description: The oef connection provides a wrapper around the OEF sdk.
Version: 0.1.0
------------------------------
------------------------------
Name: p2p
Description: The p2p connection provides a connection with the fetch.ai mail provider.
Version: 0.1.0
------------------------------
------------------------------
Name: stub
Description: The stub connection implements a connection stub which reads/writes messages from/to file.
Version: 0.1.0
------------------------------
------------------------------
Name: tcp
Description: None
Version: 0.1.0
------------------------------

"""

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
        return """Available skills:
------------------------------
Name: carpark_client
Description: None
Version: 0.1.0
------------------------------
------------------------------
Name: carpark_detection
Description: None
Version: 0.1.0
------------------------------
------------------------------
Name: echo
Description: The echo skill implements simple echo functionality.
Version: 0.1.0
------------------------------
------------------------------
Name: error
Description: The error skill implements basic error handling required by all AEAs.
Version: 0.1.0
------------------------------
------------------------------
Name: gym
Description: The gym skill wraps an RL agent.
Version: 0.1.0
------------------------------
------------------------------
Name: tac_control
Description: The tac control skill implements the logic for an AEA to control an instance of the TAC.
Version: 0.1.0
------------------------------
------------------------------
Name: tac_negotiation
Description: The tac negotiation skill implements the logic for an AEA to do fipa negotiation in the TAC.
Version: 0.1.0
------------------------------
------------------------------
Name: tac_participation
Description: The tac participation skill implements the logic for an AEA to participate in the TAC.
Version: 0.1.0
------------------------------
------------------------------
Name: weather_client
Description: None
Version: 0.1.0
------------------------------
------------------------------
Name: weather_client_ledger
Description: None
Version: 0.1.0
------------------------------
------------------------------
Name: weather_station
Description: None
Version: 0.1.0
------------------------------
------------------------------
Name: weather_station_ledger
Description: None
Version: 0.1.0
------------------------------

"""

    def test_correct_output_default_registry(self):
        """Test that the command has printed the correct output when using the default registry."""
        os.chdir(AEA_DIR)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "search", "skills"])
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
