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

"""This module contains tests for decision_maker."""

from aea.decision_maker.messages.base import InternalMessage


def test_internal_message_base():
    """Test the internal message base."""
    msg = InternalMessage()
    msg.body = {"test_key": "test_value"}

    other_msg = InternalMessage(body={"test_key": "test_value"})
    assert msg == other_msg, "Messages should be equal."
    assert str(msg) == "InternalMessage(test_key=test_value)"
    assert msg._body is not None
    msg.body = {"Test": "My_test"}
    assert msg._body == {
        "Test": "My_test"
    }, "Message body must be equal with the above dictionary."
    msg.set("Test", 2)
    assert msg._body["Test"] == 2, "body['Test'] should be equal to 2."
    msg.unset("Test")
    assert "Test" not in msg._body.keys(), "Test should not exist."

    def is_consistent_mock():
        raise Exception()

    InternalMessage._is_consistent = is_consistent_mock
    msg = InternalMessage()
