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

"""This module contains the tests for checking ipfs hashes in the documentation."""

import re
from pathlib import Path

from scripts.fix_doc_ipfs_hashes import get_hashes, read_file

from tests.conftest import ROOT_DIR


AEA_COMMAND_REGEX = r"(?P<cli>aea|autonomy) (?P<cmd>fetch|add .*) (?:(?P<vendor>.*)\/(?P<package>.[^:]*):(?P<version>\d+\.\d+\.\d+)?:?)?(?P<hash>Q[A-Za-z0-9]+)"


def test_ipfs_hashes() -> None:
    """Check doc ipfs hashes"""
    # Get the hashes dicts
    _, hashes_to_package = get_hashes()

    # Get all doc files
    all_md_files = [
        p.relative_to(ROOT_DIR) for p in Path(ROOT_DIR, "docs").rglob("*.md")
    ]

    for md_file in all_md_files:
        content = read_file(str(md_file))
        for match in re.findall(AEA_COMMAND_REGEX, content):
            _, _, doc_vendor, doc_package, _, doc_hash = match

            if not doc_vendor and not doc_package:
                # Some commands only reference the has, not the vendor or the package name
                assert (
                    doc_hash in hashes_to_package.keys()
                ), f"Unknown IPFS hash referenced in {md_file}: {doc_hash}"
                continue

            # Look for potential matching packages
            potential_packages = {
                p: h
                for h, p in hashes_to_package.items()
                if p.startswith(doc_vendor) and p.endswith(doc_package)
            }

            # Check that there is at least one similar package in hashes.csv
            assert (
                potential_packages
            ), f"The doc file {md_file} contains an 'aea fetch' command with a reference to an unknown package: '{doc_vendor}/{doc_package}:{doc_hash}'"

            # Check that there is only one similar package in hashes.csv. If there is more than one, at least one of those has a matching hash.
            assert (
                len(potential_packages) == 1 or doc_hash in potential_packages.values()
            ), f"More than one package can correspond to the 'aea fecth' command in {md_file}. Candidates: {potential_packages}"

            # If there was only one match, check that the hashes match
            if len(potential_packages) == 1:
                expected_hash = list(potential_packages.values())[0]
                assert (
                    doc_hash == expected_hash
                ), f"IPFS hash not matching in {md_file}. Expected {expected_hash}, got {doc_hash}"
