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
"""Implementation of background profiling daemon."""

import asyncio
import datetime
import gc
import logging
import platform
import textwrap
import threading
import time
from collections import Counter
from typing import Callable

from aea.connections.base import Connection
from aea.helpers.async_utils import Runnable
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea.skills.base import Behaviour, Handler


logger = logging.getLogger(__file__)

if platform.system() == "Windows":  # pragma: nocover
    import win32process  # type: ignore  # pylint: disable=import-error

    WIN32_PROCESS_TIMES_TICKS_PER_SECOND = 1e7

    def get_current_process_memory_usage() -> float:
        """Get current process memory usage in MB."""
        d = win32process.GetProcessMemoryInfo(win32process.GetCurrentProcess())  # type: ignore
        return 1.0 * d["WorkingSetSize"] / 1024 ** 2

    def get_current_process_cpu_time() -> float:
        """Get current process cpu time in seconds."""
        d = win32process.GetProcessTimes(win32process.GetCurrentProcess())  # type: ignore
        return d["UserTime"] / WIN32_PROCESS_TIMES_TICKS_PER_SECOND


else:
    import resource

    if platform.system() == "Darwin":  # pragma: nocover
        divider = 1024 ** 2
    else:
        divider = 1024

    def get_current_process_memory_usage() -> float:
        """Get current process memory usage in MB."""
        return 1.0 * resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / divider

    def get_current_process_cpu_time() -> float:
        """Get current process cpu time in seconds."""
        return resource.getrusage(resource.RUSAGE_SELF).ru_utime


class Profiling(Runnable):
    """Profiling service."""

    OBJECTS = [Message, Dialogue, Handler, Behaviour, Connection]

    def __init__(
        self,
        period: int = 0,
        output_function: Callable[[str], None] = lambda x: print(x, flush=True),
    ) -> None:
        """
        Init profiler.

        :param period: delay between profiling output in seconds.
        :param output_function: function to display ouput, one str argument.
        """
        if period < 1:  # pragma: nocover
            raise ValueError("Period should be at least 1 second!")
        super().__init__(threaded=True)
        self._period = period
        self._start_ts = time.time()
        self._messages_count = 0
        self._output_function = output_function

    def set_messages_counter(self) -> None:
        """Modify Message.__new__ to count messages created."""
        orig_new = Message.__new__  # pylint: disable=protected-access  # type: ignore

        def new(*args, **kwargs) -> Message:
            self._messages_count += 1
            return orig_new(*args, **kwargs)

        Message.__new__ = new  # type: ignore

    async def run(self) -> None:
        """Run profiling."""
        try:
            self.set_messages_counter()
            while True:
                await asyncio.sleep(self._period)
                await self.output_profile_data()
        except Exception:  # pragma: nocover
            logger.exception("Exception in Profiling")
            raise

    async def output_profile_data(self) -> None:
        """Render profiling data and call output_function."""
        data = self.get_profile_data()
        text = (
            textwrap.dedent(
                f"""
        Profiling details: {datetime.datetime.now()}
        =============================================
        Run time: {data["run_time"]} seconds
        Cpu time: {data["cpu_time"]} seconds
        Memory: {data["mem"]} MB
        Threads: {data["threads"]}
        Messages constructed: {data["messages_contstructed"]}
        Objects stats:
        """
            )
            + "\n".join([f" * {i}:  {c}" for i, c in data["objects"].items()])
            + "\n"
        )
        self._output_function(text)

    def get_profile_data(self) -> dict:
        """Get profiling data dict."""
        return {
            "run_time": time.time() - self._start_ts,
            "cpu_time": get_current_process_cpu_time(),
            "mem": get_current_process_memory_usage(),
            "threads": threading.active_count(),
            "objects": self.get_object_amount(),
            "messages_contstructed": self._messages_count,
        }

    def get_object_amount(self) -> dict:
        """Return dict with counted object instances present now."""
        result: dict = Counter()

        for obj_type in self.OBJECTS:
            result[obj_type.__name__] += 0

        for obj in gc.get_objects():
            for obj_type in self.OBJECTS:
                if isinstance(obj, obj_type):
                    result[obj_type.__name__] += 1
        return result
