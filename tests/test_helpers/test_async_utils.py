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
"""This module contains the tests for AsyncFriendlyQueue."""
import asyncio
import time
from concurrent.futures._base import CancelledError
from contextlib import suppress
from threading import Thread

import pytest

from aea.helpers.async_utils import (
    AsyncState,
    PeriodicCaller,
    Runnable,
    ThreadedAsyncRunner,
    ensure_list,
)

from tests.common.utils import wait_for_condition, wait_for_condition_async


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
async def test_async_state_transit():
    """Test async state transit contextmanager."""
    state = AsyncState()
    state.set(None)

    with state.transit(initial=1, success=2, fail=3):
        assert state.get() == 1
    assert state.get() == 2

    state.set(None)

    with suppress(ValueError):
        with state.transit(initial=1, success=2, fail=3):
            assert state.get() == 1
            raise ValueError()

    assert state.get() == 3


@pytest.mark.asyncio
async def test_asyncstate_with_list_of_valid_states():
    """Test various cases for AsyncState."""
    states = [1, 2, 3]
    state = AsyncState(1, states)

    state.set(2)
    assert state.get() == 2

    with pytest.raises(ValueError):
        state.set("anything")

    assert state.get() == 2


@pytest.mark.asyncio
async def test_asyncstate_callback():
    """Test various cases for AsyncState.callback."""
    state = AsyncState()

    called = False

    def callback_err(state):
        raise Exception("expected")

    def callback(state):
        nonlocal called
        called = True

    state.add_callback(callback_err)
    state.add_callback(callback)

    state.set(2)
    assert state.get() == 2
    assert called


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


class RunAndExit(Runnable):
    """Test class."""

    async def run(self):
        """Test method."""
        await asyncio.sleep(0.2)


class TestRunnable:
    """Tests for Runnable object."""

    def test_no_loop_and_threded(self):
        """Test runnable fails on threaded mode and loop provided.."""
        with pytest.raises(
            ValueError,
        ):
            RunAndExit(loop=asyncio.get_event_loop(), threaded=True)

    def test_task_cancel_not_set(self):
        """Test task cancel."""

        class TestRun(Runnable):
            async def run(self):
                while True:
                    await asyncio.sleep(1)

        run = TestRun()
        run._task_cancel()

    @pytest.mark.asyncio
    async def test_runnable_async(self):
        """Test runnable async methods."""
        # for pydocstyle
        class TestRun(Runnable):
            async def run(self):
                while True:
                    await asyncio.sleep(1)

        run = TestRun()
        run.start()
        run.stop()
        await run.wait_completed()

        run = TestRun(threaded=True)
        run.start()
        run.stop()
        run.wait_completed(sync=True)

        run = RunAndExit()
        await run.start_and_wait_completed()

    def test_runnable_sync(self):
        """Test runnable sync methods."""
        run = RunAndExit()
        run.start_and_wait_completed(sync=True)

    @pytest.mark.asyncio
    async def test_double_start(self):
        """Test runnable async methods."""
        # for pydocstyle
        class TestRun(Runnable):
            async def run(self):
                while True:
                    await asyncio.sleep(1)

        run = TestRun()
        await run.wait_completed()
        assert run.start()
        assert not run.start()
        run.stop()
        await run.wait_completed()
        await run.wait_completed()

    @pytest.mark.asyncio
    async def test_run_in_thread(self):
        """Test runnable in thread mode."""
        # for pydocstyle
        class TestRun(Runnable):
            async def run(self):
                while True:
                    await asyncio.sleep(1)

        run = TestRun()
        t = Thread(target=run.start_and_wait_completed, kwargs=dict(sync=True))
        t.start()
        while not run.is_running:
            pass
        run.stop()
        t.join()

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test runnable async methods."""
        # for pydocstyle
        class TestRun(Runnable):
            def __init__(
                self, loop: asyncio.AbstractEventLoop = None, threaded: bool = False
            ) -> None:
                Runnable.__init__(self, loop=loop, threaded=threaded)
                self.started = False

            async def run(self):
                while True:
                    await asyncio.sleep(0.1)
                    self.started = True

        run = TestRun(threaded=True)
        run.start()
        wait_for_condition(lambda: run.started, timeout=5)
        with pytest.raises(asyncio.TimeoutError):
            run.wait_completed(sync=True, timeout=1)

        run.stop()
        run.wait_completed(sync=True)

        run = TestRun()
        run.start()
        await wait_for_condition_async(lambda: run.started, timeout=5)
        with pytest.raises(asyncio.TimeoutError):
            await run.wait_completed(timeout=1)
        run.stop()
        await run.wait_completed()

    @pytest.mark.asyncio
    async def test_exception(self):
        """Test runnable async methods."""
        # for pydocstyle
        import time

        class TestRun(Runnable):
            async def run(self):
                raise Exception("awaited")

        run = TestRun(threaded=True)
        run.start()
        time.sleep(0.1)
        with pytest.raises(Exception, match="awaited"):
            run.wait_completed(sync=True, timeout=1)

        run.stop()
        run.wait_completed(sync=True)

        run = TestRun()
        run.start()
        with pytest.raises(Exception, match="awaited"):
            await run.wait_completed(timeout=1)

        run.stop()
        await run.wait_completed()

    @pytest.mark.asyncio
    async def test_wait_async_threaded(self):
        """Test runnable async methods."""
        # for pydocstyle
        class TestRun(Runnable):
            async def run(self):
                raise Exception("awaited")

        run = TestRun(threaded=True)
        run.start()
        await asyncio.sleep(0.4)

        with pytest.raises(Exception, match="awaited"):
            await run.wait_completed(timeout=1)

        run.stop()
        await run.wait_completed()

    @pytest.mark.asyncio
    async def test_wait_async_threaded_no_exception(self):
        """Test runnable threaded wait completed."""
        # for pydocstyle
        class TestRun(Runnable):
            async def run(self):
                await asyncio.sleep(0.1)

        run = TestRun(threaded=True)
        run.start()
        await run.wait_completed()

    @pytest.mark.asyncio
    async def test_double_stop(self):
        """Test runnable double stop."""
        # for pydocstyle
        class TestRun(Runnable):
            async def run(self):
                await asyncio.sleep(0.1)

        run = TestRun()
        run.start()
        run.stop()
        run.stop()
        await run.wait_completed()

    def test_stop_before_run(self):
        """Test stop before run."""
        # for pydocstyle
        class TestRun(Runnable):
            async def run(self):
                await asyncio.sleep(0.1)

        run = TestRun()
        run.stop()
        run.start()
        time.sleep(1)
        assert not run.is_running
