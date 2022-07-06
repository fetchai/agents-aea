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
"""This module contains the tests for the 'aea.helpers.io' module."""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aea.helpers.io import from_csv, open_file, to_csv


DUMMY_CSV_DATA = {
    "key_0": "value_0",
    "key_1": "value_1",
    "key_2": "value_2",
    "key_3": "value_3",
}


@pytest.mark.parametrize(argnames="path_builder", argvalues=[os.path.join, Path])
def test_open_file(change_directory, path_builder):
    """Test 'open_file' for the built-in open."""
    expected_string = "hello\nworld"
    path = path_builder(change_directory, "temporary-file")
    with open_file(path, "w") as file_out:
        file_out.write(expected_string)

    with open_file(path, "r") as file_in:
        assert file_in.read() == expected_string

    with open(path, "rb") as bytes_in:
        assert bytes_in.read() == bytes(expected_string, encoding="utf-8")


def test_raise_if_binary_mode():
    """Raise if mode is binary mode."""
    with pytest.raises(ValueError, match="This function can only work in text mode."):
        open_file(MagicMock(), mode="rb")


def test_csv_io() -> None:
    """Test csv utils."""

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_file = Path(temp_dir, "file.csv")

        to_csv(DUMMY_CSV_DATA, csv_file)
        assert csv_file.exists()

        csv_data = from_csv(csv_file)
        assert any(
            [csv_data[key] == value for key, value in DUMMY_CSV_DATA.items()]
        ), csv_data
