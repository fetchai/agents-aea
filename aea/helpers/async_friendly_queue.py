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

"""This module contains the implementation of AsyncFriendlyQueue."""
import asyncio
import queue
from collections import deque
from contextlib import suppress
from typing import Any


class AsyncFriendlyQueue(queue.Queue):
    """queue.Queue with async_get method."""

    def __init__(self, *args, **kwargs):
        """Init queue."""
        super().__init__(*args, **kwargs)
        self._non_empty_waiters = deque()

    def put(  # pylint: disable=signature-differs
        self, item: Any, *args, **kwargs
    ) -> None:
        """
        Put an item into the queue.

        :param item: item to put in the queue
        :param args, kwargs: similar to queue.Queue.put
        """
        super().put(item, *args, **kwargs)
        if self._non_empty_waiters:
            waiter = self._non_empty_waiters.popleft()
            waiter._loop.call_soon_threadsafe(  # pylint: disable=protected-access
                self._set_waiter, waiter
            )

    @staticmethod
    def _set_waiter(waiter) -> None:
        """Set waiter result."""
        if waiter.done():  # pragma: nocover
            return
        waiter.set_result(True)

    def get(self, *args, **kwargs) -> Any:  # pylint: disable=signature-differs
        """
        Get an item into the queue.

        :param args, kwargs: similar to queue.Queue.get
        """
        return super().get(*args, **kwargs)

    async def async_wait(self) -> None:
        """
        Wait an item appears in the queue.

        :return: None
        """
        if not self.empty():
            return
        waiter = asyncio.Future()  # type: ignore
        self._non_empty_waiters.append(waiter)
        try:
            await waiter
        finally:
            try:
                self._non_empty_waiters.remove(waiter)
            except ValueError:
                pass

    async def async_get(self) -> Any:
        """
        Wait and get an item from the queue.

        :return: item from queue
        """
        while True:
            await self.async_wait()

            with suppress(queue.Empty):
                item = self.get_nowait()
                return item
