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

"""This module contains the tests for the tasks module."""

from unittest import TestCase, mock

from aea.skills.tasks import Task, TaskManager, init_worker


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

    @mock.patch("aea.skills.tasks.logger.debug")
    def test_call_exception_while_executing(self, debug_mock):
        """Test call obj exception raised while executing."""
        obj = Task()
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

    @mock.patch("aea.skills.tasks.signal.signal")
    def test_init_worker_positive(self, signal_mock):
        """Test init_worker method positive result."""
        init_worker()
        signal_mock.assert_called_once()


class TaskManagerTestCase(TestCase):
    """Test case for TaskManager class."""

    def test_nb_workers_positive(self):
        """Test nb_workers property positive result."""
        obj = TaskManager()
        obj.nb_workers

    @mock.patch("aea.skills.tasks.logger.debug")
    def test_stop_already_stopped(self, debug_mock):
        """Test stop method already stopped."""
        obj = TaskManager()
        obj.stop()
        debug_mock.assert_called_once()

    @mock.patch("aea.skills.tasks.logger.debug")
    def test_start_already_started(self, debug_mock):
        """Test start method already started."""
        obj = TaskManager()
        obj._stopped = False
        obj.start()
        debug_mock.assert_called_once()

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
