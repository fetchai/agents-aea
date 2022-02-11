# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This module contains the tests for AsyncFriendlyQueue."""

import asyncio
import time
from queue import Empty
from threading import Thread

import pytest

from aea.helpers.async_friendly_queue import AsyncFriendlyQueue


def test_same_thread() -> None:
    """Test AsyncFriendlyQueue in one thread environment."""
    sq = AsyncFriendlyQueue()

    with pytest.raises(Empty):
        sq.get_nowait()

    item = "item"
    sq.put_nowait(item)
    assert sq.get_nowait() == item


@pytest.mark.asyncio
async def test_asyncio_loop() -> None:
    """Test AsyncFriendlyQueue inside one event loop."""
    sq = AsyncFriendlyQueue()
    item = "item"
    sq.put(item)
    assert await sq.async_get() == item


def test_many_threads_with_asyncio() -> None:
    """Test AsyncFriendlyQueue wuth multiple asyncio event loop consumers in different threads."""
    sq = AsyncFriendlyQueue()
    num_threads = 10
    threads = []
    results = []  # type: ignore

    def test(sq, timeout, results):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def wait_msg(sq, timeout, results):
            await asyncio.wait_for(sq.async_get(), timeout)
            results.append("done")

        loop.run_until_complete(wait_msg(sq, timeout, results))
        loop.close()

    for _ in range(num_threads):
        t = Thread(target=test, args=(sq, 5, results))
        t.daemon = True
        t.start()
        threads.append(t)

    time.sleep(0.03)
    for _ in range(num_threads):
        sq.put("item")

    for t in threads:
        t.join()

    assert len(results) == num_threads
