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
"""This module contains the behaviours for the 'test task skill' skill."""
from typing import Optional

from aea.skills.behaviours import TickerBehaviour
from aea.skills.tasks import Task

from packages.fetchai.skills.task_test_skill.tasks import SimpleTask


class TaskBehaviour(TickerBehaviour):
    """Echo behaviour."""

    task_id: Optional[int]
    task: Task

    def setup(self) -> None:
        """Set up the behaviour."""
        self.context.logger.info("Task Behaviour: setup method called.")
        self.task = SimpleTask("some data")
        self.task_id = None

    def act(self) -> None:
        """Act according to the behaviour."""
        self.context.logger.info("Task Behaviour: act method called.")
        if self.task_id is None:
            self.set_task()
        else:
            self.get_task_result()

    def set_task(self) -> None:
        """Set background task to run."""
        if self.task_id:
            return
        self.task_id = self.context.task_manager.enqueue_task(self.task)
        self.context.logger.info("Task set.")

    def get_task_result(self) -> None:
        """Get result of the task."""
        if self.task_id is None:
            return
        async_result = self.context.task_manager.get_task_result(self.task_id)
        if not async_result.ready():
            return
        self.context.logger.info(f"Task result is ready: {async_result.get()}")
        self.task_id = None

    def teardown(self) -> None:
        """Teardown the behaviour."""
        self.context.logger.info("Task Behaviour: teardown method called.")
