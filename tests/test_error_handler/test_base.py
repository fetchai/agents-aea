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
"""This module contains the tests for the sym link module."""

import logging
from unittest.mock import Mock, patch

from aea.error_handler.default import ErrorHandler


_default_logger = logging.getLogger(__name__)


def test_send_unsupported_protocol():
    """Test the send_unsupported_protocol method."""
    handler = ErrorHandler
    envelope_mock = Mock()
    envelope_mock.protocol_id = "1"
    envelope_mock.sender = "2"
    envelope_mock.to = "3"
    count = handler.unsupported_protocol_count
    with patch.object(_default_logger, "warning") as mock_logger:
        handler.send_unsupported_protocol(envelope_mock, _default_logger)
        mock_logger.assert_any_call(
            f"Unsupported protocol: {envelope_mock.protocol_id}. You might want to add a handler for this protocol. Sender={envelope_mock.sender}, to={envelope_mock.sender}."
        )
    assert count + 1 == handler.unsupported_protocol_count


def test_send_decoding_error():
    """Test the send_decoding_error method."""
    handler = ErrorHandler
    envelope_mock = Mock()
    envelope_mock.protocol_id = "1"
    envelope_mock.sender = "2"
    envelope_mock.to = "3"
    count = handler.decoding_error_count
    with patch.object(_default_logger, "warning") as mock_logger:
        handler.send_decoding_error(envelope_mock, _default_logger)
        mock_logger.assert_any_call(
            f"Decoding error for envelope: {envelope_mock}. Protocol_id='{envelope_mock.protocol_id}' and message are inconsistent. Sender={envelope_mock.sender}, to={envelope_mock.sender}."
        )
    assert count + 1 == handler.decoding_error_count


def test_send_unsupported_skill_1():
    """Test the send_unsupported_protocol method."""
    handler = ErrorHandler
    envelope_mock = Mock()
    envelope_mock.protocol_id = "1"
    envelope_mock.sender = "2"
    envelope_mock.to = "3"
    envelope_mock.skill_id = None
    count = handler.unsupported_skill_count
    with patch.object(_default_logger, "warning") as mock_logger:
        handler.send_unsupported_skill(envelope_mock, _default_logger)
        mock_logger.assert_any_call(
            f"Cannot handle envelope: no active handler registered for the protocol_id='{envelope_mock.protocol_id}'. Sender={envelope_mock.sender}, to={envelope_mock.sender}."
        )
    assert count + 1 == handler.unsupported_skill_count


def test_send_unsupported_skill_2():
    """Test the send_unsupported_protocol method."""
    handler = ErrorHandler
    envelope_mock = Mock()
    envelope_mock.protocol_id = "1"
    envelope_mock.sender = "2"
    envelope_mock.to = "3"
    envelope_mock.skill_id = "4"
    count = handler.unsupported_skill_count
    with patch.object(_default_logger, "warning") as mock_logger:
        handler.send_unsupported_skill(envelope_mock, _default_logger)
        mock_logger.assert_any_call(
            f"Cannot handle envelope: no active handler registered for the protocol_id='{envelope_mock.protocol_id}' and skill_id='{envelope_mock.skill_id}'. Sender={envelope_mock.sender}, to={envelope_mock.sender}."
        )
    assert count + 1 == handler.unsupported_skill_count
