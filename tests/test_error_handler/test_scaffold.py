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

import pytest

from aea.error_handler.scaffold import ErrorHandler


def test_scaffold_send_unsupported_protocol_raises_not_implemented_error():
    """Test 'send_unsupported_protocol' raises not implemented error."""
    with pytest.raises(NotImplementedError):
        ErrorHandler().send_unsupported_protocol(None, None)


def test_scaffold_send_decoding_error_raises_not_implemented_error():
    """Test 'send_decoding_error' raises not implemented error."""
    with pytest.raises(NotImplementedError):
        ErrorHandler().send_decoding_error(None, None, None)


def test_scaffold_send_no_active_handler_raises_not_implemented_error():
    """Test 'send_no_active_handler' raises not implemented error."""
    with pytest.raises(NotImplementedError):
        ErrorHandler().send_no_active_handler(None, None, None)
