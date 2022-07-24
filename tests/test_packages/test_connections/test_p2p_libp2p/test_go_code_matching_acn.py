# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This test module compares P2PLibp2p go code in open-aea and open-acn"""

import difflib
import filecmp
import logging
import os
import tempfile
from collections import Counter, namedtuple
from typing import Iterable, List

import git
import pytest

from tests.conftest import remove_test_directory
from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    libp2p_log_on_failure_all,
)


PACKAGE = "packages.valory.connections.p2p_libp2p.libp2p_node"
AEA_ROOT_DIR = os.path.join(*PACKAGE.split("."))
# if testing locally: tmp_dir = "../open-acn/"  # WARNING: will be `/` prefix missing still
ACN_GITHUB_URL = "https://github.com/valory-xyz/open-acn/"

FilePaths = namedtuple("FilePaths", "abs_aea abs_acn rel_aea rel_acn")


def get_all_file_paths(directory: str, extension: str = "") -> List[str]:
    """
    Get all nested files from a directory with a specific extension.

    usage: get_all_file_paths("packages/valory/skills")
    """

    return [
        os.path.join(root, file)
        for root, _, files in os.walk(directory)
        for file in files
        if file.endswith(extension)
    ]


def get_relative_file_paths(root: str, *abs_paths) -> List[str]:
    """Remove the root directory from the absolute paths"""

    return [abs_path.split(root).pop() for abs_path in abs_paths]


@pytest.fixture(scope="class")
def acn_repo_dir():
    """We keep the ACN repo around for all tests."""

    tmp_dir = tempfile.mkdtemp()
    acn_repo = git.Repo.clone_from(ACN_GITHUB_URL, tmp_dir)
    yield tmp_dir, acn_repo
    remove_test_directory(tmp_dir)


@pytest.fixture(scope="class")
def go_file_paths(acn_repo_dir) -> FilePaths:
    """Get go file paths"""

    tmp_dir, acn_repo = acn_repo_dir
    abs_aea = get_all_file_paths(AEA_ROOT_DIR, ".go")
    abs_acn = get_all_file_paths(tmp_dir, ".go")
    rel_aea = get_relative_file_paths(AEA_ROOT_DIR, *abs_aea)
    rel_acn = get_relative_file_paths(tmp_dir, *abs_acn)
    return FilePaths(abs_aea, abs_acn, rel_aea, rel_acn)


@libp2p_log_on_failure_all
class TestP2PLibp2pGoCodeMatchingOpenACN:
    """
    Test that the open-aea p2p_libp2p go code matches that in open-acn.

    Steps:
    1. download the open-acn repo
    2. ensure all required files are present
    3. use filecmp and difflib to check for differences
    """

    @classmethod
    def setup(cls):  # I don't take extra args :)
        """Set the test up"""

    def test_repo_not_bare(self, acn_repo_dir):
        """Check that the repo isn't bare"""

        _, acn_repo = acn_repo_dir
        assert not acn_repo.bare

    def test_unique_relative_path_assumption(self, go_file_paths: FilePaths):
        """Check assumption of unique relative paths."""

        def has_duplicates(items: Iterable) -> bool:
            return any(k for k, v in Counter(items).items() if v > 1)

        relative_paths = (go_file_paths.rel_aea, go_file_paths.rel_acn)
        assert not any(map(has_duplicates, relative_paths))

    def test_file_presence(self, go_file_paths: FilePaths):
        """Compare both ways to detect missing files."""

        relative_paths = (go_file_paths.rel_aea, go_file_paths.rel_acn)
        aea_filepaths, acn_filepaths = map(set, relative_paths)
        missing_in_acn = aea_filepaths - acn_filepaths
        missing_in_aea = acn_filepaths - aea_filepaths
        assert not missing_in_acn and not missing_in_aea

    def test_content_equal(self, go_file_paths: FilePaths) -> None:
        """Compare file content, report differences."""

        differences = {}
        zipper = zip(sorted(go_file_paths.abs_aea), sorted(go_file_paths.abs_acn))
        for aea_file, acn_file in zipper:
            # this check is fast, but provides no insight when false
            if filecmp.cmp(aea_file, acn_file):
                continue

            # to facilitate debugging sessions
            aea_content = open(aea_file).readlines()
            acn_content = open(acn_file).readlines()
            detected = difflib.unified_diff(aea_content, acn_content)
            file_name = aea_file.split(AEA_ROOT_DIR).pop()
            differences[file_name] = "".join(detected)

        if differences:
            report: str = "\n".join(f">> {k}:{v}" for k, v in differences.items())
            logging.error(f"Non-matching code:\n{report}")
        assert not bool(differences)
