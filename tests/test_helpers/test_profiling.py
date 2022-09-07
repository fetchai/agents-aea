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
"""This module contains the tests for the helpers/profiling module."""
import platform
import re
from typing import Dict, List, Optional

import pytest

from aea.helpers.profiling import Profiling
from aea.protocols.base import Message

from tests.common.utils import wait_for_condition


if platform.system() == "Windows":  # pragma: nocover
    import win32timezone  # type: ignore  # pylint: disable=import-error,import-outside-toplevel,unsed-import

    _ = win32timezone

    import win32process  # type: ignore  # pylint: disable=import-error,import-outside-toplevel,unsed-import # noqa: F401

MESSAGE_NUMBER = 10


class DummyClass:
    """Dummy class for counting purposes"""


class MessageContainer:
    """Dummy class for counting purposes"""

    def __init__(
        self, other: Optional["MessageContainer"] = None, message_number=MESSAGE_NUMBER
    ) -> None:
        """Initializer"""
        self.messages: List[Message] = (
            other.messages if other else [Message() for _ in range(message_number)]
        )


result = ""


def output_function(report):
    """Test output function"""
    global result
    result = report


def extract_object_counts(log: str) -> Dict[str, Dict[str, int]]:
    """Extract object counts from the profiling log."""
    result: Dict[str, Dict[str, int]] = {"created": {}, "present": {}, "gc": {}}

    for line in log.split("\n"):
        # Created (tracked objects)
        match = re.match(r".*\* (?P<field>.*) \(present\):  (?P<count>\d+).*", line)
        if match:
            result["present"][match.groupdict()["field"]] = int(
                match.groupdict()["count"]
            )
            continue

        # Present (tracked objects)
        match = re.match(r".*\* (?P<field>.*) \(created\):  (?P<count>\d+).*", line)
        if match:
            result["created"][match.groupdict()["field"]] = int(
                match.groupdict()["count"]
            )
            continue

        # Present (garbage collector)
        match = re.match(r".*\* (?P<field>.*) \(gc\):  (?P<count>\d+).*", line)
        if match:
            result["gc"][match.groupdict()["field"]] = int(match.groupdict()["count"])

    return result


def test_basic_profiling():
    """Test profiling tool."""
    global result
    result = ""

    p = Profiling([Message], 1, output_function=output_function)
    p.start()

    wait_for_condition(lambda: p.is_running, timeout=20)
    m = Message()
    try:
        wait_for_condition(lambda: result, timeout=20)

        assert "Profiling details" in result
    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=20)
    del m


@pytest.mark.profiling
def test_profiling_instance_number():
    """Test profiling tool."""
    global result
    result = ""

    # Generate some dummy classes to check that they appear in the gc counter
    dummy_classes_to_count = [DummyClass() for _ in range(1000)]

    p = Profiling([Message], 1, output_function=output_function)
    p.start()

    wait_for_condition(lambda: p.is_running, timeout=20)

    # Create some messages
    messages = [Message() for _ in range(MESSAGE_NUMBER)]

    try:
        # Check the number of created and present messages
        wait_for_condition(lambda: result, timeout=20)

        count_dict = extract_object_counts(result)

        assert count_dict["created"] == {"Message": MESSAGE_NUMBER}
        assert count_dict["present"] == {"Message": MESSAGE_NUMBER}
        assert count_dict["gc"]["DummyClass"] == len(dummy_classes_to_count)

        # Modify the number of messages
        messages = messages[: int(MESSAGE_NUMBER / 2)]
        result = ""

        # Check the number of created and present objects
        wait_for_condition(lambda: result, timeout=20)

        count_dict = extract_object_counts(result)

        assert count_dict["created"] == {"Message": MESSAGE_NUMBER}
        assert count_dict["present"] == {"Message": int(MESSAGE_NUMBER / 2)}

        # Modify the number of messages
        messages += [Message() for _ in range(len(messages))]
        result = ""

        # Check the number of created and present objects
        wait_for_condition(lambda: result, timeout=20)

        count_dict = extract_object_counts(result)

        assert count_dict["created"] == {
            "Message": MESSAGE_NUMBER + int(MESSAGE_NUMBER / 2)
        }
        assert count_dict["present"] == {"Message": MESSAGE_NUMBER}

    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=20)
    del messages


@pytest.mark.profiling
def test_profiling_cross_reference():
    """Test profiling tool."""
    global result
    result = ""

    p = Profiling(
        [Message, MessageContainer],
        1,
        output_function=output_function,
    )
    p.start()

    wait_for_condition(lambda: p.is_running, timeout=20)

    container_a = MessageContainer()  # contains new messages
    MessageContainer(container_a)  # shares the same messages with a

    try:
        # Check the number of created and present objects
        wait_for_condition(lambda: result, timeout=20)

        count_dict = extract_object_counts(result)

        assert count_dict["created"] == {
            "Message": MESSAGE_NUMBER,
            "MessageContainer": 2,
        }
        assert count_dict["present"] == {
            "Message": MESSAGE_NUMBER,
            "MessageContainer": 1,
        }

    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=20)


def test_profiling_counts_not_equal():
    """Test profiling tool."""
    global result
    result = ""

    p = Profiling(
        [Message, MessageContainer, DummyClass],
        1,
        output_function=output_function,
    )
    p.start()

    wait_for_condition(lambda: p.is_running, timeout=20)

    # Generate some dummy classes to check that they appear in the gc counter
    _ = [  # noqa: F841 we need to store the objects so they appear in the gc
        DummyClass() for _ in range(1000)
    ]

    container_a = MessageContainer()  # contains new messages
    MessageContainer(container_a)  # shares the same messages with a

    try:
        # Check the number of created and present objects
        wait_for_condition(lambda: result, timeout=20)

        count_dict = extract_object_counts(result)
        assert (
            len(set(count_dict["present"].values())) == 3
        ), "All element counts are equal"
        assert (
            len(set(count_dict["created"].values())) == 3
        ), "All element counts are equal"
        assert len(set(count_dict["gc"].values())) > 1, "All element counts are equal"

    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=20)
