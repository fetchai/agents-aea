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
"""This module contains the tests for async utils."""
import asyncio

import pytest

from aea.helpers.async_utils import AsyncState, create_task


@pytest.mark.asyncio
async def test_async_state_same_loop():
    """Test AsyncState class."""
    initial = None
    target_state = "target_state"
    async_state = AsyncState(initial_state=initial)

    assert async_state.state == initial
    assert await async_state.wait(initial) == (None, initial)

    task = create_task(async_state.wait(target_state))
    await asyncio.sleep(0)
    async_state.state = target_state
    assert await asyncio.wait_for(task, timeout=1) == (initial, target_state)
