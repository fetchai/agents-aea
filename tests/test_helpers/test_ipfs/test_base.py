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

"""This module contains the tests for the ipfs helper module."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from aea_cli_ipfs.ipfs_utils import IPFSTool  # type: ignore

from aea.helpers.cid import to_v1
from aea.helpers.ipfs.base import IPFSHashOnly, _is_text


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


@pytest.mark.usefixtures("use_ipfs_daemon")
class TestDirectoryHashing:
    """Test recursive directory hashing."""

    def setup(
        self,
    ) -> None:
        """Setup test."""

        self.hash_tool = IPFSHashOnly()
        self.ipfs_tool = IPFSTool(addr="/ip4/127.0.0.1/tcp/5001")

    def test_depth_0(
        self,
    ) -> None:
        """Test directory with only one file and no child directories."""

        with TemporaryDirectory() as temp_dir:
            Path(temp_dir, "dummy_file.txt").write_text("Hello, World!")

            hash_local = self.hash_tool.get(temp_dir)
            d, hash_daemon, _ = self.ipfs_tool.add(temp_dir)
            hash_daemon = to_v1(hash_daemon)

            assert (
                hash_daemon == hash_local
            ), f"Hash from daemon {hash_daemon} does not match calculated hash {hash_local}\n{d}"

    def test_depth_1(
        self,
    ) -> None:
        """Test directory with only one file and a child directory."""

        with TemporaryDirectory() as temp_dir:
            Path(temp_dir, "dummy_file.txt").write_text("Hello, World!")
            Path(temp_dir, "inner_0").mkdir()
            Path(temp_dir, "inner_0", "dummy_file_inner.txt").write_text("Foo, Bar!")

            hash_local = self.hash_tool.get(temp_dir)
            d, hash_daemon, _ = self.ipfs_tool.add(temp_dir)
            hash_daemon = to_v1(hash_daemon)

            assert (
                hash_daemon == hash_local
            ), f"Hash from daemon {hash_daemon} does not match calculated hash {hash_local}\n{d}"

    def test_depth_multi(
        self,
    ) -> None:
        """Test directory with only one file and a child directory."""

        with TemporaryDirectory() as temp_dir:
            Path(temp_dir, "dummy_file.txt").write_text("Hello, World!")
            for i in range(3, 7):
                if i % 2:
                    Path(temp_dir, f"inner_{i}").mkdir()
                    Path(
                        temp_dir, f"inner_{i}", f"dummy_file_inner_{i}.txt"
                    ).write_text(f"Foo, Bar! {i}")
                else:
                    Path(temp_dir, f"inner_{i}").mkdir()
                    for j in range(i):
                        Path(
                            temp_dir, f"inner_{i}", f"dummy_file_inner_{i}_{j}.txt"
                        ).write_text(f"Foo, Bar! {i}_{j}")
                        Path(temp_dir, f"inner_{i}", f"inner_{i}_{j}").mkdir()
                        for k in range(i):
                            Path(
                                temp_dir,
                                f"inner_{i}",
                                f"inner_{i}_{j}",
                                f"dummy_file_inner_{i}_{j}_{k}.txt",
                            ).write_text(f"Foo, Bar! {i}_{j}_{k}")

            # file larger then default chunk size
            Path(temp_dir, "dummy_file_large.txt").write_text(
                "1" * int(IPFSHashOnly.DEFAULT_CHUNK_SIZE * 1.5)
            )

            hash_local = self.hash_tool.get(temp_dir)
            _, hash_daemon, _ = self.ipfs_tool.add(temp_dir)
            hash_daemon = to_v1(hash_daemon)

            assert (
                hash_daemon == hash_local
            ), f"Hash from daemon {hash_daemon} does not match calculated hash {hash_local}"
