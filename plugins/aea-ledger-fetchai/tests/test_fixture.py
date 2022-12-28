# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This module contains the tests of the fetchai fixture helpers module."""
import platform

import pytest
import requests
from _pytest.compat import get_real_func
from aea_ledger_fetchai.test_tools.constants import (
    DEFAULT_FETCH_LEDGER_ADDR,
    DEFAULT_FETCH_LEDGER_RPC_PORT,
)
from aea_ledger_fetchai.test_tools.fixture_helpers import fetchd


def test_fetchd_fixture() -> None:
    """Test fetchd fixture just start and stop."""
    if platform.system() != "Linux":
        pytest.skip("Skip on non Linux systems")
    gen = get_real_func(fetchd)()

    next(gen)
    # started
    try:
        response = requests.get(
            f"{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_RPC_PORT}/net_info?"
        )
        assert response.status_code == 200
    finally:
        with pytest.raises(StopIteration):
            next(gen)
