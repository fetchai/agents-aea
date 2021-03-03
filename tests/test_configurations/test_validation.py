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
"""This module contains the tests for the aea.configurations.validation module."""
from aea.configurations.validation import (
    SAME_MARK,
    filter_data,
    validate_data_with_pattern,
)


def test_compare_data_pattern():
    """Test validate_data_with_pattern."""
    errors = validate_data_with_pattern({"a": 12}, {"a": 13})
    assert not errors

    errors = validate_data_with_pattern({"a": 12}, {"a": "string"})
    assert errors
    assert (
        errors[0]
        == "For attribute `a` `str` data type is expected, but `int` was provided!"
    )

    errors = validate_data_with_pattern({"a": None}, {"a": int})
    assert not errors

    assert not validate_data_with_pattern(
        {"a": 12}, {"a": "${var}"}, skip_env_vars=True
    )
    assert not validate_data_with_pattern(
        {"a": "${var}"}, {"a": "string"}, skip_env_vars=True
    )

    errors = validate_data_with_pattern({"a": 12}, {"b": 12})
    assert errors
    assert errors[0] == "Attribute `a` is not allowed to be updated!"

    errors = validate_data_with_pattern({"a": {}}, {"a": {"b": 12}})
    assert errors
    assert errors[0] == "Attribute `a` is not allowed to be updated!"


def test_filter_data():
    """Test filter_data function."""
    assert filter_data(1, 1) == SAME_MARK
    assert filter_data(1, 2) == 2
    assert filter_data(2, 1) == 1

    assert filter_data({}, {}) == SAME_MARK
    assert filter_data({1: 2}, {1: 2}) == SAME_MARK
    assert filter_data({1: 2}, {1: 3}) == {1: 3}

    assert filter_data([1, 2, 3], [1, 2, 3]) == SAME_MARK
    assert filter_data([1, 2, 3], [1, 2]) == [1, 2]

    assert filter_data({1: {2: 3}, 3: {2: 1}}, {1: {2: 3}, 3: {2: 3}, 0: 0}) == {
        3: {2: 3},
        0: 0,
    }
