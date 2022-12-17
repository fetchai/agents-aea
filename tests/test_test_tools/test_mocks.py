# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains tests for mocking utils."""

import subprocess  # nosec
from typing import Any
from unittest import mock

import pytest

from aea.test_tools.mocks import AnyStringWith, RegexComparator, ctx_mock_Popen


@pytest.mark.parametrize("builtin_type", [str, list, tuple])
def test_any_string_with(builtin_type: Any) -> None:
    """Test AnyStringWith"""

    assert AnyStringWith("in") in builtin_type(["string"])
    assert not AnyStringWith("ni") in builtin_type(["string"])


@pytest.mark.parametrize("builtin_type", [str, list, tuple])
def test_regex_comparator(builtin_type: Any) -> None:
    """Test RegexComparator"""

    assert RegexComparator("in") in builtin_type(["string"])
    assert not RegexComparator("ni") in builtin_type(["string"])


def test_ctx_mock_popen_communicate_return_value() -> None:
    """Test ctx_mock_popen"""

    cmd_name, *args = "python", "--version"
    popen = subprocess.Popen([cmd_name, *args])  # nosec
    stdout, stderr = popen.communicate()
    assert stdout is stderr is None
    assert popen.returncode == 0

    with ctx_mock_Popen():
        popen = subprocess.Popen([cmd_name])  # nosec
        stdout, stderr = popen.communicate()
        objects = stdout, stderr, popen.returncode
        assert all(isinstance(obj, mock.MagicMock) for obj in objects)
