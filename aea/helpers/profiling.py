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
from concurrent.futures._base import CancelledError
from functools import wraps
from typing import Any, Callable, Dict, List, Type

from aea.helpers.async_utils import Runnable


lock = threading.Lock()

_default_logger = logging.getLogger(__file__)

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

    _MAC_MEM_STATS_MB = 1024 ** 2
    _LINUX_MEM_STATS_MB = 1024

    def get_current_process_memory_usage() -> float:
        """Get current process memory usage in MB."""
        if platform.system() == "Darwin":  # pragma: nocover
            divider = _MAC_MEM_STATS_MB
        else:
            divider = _LINUX_MEM_STATS_MB

        return 1.0 * resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / divider

    def get_current_process_cpu_time() -> float:
        """Get current process cpu time in seconds."""
        return resource.getrusage(resource.RUSAGE_SELF).ru_utime


class Profiling(Runnable):
    """Profiling service."""

    def __init__(
        self,
        period: int = 0,
        objects_instances_to_count: List[Type] = None,
        objects_created_to_count: List[Type] = None,
        output_function: Callable[[str], None] = lambda x: print(x, flush=True),
    ) -> None:
        """
        Init profiler.

        :param period: delay between profiling output in seconds.
        :param objects_instances_to_count: object to count
        :param objects_created_to_count: object created to count
        :param output_function: function to display output, one str argument.
        """
        if period < 1:  # pragma: nocover
            raise ValueError("Period should be at least 1 second!")
        super().__init__(threaded=True)
        self._period = period
        self._start_ts = time.time()
        self._objects_instances_to_count = objects_instances_to_count or []
        self._objects_created_to_count = objects_created_to_count or []
        self._output_function = output_function
        self._counter: Dict[Type, int] = Counter()

    def set_counters(self) -> None:
        """Modify obj.__new__ to count objects created created."""
        for obj in self._objects_created_to_count:
            self._counter[obj] = 0

            def make_fn(obj: Any) -> Callable:
                orig_new = obj.__new__
                # pylint: disable=protected-access  # type: ignore

                @wraps(orig_new)
                def new(*args: Any, **kwargs: Any) -> Callable:
                    self._counter[obj] += 1
                    if orig_new is object.__new__:
                        return orig_new(args[0])  # pragma: nocover
                    return orig_new(*args, **kwargs)  # pragma: nocover

                return new

            obj.__new__ = make_fn(obj)  # type: ignore

    async def run(self) -> None:
        """Run profiling."""
        try:
            self.set_counters()
            while True:
                await asyncio.sleep(self._period)
                self.output_profile_data()
        except CancelledError:  # pragma: nocover
            pass
        except Exception:  # pragma: nocover
            _default_logger.exception("Exception in Profiling")
            raise

    def output_profile_data(self) -> None:
        """Render profiling data and call output_function."""
        data = self.get_profile_data()
        text = (
            textwrap.dedent(
                f"""
        Profiling details for current AEA process: {datetime.datetime.now()}
        =============================================
        Run time: {data["run_time"]:.6f} seconds
        Cpu time: {data["cpu_time"]:.6f} seconds,
        Cpu/Run time: {100*data["cpu_time"]/data["run_time"]:.6f}%
        Memory: {data["mem"]:.6f} MB
        Threads: {data["threads"]['amount']}  {data["threads"]['names']}
        Objects present:
        """
            )
            + "\n".join([f" * {i}:  {c}" for i, c in data["objects_present"].items()])
            + "\n"
            + """Objects created:\n"""
            + "\n".join(
                [f" * {i.__name__}:  {c}" for i, c in data["objects_created"].items()]
            )
            + "\n"
        )
        self._output_function(text)

    def get_profile_data(self) -> Dict:
        """Get profiling data dict."""
        return {
            "run_time": time.time() - self._start_ts,
            "cpu_time": get_current_process_cpu_time(),
            "mem": get_current_process_memory_usage(),
            "threads": {
                "amount": threading.active_count(),
                "names": [i.name for i in threading.enumerate()],
            },
            "objects_present": self.get_objects_instances(),
            "objects_created": self.get_objecst_created(),
        }

    def get_objects_instances(self) -> Dict:
        """Return dict with counted object instances present now."""
        result: Dict = Counter()

        lock.acquire()
        try:
            for obj_type in self._objects_instances_to_count:
                result[obj_type.__name__] += 0

            for obj in gc.get_objects():
                for obj_type in self._objects_instances_to_count:
                    if isinstance(obj, obj_type):
                        result[obj_type.__name__] += 1
        finally:
            lock.release()
        return result

    def get_objecst_created(self) -> Dict:
        """Return dict with counted object instances created."""
        return self._counter
