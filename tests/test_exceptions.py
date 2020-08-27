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
"""This module contains tests for aea exceptions."""

import pytest

from aea.exceptions import AEAEnforceError, enforce


def test_enforce_no_exception():
    """Test enforce does not throw exception if condition is True."""
    enforce(True, "Error message")


def test_enforce_exception():
    """Test enforce does throw exception if condition is False."""
    error_msg = "Error message"
    with pytest.raises(AEAEnforceError, match=error_msg):
        enforce(False, error_msg)
