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

"""This module contains mocking utils testing purposes."""
import re
import unittest
from collections import Sequence
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock


class AnyStringWith(str):
    """
    Helper class to assert calls of mocked method with string arguments.

    It will use string inclusion as equality comparator.
    """

    def __eq__(self, other):
        return self in other


class RegexComparator(str):
    """
    Helper class to assert calls of mocked method with string arguments.

    It will use regex matching as equality comparator.
    """

    def __eq__(self, other):
        regex = re.compile(str(self), re.MULTILINE | re.DOTALL)
        s = str(other)
        return bool(regex.match(s))


@contextmanager
def ctx_mock_Popen() -> MagicMock:
    """
    Mock subprocess.Popen.

    Act as context manager.

    :return: mock object.
    """
    return_value = MagicMock()
    return_value.communicate.return_value = (MagicMock(), MagicMock())

    with unittest.mock.patch("subprocess.Popen", return_value=return_value) as mocked:
        yield mocked


class MockCallableNTimes:
    """Mock a callable for N times."""

    def __init__(self, values: Sequence, default: Any):
        """Initialize."""
        self.values = values
        self.default = default

        self._iterator = iter(self.values)

    def __call__(self, *args, **kwargs):
        try:
            n = next(self._iterator)
            if n is None:
                return self.default
            if issubclass(n, BaseException):
                raise n
            print(n)
            return n
        except StopIteration:
            return self.default
