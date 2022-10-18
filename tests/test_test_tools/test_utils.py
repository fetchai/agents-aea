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

"""Test utilities."""

import tempfile

import pytest

from aea.test_tools.utils import remove_test_directory, wait_for_condition


def test_wait_for_condition():
    """Test test_wait_for_condition"""

    wait_for_condition(lambda: True)
    with pytest.raises(TimeoutError, match="test error msg"):
        wait_for_condition(lambda: False, error_msg="test error msg")


def test_remove_test_directory():
    """Test remove_test_directory"""

    with tempfile.TemporaryDirectory() as tmp_dir:
        assert remove_test_directory(str(tmp_dir))
