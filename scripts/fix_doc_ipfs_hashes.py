#!/usr/bin/env python3
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

"""This module contains the tools for autoupdating ipfs hashes in the documentation."""

import re
from pathlib import Path
from typing import Dict, Tuple


FETCH_COMMAND_REGEX = (
    r"aea fetch (?P<vendor>.*)\/(?P<package>.*):(?P<hash>Q.*) \-\-remote"
)


def read_file(filepath: str) -> str:
    """Loads a file into a string"""
    with open(filepath, "r", encoding="utf-8") as file_:
        file_str = file_.read()
    return file_str


def get_hashes() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Get a dictionary with all packages and their hashes"""
    CSV_HASH_REGEX = r"(?P<vendor>.*)\/(?P<type>.*)\/(?P<name>.*),(?P<hash>.*)\n"
    hashes_file = Path("packages", "hashes.csv").relative_to(".")
    hashes_content = read_file(str(hashes_file))
    package_to_hashes = {}
    hashes_to_package = {}
    for match in re.findall(CSV_HASH_REGEX, hashes_content):
        package_to_hashes[f"{match[0]}/{match[1]}/{match[2]}"] = match[3]
        hashes_to_package[match[3]] = f"{match[0]}/{match[1]}/{match[2]}"
    return package_to_hashes, hashes_to_package


def fix_ipfs_hashes() -> None:
    """Fix ipfs hashes in the docs"""
    _, hashes_to_package = get_hashes()

    all_md_files = Path("docs").rglob("*.md")
    errors = False

    for md_file in all_md_files:
        print(f"Checking {md_file}")
        content = read_file(str(md_file))
        for match in re.findall(FETCH_COMMAND_REGEX, content):
            doc_vendor, doc_package, doc_hash = match

            # Look for potential matching packages
            potential_packages = {
                p: h
                for h, p in hashes_to_package.items()
                if p.startswith(doc_vendor) and p.endswith(doc_package)
            }

            if not potential_packages:
                print(
                    f"Could not check an IPFS hash on doc file {md_file} because it references an unknown package: '{doc_vendor}/{doc_package}:{doc_hash}'"
                )
                errors = True
                continue

            if (
                len(potential_packages) != 1
                and doc_hash not in potential_packages.values()
            ):
                print(
                    f"\nCould not check an IPFS hash on doc file {md_file} because there are multiple matching packages in hashes.csv. Fix it manually:\n"
                    f"Referenced package in docs {doc_vendor}/{doc_package}:{doc_hash}\nPotential packages: {potential_packages}.\n"
                )
                errors = True
                continue

            # Overwrite with new hash
            expected_hash = list(potential_packages.values())[0]

            if doc_hash == expected_hash:
                continue

            new_command = (
                f"aea fetch {doc_vendor}/{doc_package}:{expected_hash} --remote"
            )

            new_content = re.sub(
                FETCH_COMMAND_REGEX, new_command, content, count=0, flags=0
            )

            with open(str(md_file), "w", encoding="utf-8") as qs_file:
                qs_file.write(new_content)
            print(f"Fixed an IPFS hash on doc file {md_file}")

    if errors:
        raise ValueError(
            "There were some errors while processing the docs. Check the logs."
        )
    print("OK")


if __name__ == "__main__":
    fix_ipfs_hashes()
