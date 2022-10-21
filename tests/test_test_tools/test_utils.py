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

import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from aea.test_tools import utils
from aea.test_tools.utils import (
    FULL_PERMISSION,
    remove_test_directory,
    wait_for_condition,
)


def test_wait_for_condition():
    """Test test_wait_for_condition"""

    wait_for_condition(lambda: True)
    with pytest.raises(TimeoutError, match="test error msg"):
        wait_for_condition(lambda: False, error_msg="test error msg")


@pytest.mark.parametrize("path_type", [str, Path])
def test_remove_non_empty_test_directory(path_type):
    """Test remove_test_directory"""

    tmp_dir = path_type(tempfile.TemporaryDirectory().name)
    assert not os.path.exists(tmp_dir)
    shutil.copytree(str(Path(utils.__file__).parent), tmp_dir)
    assert os.path.isdir(tmp_dir)
    assert list(Path(tmp_dir).glob("*"))

    permission = os.stat(tmp_dir).st_mode
    assert permission != FULL_PERMISSION
    with mock.patch("os.lstat", side_effect=Exception):
        assert not remove_test_directory(tmp_dir)
    assert os.path.exists(tmp_dir)
    assert os.stat(tmp_dir).st_mode == permission

    assert remove_test_directory(tmp_dir)
    assert not os.path.exists(tmp_dir)
