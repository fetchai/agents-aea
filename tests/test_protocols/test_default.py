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

"""This module contains the tests of the messages module."""

# import base64
# import json
from unittest import mock

import pytest

from aea.protocols.default.message import DefaultMessage


def test_default_bytes_serialization():
    """Test that the serialization for the 'simple' protocol works for the BYTES message."""
    expected_msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    msg_bytes = DefaultMessage.serializer.encode(expected_msg)
    actual_msg = DefaultMessage.serializer.decode(msg_bytes)
    assert expected_msg == actual_msg

    with pytest.raises(ValueError):
        with mock.patch(
            "aea.protocols.default.message.DefaultMessage.Performative"
        ) as mock_type_enum:
            mock_type_enum.BYTES.value = "unknown"
            assert DefaultMessage.serializer.encode(expected_msg), ""


def test_default_error_serialization():
    """Test that the serialization for the 'simple' protocol works for the ERROR message."""
    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.ERROR,
        error_code=DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL,
        error_msg="An error",
        error_data={"error": b"Some error data"},
    )
    msg_bytes = DefaultMessage.serializer.encode(msg)
    actual_msg = DefaultMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    # msg = DefaultMessage(
    #     performative=DefaultMessage.Performative.BYTES, content=b"hello", dialogue_reference=("", ""), message_id=1, target=0,
    # )
    # with pytest.raises(ValueError):
    #     with mock.patch(
    #         "aea.protocols.default.message.DefaultMessage.Performative"
    #     ) as mock_type_enum:
    #         mock_type_enum.BYTES.value = "unknown"
    #         body = {}  # Dict[str, Any]
    #         body["performative"] = str(msg.performative.value)
    #         content = msg.content
    #         body["content"] = base64.b64encode(content).decode("utf-8")
    #         bytes_msg = json.dumps(body).encode("utf-8")
    #         returned_msg = DefaultMessage.serializer.decode(bytes_msg)
    #         assert msg != returned_msg, "Messages must be different"


def test_default_message_str_values():
    """Tests the returned string values of default Message."""
    assert (
        str(DefaultMessage.Performative.BYTES) == "bytes"
    ), "DefaultMessage.Performative.BYTES must be bytes"
    assert (
        str(DefaultMessage.Performative.ERROR) == "error"
    ), "DefaultMessage.Performative.ERROR must be error"


def test_check_consistency_raises_exception_when_type_not_recognized():
    """Test that we raise exception when the type of the message is not recognized."""
    message = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    # mock the __eq__ method such that any kind of matching is going to fail.
    with mock.patch.object(DefaultMessage.Performative, "__eq__", return_value=False):
        assert not message._is_consistent()
