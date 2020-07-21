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
"""This module contains the tests for AsyncFriendlyQueue."""
import asyncio
from concurrent.futures._base import CancelledError

import pytest

from aea.helpers.async_utils import (
    AsyncState,
    PeriodicCaller,
    ThreadedAsyncRunner,
    cancel_and_wait,
    ensure_list,
    ensure_loop,
)


def test_enusre_list() -> None:
    """Test AsyncFriendlyQueue in one thread environment."""
    list1 = [1, 2, 3]
    assert ensure_list(list1) is list1

    assert ensure_list(1) == [1]
    assert ensure_list(map(lambda x: x, list1)) == list1


@pytest.mark.asyncio
async def test_async_state():
    """Test various cases for AsyncState."""
    loop = asyncio.get_event_loop()
    state = AsyncState()

    # check set/get
    value = 1
    state.set(value)
    assert state.get() == value

    # check set/get with state property
    value = 3
    state.state = 3
    assert state.state == value

    # check wait/set
    loop.call_soon(state.set, 2)
    await state.wait(2)

    # state is already set
    await state.wait(2)


@pytest.mark.asyncio
async def test_periodic_caller_start_stop():
    """Test start stop calls for PeriodicCaller."""
    called = 0

    def callback():
        nonlocal called
        called += 1

    periodic_caller = PeriodicCaller(callback, period=0.1)
    periodic_caller.start()

    await asyncio.sleep(0.15)
    assert called >= 1

    periodic_caller.stop()
    old_called = called
    await asyncio.sleep(0.15)
    assert old_called == called


@pytest.mark.asyncio
async def test_periodic_caller_exception():
    """Test exception raises for PeriodicCaller."""
    exception_called = False

    def exception_callback(*args, **kwargs):
        nonlocal exception_called
        exception_called = True

    def callback():
        raise Exception("expected")

    periodic_caller = PeriodicCaller(
        callback, period=0.1, exception_callback=exception_callback
    )
    periodic_caller.start()

    await asyncio.sleep(0.15)
    assert exception_called
    periodic_caller.stop()


@pytest.mark.asyncio
async def test_ensure_loop():
    """Test ensure_loop."""
    loop = asyncio.new_event_loop()
    assert ensure_loop(loop) == loop

    loop = asyncio.get_event_loop()
    assert ensure_loop(loop) != loop


@pytest.mark.asyncio
async def test_threaded_async_run():
    """Test threaded async runner."""
    runner = ThreadedAsyncRunner()
    runner.start()

    async def fn():
        return "ok"

    assert runner.call(fn()).result() == "ok"
    runner.stop()


@pytest.mark.asyncio
async def test_threaded_async_run_cancel_task():
    """Test threaded async runner tasks cancelled."""
    runner = ThreadedAsyncRunner()
    runner.start()

    async def fn():
        await asyncio.sleep(1)

    task = runner.call(fn())
    await asyncio.sleep(0.1)
    task.cancel()
    await asyncio.sleep(0.1)
    with pytest.raises(CancelledError):
        task.result()

    assert task.done()

    # cancel before start
    task = runner.call(fn())
    task.cancel()
    with pytest.raises(CancelledError):
        task.result()
    assert task.done()
    runner.stop()


@pytest.mark.asyncio
async def test_cancel_and_wait():
    """Test task cancel and wait."""
    loop = asyncio.get_event_loop()
    task = loop.create_task(asyncio.sleep(1))

    r = await cancel_and_wait(task)
    assert isinstance(r, asyncio.CancelledError)

    # cancel and wait completed task
    task = loop.create_task(asyncio.sleep(0))
    await asyncio.sleep(0.01)
    assert task.done()
    r = await cancel_and_wait(task)
    assert r is None
