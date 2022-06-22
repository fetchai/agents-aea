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


AEA_COMMAND_REGEX = r"(?P<full_cmd>(?P<cli>aea|autonomy) (?P<cmd>fetch|add .*) (?:(?P<vendor>.*)\/(?P<package>.[^:]*):(?P<version>\d+\.\d+\.\d+)?:?)?(?P<hash>Q[A-Za-z0-9]+))"


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
        content = read_file(str(md_file))
        for match in re.findall(AEA_COMMAND_REGEX, content):
            (
                doc_full_cmd,
                doc_cli,
                doc_cmd,
                doc_vendor,
                doc_package,
                doc_version,
                doc_hash,
            ) = match

            if not doc_vendor and not doc_package:
                print(
                    f"Warning: can't check a IPFS hash in {md_file} because this commands just uses the hash:\n\t{doc_full_cmd}"
                )
                continue

            # Look for potential matching packages
            potential_packages = {
                p: h
                for h, p in hashes_to_package.items()
                if p.startswith(doc_vendor) and p.endswith(doc_package)
            }

            package_type = (
                doc_cmd.replace("add", "").strip() if "add" in doc_cmd else None
            )

            if package_type:
                potential_packages = {
                    p: h for p, h in potential_packages.items() if package_type in p
                }

            if not potential_packages:
                print(
                    f"Could not check an IPFS hash on doc file {md_file} because it references an unknown package:\n'{doc_full_cmd}'"
                )
                errors = True
                continue

            if (
                len(potential_packages) != 1
                and doc_hash not in potential_packages.values()
            ):
                print(
                    f"\nCould not check an IPFS hash on doc file {md_file} because there are multiple matching packages in hashes.csv. Fix it manually:\n"
                    f"Command in docs: {doc_full_cmd}\nPotential packages: {potential_packages}.\n"
                )
                errors = True
                continue

            # Overwrite with new hash
            expected_hash = list(potential_packages.values())[0]

            if doc_hash == expected_hash:
                continue

            new_command = ""
            if doc_vendor and doc_package:
                new_command = f"{doc_cli} {doc_cmd} {doc_vendor}/{doc_package}:{doc_version + ':' if doc_version else ''}{expected_hash}"
            else:
                new_command = f"{doc_cli} {doc_cmd} {expected_hash}"

            new_content = content.replace(doc_full_cmd, new_command)

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
