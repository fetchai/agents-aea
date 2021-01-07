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
"""This module contains the tests for the helper module."""
import pytest

from aea.helpers.env_vars import (
    apply_env_variables,
    convert_value_str_to_type,
    is_env_variable,
    replace_with_env_var,
)


def test_is_env_variable():
    """Test is_env_variable."""
    assert is_env_variable("${test}")
    assert is_env_variable("${test:int}")
    assert is_env_variable("${test:int:12}")

    assert not is_env_variable("sdfsdf")


def test_apply_env_variables():
    """Test apply_env_variables"""
    assert apply_env_variables("${var}", {"var": "test"}) == "test"
    assert apply_env_variables("var", {"var": "test"}) == "var"
    assert apply_env_variables(["${var}"], {"var": "test"}) == ["test"]
    assert apply_env_variables({"${var}": "${var}"}, {"var": "test"}) == {
        "test": "test"
    }


def test_replace_with_env_var():
    """Test replace_with_env_var."""
    assert replace_with_env_var("${var:int:12}", {"var": "10"}) == 10
    assert replace_with_env_var("${var:int:12}", {}) == 12
    assert replace_with_env_var("var", {}) == "var"
    assert replace_with_env_var("${var}", {}, default_value=100) == 100

    with pytest.raises(
        ValueError, match=r"`var` not found in env variables and no default value set!",
    ):
        replace_with_env_var("${var}", {})


def test_convert_value_str_to_type():
    """Test convert_value_str_to_type."""
    assert convert_value_str_to_type("false", "bool") is False
    assert convert_value_str_to_type("True", "bool") is True
    assert convert_value_str_to_type("12", "int") == 12
    assert convert_value_str_to_type("1.1", "float") == 1.1
    assert convert_value_str_to_type("1sdfsdf2", "none") is None
    assert convert_value_str_to_type('{"a": 12}', "dict") == {"a": 12}
