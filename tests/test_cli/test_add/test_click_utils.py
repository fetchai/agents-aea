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

"""Module with tests for click utils of the aea cli."""

import pytest
from click import ClickException

from aea.cli.utils.click_utils import reraise_as_click_exception


def test_reraise_as_click_exception() -> None:
    """Test reraise_as_click_exception"""

    # all are exceptions
    assert issubclass(ValueError, Exception)
    assert issubclass(ZeroDivisionError, Exception)
    assert issubclass(ClickException, Exception)

    # none are subclasses of one-another
    assert not issubclass(ValueError, ClickException)
    assert not issubclass(ClickException, ValueError)

    assert not issubclass(ValueError, ZeroDivisionError)
    assert not issubclass(ZeroDivisionError, ValueError)

    # Beware! Does not fail because we exit early
    with pytest.raises(ValueError):
        with pytest.raises(ZeroDivisionError):
            raise ValueError()
        raise AssertionError()

    # 1. do not raise on pass
    with reraise_as_click_exception():
        pass

    with reraise_as_click_exception(Exception):
        pass

    # 2. raise ClickException instead of ValueError
    with pytest.raises(ClickException):
        with reraise_as_click_exception(ValueError):
            raise ValueError()

    # 3. do not raise on another Exception
    with pytest.raises(ZeroDivisionError):
        with reraise_as_click_exception(ValueError):
            raise ZeroDivisionError()
