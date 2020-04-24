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

"""This module contains decorators for AEA end-to-end testing."""

from typing import Callable

import pytest


def skip_test_ci(pytest_func: Callable) -> Callable:
    """
    Decorate a pytest method to skip a test in a case of CI usage.

    :param pytest_func: a pytest method to decorate.

    :return: decorated method.
    """

    def wrapped(self, pytestconfig, *args, **kwargs):
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")
        else:
            pytest_func(self, pytestconfig, *args, **kwargs)

    return wrapped
