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
"""This module contains the tests for the task manager."""
from multiprocessing.pool import AsyncResult

import pytest

from aea.skills.tasks import Task, TaskManager


class MyTask(Task):
    """Test class for a task."""

    def __init__(self, return_value):
        """Initialise test task."""
        super().__init__()
        self.setup_called = False
        self.teardown_called = False
        self.execute_called = False
        self.execute_args = None
        self.execute_kwargs = None
        self.return_value = return_value

    def setup(self) -> None:
        """Setup task."""
        self.setup_called = True

    def execute(self, *args, **kwargs) -> None:
        """Execute task."""
        self.execute_called = True
        self.execute_args = args
        self.execute_kwargs = kwargs
        return self.return_value

    def teardown(self) -> None:
        """Teardown task."""
        self.teardown_called = True


class TestTaskManager:
    """Test the features of the task manager."""

    WAIT_TIMEOUT = 20.0

    def _return_a_constant(self, a: int, b: int = 10):
        return a + b

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.task_manager = TaskManager(nb_workers=5)
        cls.task_manager.start()

    def test_task_manager_function_with_default_arguments(self):
        """Test a function submitted to the task manager with default arguments."""
        task_id = self.task_manager.enqueue_task(self._return_a_constant, args=(32,))
        task_result = self.task_manager.get_task_result(task_id)
        assert isinstance(task_result, AsyncResult)
        result = task_result.get(self.WAIT_TIMEOUT)
        assert result == 42

    def test_task_manager_function_with_keyword_arguments(self):
        """Test a function submitted to the task manager with keyword arguments."""
        task_id = self.task_manager.enqueue_task(
            self._return_a_constant, args=(32,), kwds={"b": 10}
        )
        task_result = self.task_manager.get_task_result(task_id)
        assert isinstance(task_result, AsyncResult)
        result = task_result.get(self.WAIT_TIMEOUT)
        assert result == 42

    def test_task_manager_function_with_wrong_argument_number(self):
        """Test wrong number of arguments."""
        task_id = self.task_manager.enqueue_task(
            self._return_a_constant, args=(), kwds={"b": 10}
        )
        task_result = self.task_manager.get_task_result(task_id)
        assert isinstance(task_result, AsyncResult)
        with pytest.raises(TypeError, match="missing .+ required positional argument:"):
            task_result.get(self.WAIT_TIMEOUT)

    def test_task_manager_task_object(self):
        """Test task manager with task object."""
        expected_args = (0, 1)
        expected_kwargs = {"a": 0, "b": 2}
        expected_return_value = 42
        my_task = MyTask(return_value=expected_return_value)
        task_id = self.task_manager.enqueue_task(
            my_task, args=expected_args, kwds=expected_kwargs
        )
        task_result = self.task_manager.get_task_result(task_id)
        assert isinstance(task_result, AsyncResult)

        expected_task = task_result.get(self.WAIT_TIMEOUT)
        assert expected_task.result == expected_return_value
        assert expected_task.setup_called
        assert expected_task.execute_called
        assert expected_task.teardown_called
        assert expected_task.execute_args == expected_args
        assert expected_task.execute_kwargs == expected_kwargs

        # the original instance is different than the one returned by the task manager.
        with pytest.raises(ValueError):
            result = my_task.result  # noqa
        assert not my_task.is_executed
        assert not my_task.setup_called
        assert not my_task.execute_called
        assert not my_task.teardown_called
        assert my_task.execute_args is None
        assert my_task.execute_kwargs is None

    def test_task_manager_task_object_fails_when_not_pickable(self):
        """Test task manager with task object fails when the task is not pickable."""
        expected_args = [lambda x: x]
        my_task = MyTask(return_value=None)
        task_id = self.task_manager.enqueue_task(my_task, args=expected_args)
        task_result = self.task_manager.get_task_result(task_id)
        assert isinstance(task_result, AsyncResult)

        with pytest.raises(AttributeError, match="Can't pickle local object"):
            expected_task = task_result.get(self.WAIT_TIMEOUT)  # noqa

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        cls.task_manager.stop()
