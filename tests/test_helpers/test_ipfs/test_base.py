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

"""This module contains the tests for the ipfs helper module."""

import os
from unittest.mock import patch

from aea.helpers.ipfs.base import IPFSHashOnly, _is_text

from tests.conftest import CUR_PATH


FILE_PATH = "__init__.py"


def test_get_hash():
    """Test get hash IPFSHashOnly."""
    ipfs_hash = IPFSHashOnly().get(file_path=os.path.join(CUR_PATH, FILE_PATH))
    assert ipfs_hash == "QmWeMu9JFPUcYdz4rwnWiJuQ6QForNFRsjBiN5PtmkEg4A"


def test_is_text_negative():
    """Test the helper method 'is_text' negative case."""
    # https://gehrcke.de/2015/12/how-to-raise-unicodedecodeerror-in-python-3/
    with patch(
        "aea.helpers.ipfs.base.open_file",
        side_effect=UnicodeDecodeError("foo", b"bytes", 1, 2, "Fake reason"),
    ):
        assert not _is_text("path")


def test_hash_for_big_file():
    """Check hash is ok for big amount of data with chunks support."""
    VALID_HASH = "QmWt5fanMr2JbiaUAUpyLUL8FegGn95t5tHA6kgobXgWX3"  # from ipfs daemon
    data = b"1" * int(IPFSHashOnly.DEFAULT_CHUNK_SIZE * 1.5)
    my_hash = IPFSHashOnly._generate_hash(data)
    assert my_hash == VALID_HASH
