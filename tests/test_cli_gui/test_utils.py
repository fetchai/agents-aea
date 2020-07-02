# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Test module for utils of CLI GUI."""

from subprocess import TimeoutExpired  # nosec
from unittest import TestCase, mock

from aea.cli_gui.utils import (
    ProcessState,
    _call_subprocess,
    _terminate_process,
    get_process_status,
    read_error,
    read_tty,
)


def _raise_timeout_expired(*args, **kwargs):
    raise TimeoutExpired("cmd", None)


@mock.patch("aea.cli_gui.utils._terminate_process")
@mock.patch("aea.cli_gui.utils.logging.exception")
@mock.patch("aea.cli_gui.utils.subprocess.Popen")
class CallSubprocessTestCase(TestCase):
    """Test case for _call_subprocess method."""

    def test__call_subprocess_positive(self, popen_mock, exc_mock, terminate_mock):
        """Test _call_subprocess for positive result."""
        proc_mock = mock.Mock()
        proc_mock.wait = mock.Mock(return_value="wait-return")
        popen_mock.return_value = proc_mock

        result = _call_subprocess("arg1")
        expected_result = "wait-return"

        self.assertEqual(result, expected_result)
        popen_mock.assert_called_once_with("arg1")
        proc_mock.wait.assert_called_once()
        exc_mock.assert_not_called()
        terminate_mock.assert_called_once_with(proc_mock)

    def test__call_subprocess_negative(self, popen_mock, exc_mock, terminate_mock):
        """Test _call_subprocess for negative result."""
        proc_mock = mock.Mock()
        proc_mock.wait = _raise_timeout_expired
        popen_mock.return_value = proc_mock

        result = _call_subprocess("arg1")
        expected_result = -1

        self.assertEqual(result, expected_result)
        popen_mock.assert_called_once_with("arg1")
        exc_mock.assert_called_once()
        terminate_mock.assert_called_once_with(proc_mock)


@mock.patch("aea.cli_gui.utils.logging.info")
@mock.patch("aea.cli_gui.utils.io.TextIOWrapper")
class ReadTtyTestCase(TestCase):
    """Test case for read_tty method."""

    def test_read_tty_positive(self, text_wrapper_mock, logging_info_mock):
        """Test read_tty method for positive result."""
        text_wrapper_mock.return_value = ["line3", "line4"]
        pid_mock = mock.Mock()
        pid_mock.stdout = "stdout"

        str_list = ["line1", "line2"]
        read_tty(pid_mock, str_list)
        expected_result = ["line1", "line2", "line3", "line4", "process terminated\n"]
        self.assertEqual(str_list, expected_result)
        text_wrapper_mock.assert_called_once_with("stdout", encoding="utf-8")


@mock.patch("aea.cli_gui.utils.logging.error")
@mock.patch("aea.cli_gui.utils.io.TextIOWrapper")
class ReadErrorTestCase(TestCase):
    """Test case for read_error method."""

    def test_read_error_positive(self, text_wrapper_mock, logging_error_mock):
        """Test read_error method for positive result."""
        text_wrapper_mock.return_value = ["line3", "line4"]
        pid_mock = mock.Mock()
        pid_mock.stderr = "stderr"

        str_list = ["line1", "line2"]
        read_error(pid_mock, str_list)
        expected_result = ["line1", "line2", "line3", "line4", "process terminated\n"]
        self.assertEqual(str_list, expected_result)
        text_wrapper_mock.assert_called_once_with("stderr", encoding="utf-8")


class TerminateProcessTestCase(TestCase):
    """Test case for _terminate_process method."""

    def test__terminate_process_positive(self):
        """Test _terminate_process for positive result."""
        process_mock = mock.Mock()
        process_mock.poll = mock.Mock(return_value="Not None")
        _terminate_process(process_mock)

        process_mock.poll = mock.Mock(return_value=None)
        process_mock.terminate = mock.Mock()
        process_mock.wait = _raise_timeout_expired
        process_mock.kill = mock.Mock()

        _terminate_process(process_mock)
        process_mock.poll.assert_called_once()
        process_mock.terminate.assert_called_once()
        process_mock.kill()


class GetProcessStatusTestCase(TestCase):
    """Test case for get_process_status method."""

    def test_get_process_status_positive(self):
        """Test get_process_status for positive result."""
        proc_id_mock = mock.Mock()

        proc_id_mock.poll = mock.Mock(return_value=-1)
        result = get_process_status(proc_id_mock)
        expected_result = ProcessState.FINISHED
        self.assertEqual(result, expected_result)

        proc_id_mock.poll = mock.Mock(return_value=1)
        result = get_process_status(proc_id_mock)
        expected_result = ProcessState.FAILED
        self.assertEqual(result, expected_result)
