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
"""This module contains the tests for the helpers/profiling module."""
from aea.helpers.profiling import Profiling
from aea.protocols.base import Message

from tests.common.utils import wait_for_condition


def test_profiling():
    """Test profiling tool."""
    result = ""

    def output_function(report):
        nonlocal result
        result = report

    p = Profiling(1, [Message], [Message], output_function=output_function)
    p.start()

    wait_for_condition(lambda: p.is_running, timeout=20)
    m = Message()
    try:
        wait_for_condition(lambda: result, timeout=20)

        assert "Profiling details" in result
    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=20)
    del m
