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
from typing import List, Optional

from aea.helpers.profiling import Profiling
from aea.protocols.base import Message

from tests.common.utils import wait_for_condition


def test_basic_profiling():
    """Test profiling tool."""
    result = ""

    def output_function(report):
        nonlocal result
        result = report

    p = Profiling(1, [Message], [Message], output_function=output_function)
    p.start()

    wait_for_condition(lambda: p.is_running, timeout=20)
    m = Message()
    try:
        wait_for_condition(lambda: result, timeout=20)

        assert "Profiling details" in result
        assert "incomplete_to_complete_dialogue_labels" in result
    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=20)
    del m


def test_profiling_instance_number():
    """Test profiling tool."""
    result = ""

    def output_function(report):
        nonlocal result
        result = report

    p = Profiling(1, [Message], [Message], output_function=output_function)
    p.start()

    wait_for_condition(lambda: p.is_running, timeout=20)

    # Create some messages
    MESSAGE_NUMBER = 10
    messages = [Message() for _ in range(MESSAGE_NUMBER)]

    try:
        # Check the number of created and present messages
        wait_for_condition(lambda: result, timeout=20)

        assert "Profiling details" in result
        assert "incomplete_to_complete_dialogue_labels" in result
        assert f"Message (present):  {MESSAGE_NUMBER}" in result
        assert f"Message (created):  {MESSAGE_NUMBER}" in result

        # Modify the number of messages
        messages = messages[: int(MESSAGE_NUMBER / 2)]
        result = ""

        # Check the number of created and present messages
        wait_for_condition(lambda: result, timeout=20)

        assert "Profiling details" in result
        assert "incomplete_to_complete_dialogue_labels" in result
        assert f"Message (present):  {int(MESSAGE_NUMBER / 2)}" in result
        assert f"Message (created):  {MESSAGE_NUMBER}" in result

        # Modify the number of messages
        messages += [Message() for _ in range(len(messages))]
        result = ""

        # Check the number of created and present messages
        wait_for_condition(lambda: result, timeout=20)

        assert "Profiling details" in result
        assert "incomplete_to_complete_dialogue_labels" in result
        assert f"Message (present):  {MESSAGE_NUMBER}" in result
        assert (
            f"Message (created):  {MESSAGE_NUMBER + int(MESSAGE_NUMBER / 2)}" in result
        )

    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=20)
    del messages


def test_profiling_cross_reference():
    """Test profiling tool."""
    result = ""
    MESSAGE_NUMBER = 10

    def output_function(report):
        nonlocal result
        result = report

    class MessageContainer:
        def __init__(self, other: Optional["MessageContainer"] = None) -> None:
            self.messages: List[Message] = (
                other.messages if other else [Message() for _ in range(MESSAGE_NUMBER)]
            )

    p = Profiling(
        1,
        [Message, MessageContainer],
        [Message, MessageContainer],
        output_function=output_function,
    )
    p.start()

    wait_for_condition(lambda: p.is_running, timeout=20)

    container_a = MessageContainer()  # contains new messages
    MessageContainer(container_a)  # shares the same messages with a

    try:
        # Check the number of created and present messages
        wait_for_condition(lambda: result, timeout=20)

        assert "Profiling details" in result
        assert "incomplete_to_complete_dialogue_labels" in result
        assert f"Message (present):  {MESSAGE_NUMBER}" in result
        assert f"Message (created):  {MESSAGE_NUMBER}" in result
        assert f"MessageContainer (present):  1" in result
        assert f"MessageContainer (created):  2" in result

    finally:
        p.stop()
        p.wait_completed(sync=True, timeout=20)
