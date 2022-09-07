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
from typing import Any, Callable
from typing import Counter as CounterType
from typing import Dict, List, Tuple, Type

from aea.helpers.async_utils import Runnable
from aea.helpers.profiler_type_black_list import PROFILER_TYPE_BLACK_LIST


BYTES_TO_MBYTES = 1024**-2

lock = threading.Lock()

_default_logger = logging.getLogger(__file__)

if platform.system() == "Windows":  # pragma: nocover

    import win32process  # type: ignore  # pylint: disable=import-error,import-outside-toplevel

    WIN32_PROCESS_TIMES_TICKS_PER_SECOND = 1e7

    def get_current_process_memory_usage() -> float:
        """Get current process memory usage in MB."""
        d = win32process.GetProcessMemoryInfo(win32process.GetCurrentProcess())  # type: ignore
        return float(d["WorkingSetSize"]) * BYTES_TO_MBYTES

    def get_peak_process_memory_usage() -> float:
        """Get current process memory usage in MB."""
        d = win32process.GetProcessMemoryInfo(win32process.GetCurrentProcess())  # type: ignore
        return float(d["PeakWorkingSetSize"]) * BYTES_TO_MBYTES

    def get_current_process_cpu_time() -> float:
        """Get current process cpu time in seconds."""
        d = win32process.GetProcessTimes(win32process.GetCurrentProcess())  # type: ignore
        return d["UserTime"] / WIN32_PROCESS_TIMES_TICKS_PER_SECOND

else:
    import resource
    import tracemalloc

    def get_current_process_memory_usage() -> float:
        """Get current process memory usage in MB."""
        return tracemalloc.get_traced_memory()[0] * BYTES_TO_MBYTES

    def get_peak_process_memory_usage() -> float:
        """Get current process memory usage in MB."""
        return tracemalloc.get_traced_memory()[1] * BYTES_TO_MBYTES

    def get_current_process_cpu_time() -> float:
        """Get current process cpu time in seconds."""
        return resource.getrusage(resource.RUSAGE_SELF).ru_utime


class Profiling(Runnable):
    """Profiling service."""

    def __init__(
        self,
        types_to_track: List[Type],
        period: int = 0,
        output_function: Callable[[str], None] = lambda x: print(x, flush=True),
    ) -> None:
        """
        Init profiler.

        :param period: delay between profiling output in seconds.
        :param types_to_track: object types to count
        :param output_function: function to display output, one str argument.
        """
        if period < 1:  # pragma: nocover
            raise ValueError("Profiling frequency should be at least 1 second!")
        super().__init__(threaded=True)
        self._period = period
        self._start_ts = time.time()
        self._types_to_track: List[Type] = types_to_track
        self._output_function = output_function
        self.object_counts: Dict[Type, List[int]] = {
            obj: [0, 0] for obj in types_to_track
        }  # {object: [instances_created, instances_deleted]}
        self.set_counters()

        if platform.system() != "Windows":
            tracemalloc.start()

    def set_counters(self) -> None:
        """Modify __new__ and __del__ to count objects created created and destroyed."""

        def call_count(wrapped: Callable, index: int, obj: Any) -> Callable:
            orig_new = obj.__new__

            @wraps(wrapped)
            def wrapper(*args: Any, **kwargs: Any) -> Callable:
                self.object_counts[obj][index] += 1
                # Avoid TypeError: object.__new__() takes exactly one argument
                if orig_new is object.__new__:
                    return orig_new(args[0])  # pragma: nocover
                return wrapped(*args, **kwargs)

            return wrapper

        for t in self._types_to_track:
            t.__new__ = call_count(t.__new__, 0, t)
            # For some reason, if we don't init the __del__ method with an empty function, the next
            # line will raise the exception: AttributeError: type object 'Message' has no attribute '__del__'
            t.__del__ = lambda _: None
            t.__del__ = call_count(t.__del__, 1, t)

    async def run(self) -> None:
        """Run profiling."""
        try:
            while True:
                await asyncio.sleep(self._period)
                self.output_profile_data()
        except CancelledError:  # pragma: nocover
            pass
        except Exception:  # pragma: nocover
            _default_logger.exception("Exception in Profiling")
            raise
        finally:
            if platform.system() != "Windows":
                tracemalloc.stop()

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
        Memory: {data["mem"]:.6f} MB [Peak {data["mem_peak"]:.6f} MB]
        Threads: {data["threads"]['amount']}  {data["threads"]['names']}
        Objects present:
        """
            )
            + "\n".join(
                [
                    f" * {i.__name__} (present):  {c}"
                    for i, c in data["objects_present"].items()
                ]
            )
            + "\n"
            + """Objects created:\n"""
            + "\n".join(
                [
                    f" * {i.__name__} (created):  {c}"
                    for i, c in data["objects_created"].items()
                ]
            )
            + "\n"
            + """Most common objects in garbage collector (excluding blacklisted):\n"""
            + "\n".join(
                [f" * {i[0]} (gc):  {i[1]}" for i in data["most_common_objects_in_gc"]]
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
            "mem_peak": get_peak_process_memory_usage(),
            "threads": {
                "amount": threading.active_count(),
                "names": [i.name for i in threading.enumerate()],
            },
            "objects_present": {k: v[0] - v[1] for k, v in self.object_counts.items()},
            "objects_created": {k: v[0] for k, v in self.object_counts.items()},
            "most_common_objects_in_gc": get_most_common_objects_in_gc(),
        }


def get_most_common_objects_in_gc(number: int = 15) -> List[Tuple[str, int]]:
    """Get the highest-count objects in the garbage collector."""

    object_count: CounterType = Counter()
    lock.acquire()
    try:
        for obj in gc.get_objects():
            object_type = str(
                getattr(obj, "__class__", type(obj)).__name__
            )  # not all objects have the __class__ attribute
            if object_type not in PROFILER_TYPE_BLACK_LIST:
                object_count[object_type] += 1
    finally:
        lock.release()
    return object_count.most_common(number)
