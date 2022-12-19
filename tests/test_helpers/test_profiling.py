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
    # type: ignore  # pylint: disable=import-error,import-outside-toplevel,unsed-import
    import win32timezone  # type: ignore

    _ = win32timezone

    import win32process  # type: ignore  # pylint: disable=import-error,import-outside-toplevel,unsed-import # noqa: F401


TIMEOUT = 20
MESSAGE_NUMBER = 10
DUMMIES_NUMBER = 1000


class DummyClass:
    """Dummy class for counting purposes"""


class MessageContainer:
    """Dummy class for counting purposes"""

    def __init__(self, other: Optional["MessageContainer"] = None) -> None:
        """Initializer"""
        self.messages: List[Message] = other.messages if other else create_messages()


def __create_two_return_one() -> MessageContainer:
    """Create two message containers return only one referencing the same messages"""
    # create MessageContainer twice, Messages in them only once (shared)
    # only one of them is tracked by garbage collector, as the inner is unbound
    return MessageContainer(MessageContainer())


def create_dummies() -> List[DummyClass]:
    """Create n dummy class instances"""
    return [DummyClass() for _ in range(DUMMIES_NUMBER)]


def create_messages() -> List[Message]:
    """Create n messages"""
    return [Message() for _ in range(MESSAGE_NUMBER)]


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

    def output_function(report):
        """Test output function"""
        nonlocal result
        result = report

    result, types_to_track = "", [Message]
    p = Profiling(types_to_track, 1, output_function=output_function)
    p.start()
    m = Message()
    del m
    wait_for_condition(lambda: p.is_running, timeout=TIMEOUT)

    try:
        wait_for_condition(lambda: result, timeout=TIMEOUT)
        assert "Profiling details" in result
        assert p.object_counts[Message] == [1, 1]
    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=TIMEOUT)


@pytest.mark.profiling
def test_profiling_instance_number():
    """Test profiling tool."""

    def output_function(report):
        """Test output function"""
        nonlocal result
        result = report

    result, types_to_track = "", [Message]
    p = Profiling(types_to_track, 1, output_function=output_function)
    p.start()
    wait_for_condition(lambda: p.is_running, timeout=TIMEOUT)

    __reference, messages = create_dummies(), create_messages()  # noqa: F841

    try:
        wait_for_condition(lambda: result, timeout=TIMEOUT)
        count_dict = extract_object_counts(result)
        assert count_dict["created"] == {"Message": MESSAGE_NUMBER}
        assert count_dict["present"] == {"Message": MESSAGE_NUMBER}
        assert count_dict["gc"]["DummyClass"] == DUMMIES_NUMBER
        # create no new, cut existing messages by half
        result, messages = "", messages[: MESSAGE_NUMBER // 2]
        wait_for_condition(lambda: result, timeout=TIMEOUT)
        count_dict = extract_object_counts(result)
        assert count_dict["created"] == {"Message": MESSAGE_NUMBER}
        assert count_dict["present"] == {"Message": MESSAGE_NUMBER // 2}
        # create a second series of messages, add to the remaining half
        result, messages = "", [messages + create_messages()]
        wait_for_condition(lambda: result, timeout=TIMEOUT)
        count_dict = extract_object_counts(result)
        assert count_dict["created"] == {"Message": 2 * MESSAGE_NUMBER}
        assert count_dict["present"] == {"Message": 1.5 * MESSAGE_NUMBER}
    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=TIMEOUT)


@pytest.mark.profiling
def test_profiling_cross_reference():
    """Test profiling tool."""

    def output_function(report):
        """Test output function"""
        nonlocal result
        result = report

    result, types_to_track = "", [Message, MessageContainer]
    p = Profiling(types_to_track, 1, output_function=output_function)
    p.start()
    wait_for_condition(lambda: p.is_running, timeout=TIMEOUT)

    __reference = __create_two_return_one()  # noqa: F841
    expected_created = {"Message": MESSAGE_NUMBER, "MessageContainer": 2}
    expected_present = {"Message": MESSAGE_NUMBER, "MessageContainer": 1}

    try:
        wait_for_condition(lambda: result, timeout=TIMEOUT)
        count_dict = extract_object_counts(result)
        assert count_dict["created"] == expected_created
        assert count_dict["present"] == expected_present
    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=TIMEOUT)


@pytest.mark.profiling
def test_profiling_counts_not_equal():
    """Test profiling tool."""

    def output_function(report):
        """Test output function"""
        nonlocal result
        result = report

    result, types_to_track = "", [Message, MessageContainer, DummyClass]
    p = Profiling(types_to_track, 1, output_function=output_function)
    p.start()
    wait_for_condition(lambda: p.is_running, timeout=TIMEOUT)

    __reference = create_dummies(), __create_two_return_one()  # noqa: F841
    expected_shared = {"Message": MESSAGE_NUMBER, "DummyClass": DUMMIES_NUMBER}
    expected_created = {**expected_shared, "MessageContainer": 2}
    expected_present = {**expected_shared, "MessageContainer": 1}

    try:
        wait_for_condition(lambda: result, timeout=TIMEOUT)
        count_dict = extract_object_counts(result)
        assert count_dict["created"] == expected_created
        assert count_dict["present"] == expected_present
        assert count_dict["gc"].get("DummyClass", 0) == DUMMIES_NUMBER
        assert "Message" not in count_dict["gc"]
        assert "MessageContainer" not in count_dict["gc"]
    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=TIMEOUT)
