# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains tests for aea exceptions."""

import pytest

from aea.exceptions import AEAEnforceError, _StopRuntime, enforce, parse_exception


def test_enforce_no_exception():
    """Test enforce does not throw exception if condition is True."""
    enforce(True, "Error message")


def test_enforce_exception():
    """Test enforce does throw exception if condition is False."""
    error_msg = "Error message"
    with pytest.raises(AEAEnforceError, match=error_msg):
        enforce(False, error_msg)


def test_stop_runtime():
    """Test thes stop runtime exception."""
    test = "test string"
    e = _StopRuntime(test)
    assert e.reraise == test


def test_parse_exception_i():
    """Test parse exception."""

    def exception_raise():
        """A function that raises an exception."""
        raise ValueError("expected")

    try:
        exception_raise()
    except Exception as e:
        out = parse_exception(e)

    expected = [
        "Traceback (most recent call last):\n\n",
        'test_exceptions.py", line ',
        "in exception_raise\n",
        'raise ValueError("expected")\n\nValueError: expected\n',
    ]
    assert all([string in out for string in expected])


def test_parse_exception_ii():
    """Test parse exception."""

    def exception_raise():
        """A function that raises an exception."""
        raise AEAEnforceError("expected")

    try:
        exception_raise()
    except Exception as e:
        out = parse_exception(e)

    expected = [
        "Traceback (most recent call last):\n\n",
        'test_exceptions.py", line ',
        "in test_parse_exception_ii\n",
        "exception_raise()\n\n",
        ", line",
        "in exception_raise\n",
        'raise AEAEnforceError("expected")\n\naea.exceptions.AEAEnforceError: expected\n',
    ]
    assert all([string in out for string in expected])
