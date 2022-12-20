# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
"""This module contains the tests for the helper module."""
from typing import List

import pytest

from aea.helpers.env_vars import (
    apply_env_variables,
    apply_env_variables_on_agent_config,
    convert_value_str_to_type,
    export_path_to_env_var_string,
    generate_env_vars_recursively,
    is_env_variable,
    is_strict_list,
    replace_with_env_var,
)


def test_is_env_variable():
    """Test is_env_variable."""
    assert is_env_variable("${TEST}")
    assert is_env_variable("${TEST:int}")
    assert is_env_variable("${TEST:int:12}")

    assert not is_env_variable("sdfsdf")


def test_apply_env_variables():
    """Test apply_env_variables"""
    assert apply_env_variables("${VAR}", {"VAR": "test"}) == "test"
    assert apply_env_variables("var", {"var": "test"}) == "var"
    assert apply_env_variables(["${VAR}"], {"VAR": "test"}) == ["test"]


def test_replace_with_env_var():
    """Test replace_with_env_var."""
    assert replace_with_env_var("${VAR:int:12}", {"VAR": "10"}) == 10
    assert replace_with_env_var("${VAR:int:12}", {}) == 12
    assert replace_with_env_var("${VAR}", {}, default_value=100) == 100

    assert replace_with_env_var("var", {}) == "var"


def test_failures() -> None:
    """Test failures."""

    with pytest.raises(
        ValueError,
        match=r"`VAR` not found in env variables and no default value set!",
    ):
        replace_with_env_var("${VAR}", {})

    with pytest.raises(KeyError, match="`var` is not a valid python data type"):
        replace_with_env_var("${VAR:var}", {"VAR": "some_value"})

    with pytest.raises(
        ValueError, match="Cannot convert string `some_value` to type `float`"
    ):
        replace_with_env_var("${VAR:float}", {"VAR": "some_value"})


def test_apply_none_with_env_var():
    """Test replace_with_env_var."""
    assert replace_with_env_var("${VAR:int:none}", {"VAR": "10"}) == 10
    assert replace_with_env_var("${VAR:int:none}", {}) is None


def test_convert_value_str_to_type():
    """Test convert_value_str_to_type."""
    assert convert_value_str_to_type("false", "bool") is False
    assert convert_value_str_to_type("True", "bool") is True
    assert convert_value_str_to_type("12", "int") == 12
    assert convert_value_str_to_type("1.1", "float") == 1.1
    assert convert_value_str_to_type("1sdfsdf2", "none") is None
    assert convert_value_str_to_type('{"a": 12}', "dict") == {"a": 12}
    assert convert_value_str_to_type("Null", "str") is None
    assert convert_value_str_to_type("none", "str") is None
    assert convert_value_str_to_type("null", "str") is None
    assert convert_value_str_to_type("None", "str") is None


@pytest.mark.parametrize(
    ("export_path", "var_string"),
    argvalues=[
        (["skill", "dummy", "models", "args"], "SKILL_DUMMY_MODELS_ARGS"),
        (
            ["skill", "dummy", "models", "args", "params"],
            "SKILL_DUMMY_MODELS_ARGS_PARAMS",
        ),
        (
            ["skill", "dummy", "models", "args", "params", "name"],
            "SKILL_DUMMY_MODELS_ARGS_PARAMS_NAME",
        ),
        (["connection", "dummy", "config", "host"], "CONNECTION_DUMMY_CONFIG_HOST"),
        ([0, "connection", "dummy"], "0_CONNECTION_DUMMY"),
        (["connection", 0, "dummy"], "CONNECTION_0_DUMMY"),
        (["connection", "dummy", 0], "CONNECTION_DUMMY_0"),
    ],
)
def test_env_var_string_generator(export_path: List[str], var_string: str) -> None:
    """Test `export_path_to_env_var_string` method"""

    assert export_path_to_env_var_string(export_path=export_path) == var_string


@pytest.mark.parametrize(
    ("export_data", "template"),
    argvalues=[
        (
            {
                "dict": "Viraj",
            },
            {
                "dict": "${str}",
            },
        ),
        (
            {"list": [1, 2, 3]},
            {"list": "${list}"},
        ),
        (
            {
                "nested_dict": {
                    "dict": "Viraj",
                }
            },
            {
                "nested_dict": {
                    "dict": "${str}",
                },
            },
        ),
        (
            {"nested_list": [[1], [2], [3]]},
            {"nested_list": "${list}"},
        ),
        (
            {
                "nested_dict": {
                    "dict": "Viraj",
                    "list": [1, 2, 3],
                }
            },
            {
                "nested_dict": {
                    "dict": "${str}",
                    "list": "${list}",
                },
            },
        ),
        (
            {
                "nested_list": [
                    {
                        "dict": "hello",
                    },
                    {
                        "dict": "world",
                    },
                ]
            },
            {
                "nested_list": [
                    {"dict": "${str}"},
                    {"dict": "${str}"},
                ]
            },
        ),
    ],
)
def test_match_export_parse_consistency(export_data, template) -> None:
    """Test to match export and parsing consistency with different data structures."""

    env_vars = generate_env_vars_recursively(
        export_data,
        export_path=[],
    )

    parsed_data = apply_env_variables(template, env_variables=env_vars)

    assert parsed_data == export_data


def test_apply_env_variables_on_agent_config():
    """Test apply_env_variables_on_agent_config function."""
    result = apply_env_variables_on_agent_config(
        [{"arg": "${VAR}"}, {"public_id": "fetchai/test:0.1.0", "arg": "${VAR}"}],
        {"VAR": 12},
    )
    assert result == [{"arg": 12}, {"arg": 12, "public_id": "fetchai/test:0.1.0"}]


def test_is_strict_list():
    """Test is_strict method."""
    assert is_strict_list([1, 2, 3])
    assert is_strict_list([1, 2, 3, [1, 2, 3]])
    assert not is_strict_list([1, 2, {}])
    assert not is_strict_list([1, 2, [[{}]]])
    assert not is_strict_list([(dict(hello="world"),)])
