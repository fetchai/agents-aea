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
"""This module contains the tests for the helpers.multiple_executor."""

import asyncio
from asyncio.events import AbstractEventLoop

from aea.helpers.multiple_executor import AbstractExecutorTask, TaskAwaitable


class Task(AbstractExecutorTask):
    """Simple Executor Task for testing."""

    def start(self):
        """Implement start task function here."""
        pass

    def stop(self) -> None:
        """Implement stop task function here."""
        pass

    def create_async_task(self, loop: AbstractEventLoop) -> TaskAwaitable:
        """
        Create asyncio task for task run in asyncio loop.

        :param loop: the event loop
        :return: task to run in asyncio loop.
        """
        pass


def test_task_failed():
    """Test task failed."""
    task = Task()
    assert not task.failed

    task.future = asyncio.Future()
    assert not task.failed

    task.future.set_result(None)

    assert not task.failed

    task.future = asyncio.Future()
    task.future.set_exception(KeyboardInterrupt())

    assert not task.failed

    task.future = asyncio.Future()
    task.future.set_exception(ValueError())

    assert task.failed
