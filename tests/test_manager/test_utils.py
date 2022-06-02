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
"""This module contains tests for aea manager utils."""
import time
from random import randint
from tempfile import TemporaryDirectory

import pytest

from aea.manager.utils import run_in_venv


RETURN_VALUE = randint(0, 2000)  # nosec

DEFAULT_TIMEOUT = 20


def _process_long():
    time.sleep(70)


def _process_exception():
    raise ValueError("Expected")


def _process_return_value(value_to_return):
    return value_to_return


def test_process_run_in_venv_timeout_error():
    """Test timeout error raised for process running too long."""
    with TemporaryDirectory() as tmp_dir:
        with pytest.raises(TimeoutError):
            run_in_venv(tmp_dir, _process_long, timeout=DEFAULT_TIMEOUT)


def test_process_run_in_venv_raise_custom_exception():
    """Test process returns expcetion."""
    with TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception, match="Expected"):
            run_in_venv(tmp_dir, _process_exception, timeout=DEFAULT_TIMEOUT)


def test_process_run_in_venv_return_value():
    """Test process return value."""
    with TemporaryDirectory() as tmp_dir:
        ret_value = run_in_venv(
            tmp_dir, _process_return_value, DEFAULT_TIMEOUT, RETURN_VALUE
        )
        assert ret_value == RETURN_VALUE
