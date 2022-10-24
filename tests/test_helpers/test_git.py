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

"""Tests for git tools."""

from unittest import mock

from aea.helpers.git import check_working_tree_is_dirty


def test_check_working_tree_is_dirty():
    """Test check_working_tree_is_dirty"""

    # NOTE: logic is inverted from what one would expect
    with mock.patch("subprocess.check_output", return_value=b""):
        assert check_working_tree_is_dirty()
    with mock.patch("subprocess.check_output", return_value=b"dirt"):
        assert not check_working_tree_is_dirty()
