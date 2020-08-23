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

from unittest import mock
from unittest.mock import patch

import pytest

import aea
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


def test_default_valid_performatives():
    """Test 'valid_performatives' getter."""
    msg = DefaultMessage(DefaultMessage.Performative.BYTES, content=b"")
    assert msg.valid_performatives == set(
        map(lambda x: x.value, iter(DefaultMessage.Performative))
    )


def test_light_protocol_rule_3_target_0():
    """Test that if message_id is not 1, target must be > 0"""
    with patch.object(aea.protocols.default.message.logger, "error") as mock_logger:
        message_id = 2
        target = 0
        DefaultMessage(
            message_id=message_id,
            target=target,
            performative=DefaultMessage.Performative.BYTES,
            content=b"",
        )
        mock_logger.assert_any_call(
            f"Invalid 'target'. Expected an integer between 1 and {message_id - 1} inclusive. Found {target}."
        )


def test_light_protocol_rule_3_target_less_than_message_id():
    """Test that if message_id is not 1, target must be > message_id"""
    with patch.object(aea.protocols.default.message.logger, "error") as mock_logger:
        message_id = 2
        target = 2
        DefaultMessage(
            message_id=message_id,
            target=target,
            performative=DefaultMessage.Performative.BYTES,
            content=b"",
        )
        mock_logger.assert_any_call(
            f"Invalid 'target'. Expected an integer between 1 and {message_id - 1} inclusive. Found {target}."
        )


def test_serializer_performative_not_found():
    """Test the serializer when the performative is not found."""
    message = DefaultMessage(
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"",
    )
    message_bytes = message.serializer.encode(message)
    with patch.object(DefaultMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(ValueError, match="Performative not valid: .*"):
            message.serializer.decode(message_bytes)
