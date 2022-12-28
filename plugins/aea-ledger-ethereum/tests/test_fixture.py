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
"""This module contains the tests of the ethereum module."""
import pytest
import requests
from _pytest.compat import get_real_func
from aea_ledger_ethereum.test_tools.fixture_helpers import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
    ganache,
)

from tests.conftest import action_for_platform


@action_for_platform("Linux", skip=False)
def test_ganache_fixture() -> None:
    """Test ganache fixture just start and stop."""
    request = dict(jsonrpc=2.0, method="web3_clientVersion", params=[], id=1)

    gen = get_real_func(ganache)()

    next(gen)
    # started

    try:
        response = requests.post(
            f"{DEFAULT_GANACHE_ADDR}:{DEFAULT_GANACHE_PORT}", json=request
        )
        assert response.status_code == 200
    finally:
        with pytest.raises(StopIteration):
            next(gen)
