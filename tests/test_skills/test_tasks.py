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

"""This module contains the tests for the tasks module."""

from unittest import TestCase, mock
from unittest.mock import Mock, patch

from aea.skills.tasks import Task, TaskManager


def _raise_exception(self, *args, **kwargs):
    raise Exception()


class TaskTestCase(TestCase):
    """Test case for Task class."""

    def test_call_positive(self):
        """Test call obj positive result."""
        obj = Task()
        obj.setup = mock.Mock()
        obj.execute = mock.Mock()
        obj.teardown = mock.Mock()
        obj()

    def test_call_already_executed(self):
        """Test call obj already executed."""
        obj = Task()
        obj._is_executed = True
        with self.assertRaises(ValueError):
            obj()

    def test_call_exception_while_executing(self):
        """Test call obj exception raised while executing."""
        obj = Task()
        with mock.patch.object(obj.logger, "debug") as debug_mock:
            obj.setup = mock.Mock()
            obj.execute = _raise_exception
            obj.teardown = mock.Mock()
            obj()
            debug_mock.assert_called_once()

    def test_is_executed_positive(self):
        """Test is_executed property positive result."""
        obj = Task()
        obj.is_executed

    def test_result_positive(self):
        """Test result property positive result."""
        obj = Task()
        obj._is_executed = True
        obj.result

    def test_result_not_executed(self):
        """Test result property task not executed."""
        obj = Task()
        with self.assertRaises(ValueError):
            obj.result


class InitWorkerTestCase(TestCase):
    """Test case for init_worker method."""

    @mock.patch("aea.skills.tasks._init_worker")
    def test_init_worker_positive(self, init_worker_mock):
        """Test init_worker method positive result."""
        task_manager = TaskManager(is_lazy_pool_start=False)
        task_manager.start()
        try:
            init_worker_mock.assert_called()
        finally:
            task_manager.stop()


class TaskManagerTestCase(TestCase):
    """Test case for TaskManager class."""

    def test_nb_workers_positive(self):
        """Test nb_workers property positive result."""
        obj = TaskManager()
        obj.nb_workers

    def test_stop_already_stopped(self):
        """Test stop method already stopped."""
        obj = TaskManager()
        with mock.patch.object(obj.logger, "debug") as debug_mock:
            obj.stop()
            debug_mock.assert_called_once()

    def test_start_already_started(self):
        """Test start method already started."""
        obj = TaskManager()
        with mock.patch.object(obj.logger, "debug") as debug_mock:
            obj._stopped = False
            obj.start()
            debug_mock.assert_called_once()
            obj.stop()

    def test_start_lazy_pool_start(self):
        """Test start method with lazy pool start."""
        obj = TaskManager(is_lazy_pool_start=False)
        with mock.patch.object(obj.logger, "debug") as debug_mock:
            obj.start()
            obj._stopped = True
            obj.start()
            debug_mock.assert_called_with("Pool was already started!")
            obj.start()

    def test_enqueue_task_stopped(self):
        """Test enqueue_task method manager stopped."""
        obj = TaskManager()
        func = mock.Mock()
        with self.assertRaises(ValueError):
            obj.enqueue_task(func)
            func.assert_not_called()

    def test_enqueue_task_positive(self):
        """Test enqueue_task method positive result."""
        obj = TaskManager()
        func = mock.Mock()
        obj._stopped = False
        obj._pool = mock.Mock()
        obj._pool.apply_async = mock.Mock(return_value="async_result")
        obj.enqueue_task(func)
        obj._pool.apply_async.assert_called_once()

    def test_get_task_result_id_not_present(self):
        """Test get_task_result method id not present."""
        obj = TaskManager()
        with self.assertRaises(ValueError):
            obj.get_task_result("task_id")

    def test_get_task_result_positive(self):
        """Test get_task_result method positive result."""
        obj = TaskManager()
        obj._results_by_task_id = {"task_id": "result"}
        obj.get_task_result("task_id")


class TestTaskPoolManagementManager(TestCase):
    """Tests for pool management by task manager. Lazy and non lazy."""

    def tearDown(self):
        """Stop task manager. assumed it's created on each test."""
        self.task_manager.stop()

    def test_start_stop_reflected_by_is_started(self) -> None:
        """Test is_started property of task manaher."""
        self.task_manager = TaskManager()
        assert not self.task_manager.is_started
        self.task_manager.start()
        assert self.task_manager.is_started

        self.task_manager.stop()
        assert not self.task_manager.is_started

    def test_lazy_pool_not_started(self) -> None:
        """Lazy pool creation assumes pool create on first task enqueue."""
        self.task_manager = TaskManager(is_lazy_pool_start=True)
        self.task_manager.start()
        assert not self.task_manager._pool

    def test_not_lazy_pool_is_started(self) -> None:
        """Lazy pool creation assumes pool create on first task enqueue."""
        self.task_manager = TaskManager(is_lazy_pool_start=False)
        self.task_manager.start()
        assert self.task_manager._pool

    @patch("aea.skills.tasks.Pool.apply_async")
    def test_lazy_pool_start_on_enqueue(self, apply_async_mock: Mock) -> None:
        """
        Test lazy pool created on enqueue once.

        :param apply_async_mock: is mock for aea.skills.tasks.Pool.apply_async
        """
        self.task_manager = TaskManager(is_lazy_pool_start=True)
        self.task_manager.start()
        assert not self.task_manager._pool

        self.task_manager.enqueue_task(print)

        apply_async_mock.assert_called_once()
        assert self.task_manager._pool

        """Check pool created once on several enqueues"""
        pool = self.task_manager._pool

        self.task_manager.enqueue_task(print)

        assert self.task_manager._pool is pool
