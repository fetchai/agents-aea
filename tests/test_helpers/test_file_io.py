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
"""This module contains the tests for the 'helpers/file_io' module."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import aea
from aea.configurations.base import PublicId
from aea.helpers.file_io import _decode, envelope_from_bytes, lock_file, write_envelope
from aea.mail.base import Envelope


class TestFileLock:
    """Test for filelocks."""

    def test_lock_file_ok(self):
        """Work ok ok for random file."""
        with tempfile.TemporaryFile() as fp:
            with lock_file(fp):
                pass

    def test_lock_file_error(self):
        """Fail on closed file."""
        with tempfile.TemporaryFile() as fp:
            fp.close()
            with pytest.raises(ValueError):
                with lock_file(fp):
                    pass


def test_envelope_serialization():
    """Test envelope serialization/deserialization with files."""
    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_specification_id=PublicId("author", "name", "0.1.0"),
        message=b"",
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = Path(os.path.join(temp_dir, "output_file"))
        with output_file.open(mode="wb") as fout:
            write_envelope(envelope, fout)

        actual_envelope = envelope_from_bytes(output_file.read_bytes())

    assert envelope == actual_envelope


def test_decode_fails():
    """Test decode fails."""
    with pytest.raises(
        ValueError,
        match="Expected at least 5 values separated by commas and last value being empty or new line, got 1",
    ):
        _decode(b"")


def test_envelope_from_bytes_bad_format():
    """Test envelope_from_bytes, when the input has a bad format we raise ValueError."""
    test_error_message = "Something bad happened."
    _bytes = b""
    with patch(
        "aea.helpers.file_io._decode", side_effect=ValueError(test_error_message)
    ):
        with patch.object(aea.helpers.file_io._default_logger, "error") as mock_error:
            envelope_from_bytes(_bytes)
            mock_error.assert_called_with(
                f"Bad formatted input: {_bytes}. {test_error_message}"
            )
