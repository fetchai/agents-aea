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
"""Helper fot benchmark run control."""
from multiprocessing import Queue
from typing import Any


class BenchmarkControl:
    """Class to sync executor and function in test."""

    START_MSG = "start"

    def __init__(self):
        """Init."""
        self._queue = Queue(2)

    def start(self) -> None:
        """Notify executor to start measure resources."""
        self._queue.put(self.START_MSG)

    def wait_msg(self) -> Any:
        """Wait a message from function being tested."""
        return self._queue.get()
