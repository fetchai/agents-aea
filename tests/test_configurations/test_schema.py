# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This test module contains the tests for the JSON schemas of the configuration files."""
import itertools
import json
import os
from itertools import zip_longest
from pathlib import Path

import jsonschema
import pytest
import yaml
from jsonschema import Draft4Validator  # type: ignore

from aea.configurations.validation import make_jsonschema_base_uri

from tests.conftest import (
    AGENT_CONFIGURATION_SCHEMA,
    CONFIGURATION_SCHEMA_DIR,
    CONNECTION_CONFIGURATION_SCHEMA,
    CONTRACT_CONFIGURATION_SCHEMA,
    PROTOCOL_CONFIGURATION_SCHEMA,
    PROTOCOL_SPEC_CONFIGURATION_SCHEMA,
    ROOT_DIR,
    SKILL_CONFIGURATION_SCHEMA,
    agent_config_files,
    connection_config_files,
    contract_config_files,
    protocol_config_files,
    protocol_specification_files,
    skill_config_files,
)


def test_agent_configuration_schema_is_valid_wrt_draft_04():
    """Test that the JSON schema for the agent configuration file is compliant with the specification Draft 04."""
    agent_config_schema = json.load(
        open(
            os.path.join(
                ROOT_DIR, "aea", "configurations", "schemas", "aea-config_schema.json"
            )
        )
    )
    Draft4Validator.check_schema(agent_config_schema)


def test_skill_configuration_schema_is_valid_wrt_draft_04():
    """Test that the JSON schema for the skill configuration file is compliant with the specification Draft 04."""
    skill_config_schema = json.load(
        open(
            os.path.join(
                ROOT_DIR, "aea", "configurations", "schemas", "skill-config_schema.json"
            )
        )
    )
    Draft4Validator.check_schema(skill_config_schema)


def test_connection_configuration_schema_is_valid_wrt_draft_04():
    """Test that the JSON schema for the connection configuration file is compliant with the specification Draft 04."""
    connection_config_schema = json.load(
        open(
            os.path.join(
                ROOT_DIR,
                "aea",
                "configurations",
                "schemas",
                "connection-config_schema.json",
            )
        )
    )
    Draft4Validator.check_schema(connection_config_schema)


def test_protocol_configuration_schema_is_valid_wrt_draft_04():
    """Test that the JSON schema for the protocol configuration file is compliant with the specification Draft 04."""
    protocol_config_schema = json.load(
        open(
            os.path.join(
                ROOT_DIR,
                "aea",
                "configurations",
                "schemas",
                "protocol-config_schema.json",
            )
        )
    )
    Draft4Validator.check_schema(protocol_config_schema)


def test_definitions_schema_is_valid_wrt_draft_04():
    """Test that the JSON schema for the definitions is compliant with the specification Draft 04."""
    definitions_config_schema = json.load(
        open(
            os.path.join(
                ROOT_DIR, "aea", "configurations", "schemas", "definitions.json"
            )
        )
    )
    Draft4Validator.check_schema(definitions_config_schema)


@pytest.mark.parametrize(
    "schema_file_path, config_file_path",
    itertools.chain.from_iterable(
        [
            zip_longest([], files, fillvalue=schema)
            for files, schema in [
                (agent_config_files, AGENT_CONFIGURATION_SCHEMA),
                (protocol_config_files, PROTOCOL_CONFIGURATION_SCHEMA),
                (contract_config_files, CONTRACT_CONFIGURATION_SCHEMA),
                (connection_config_files, CONNECTION_CONFIGURATION_SCHEMA),
                (skill_config_files, SKILL_CONFIGURATION_SCHEMA),
                (protocol_specification_files, PROTOCOL_SPEC_CONFIGURATION_SCHEMA),
            ]
        ]
    ),
)
def test_config_validation(schema_file_path, config_file_path):
    """Test configuration validation."""
    # TODO a bit inefficient to load each schema everytime; consider making the validators as fixtures.
    schema = json.load(open(schema_file_path))
    resolver = jsonschema.RefResolver(
        make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR).absolute()),
        schema,
    )
    validator = Draft4Validator(schema, resolver=resolver)
    config_data = list(yaml.safe_load_all(open(config_file_path)))
    validator.validate(instance=config_data[0])
