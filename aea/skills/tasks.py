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

"""This module contains the classes for tasks."""
import threading
from collections import deque
from concurrent.futures import Executor, ThreadPoolExecutor
from queue import Queue
from threading import Thread
from typing import Optional

from aea.skills.base import Task


class TaskManager:
    """A Task manager."""

    def __init__(self, executor: Optional[Executor] = None):
        self._executor = executor if executor is not None else ThreadPoolExecutor()

        self.task_queue = Queue()
        self.futures = deque([])

        self.stopped = True
        self.thread = Thread(target=self.dispatch)
        self.lock = threading.Lock()

    def enqueue_task(self, task: Task):
        self.task_queue.put(task)

    def dispatch(self):
        while not self.stopped:
            next_task = self.task_queue.get(block=True)  # type: Optional[Task]
            if next_task is None:
                return

            future = self._executor.submit(next_task.execute)
            self.futures.append(future)

    def start(self):
        with self.lock:
            self.stopped = False
            self.thread.start()

    def stop(self):
        with self.lock:
            self.stopped = True
            self.task_queue.put(None)
            self.thread.join()
