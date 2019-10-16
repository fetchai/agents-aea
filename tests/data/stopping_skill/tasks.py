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

"""This module contains the tasks for the 'stop' skill."""
import datetime

from aea.skills.base import Task


class StopTask(Task):
    """Dummy task."""

    def __init__(self, **kwargs):
        """Initialize the task."""
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.timeout = kwargs.get("timeout", 3.0)
        self.enabled = kwargs.get("enabled", False)

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self.start_time = datetime.datetime.now()
        self.end_time = self.start_time + datetime.timedelta(0, self.timeout)

    def execute(self) -> None:
        """Execute the task."""
        if self.enabled and datetime.datetime.now() > self.end_time:
            self.context.liveness._is_stopped = True

    def teardown(self) -> None:
        """Teardown the task."""
