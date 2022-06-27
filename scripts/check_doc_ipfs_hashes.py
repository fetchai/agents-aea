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

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml


AEA_COMMAND_REGEX = r"(?P<full_cmd>(?P<cli>aea|autonomy) (?P<cmd>fetch|add .*) (?:(?P<vendor>.*)\/(?P<package>.[^:]*):(?P<version>\d+\.\d+\.\d+)?:?)?(?P<hash>Q[A-Za-z0-9]+))"

ROOT_DIR = Path(__file__).parent.parent


def read_file(filepath: str) -> str:
    """Loads a file into a string"""
    with open(filepath, "r", encoding="utf-8") as file_:
        file_str = file_.read()
    return file_str


class Package:  # pylint: disable=too-few-public-methods
    """Class that represents a package in hashes.csv"""

    CSV_HASH_REGEX = r"(?P<vendor>.*)\/(?P<type>.*)\/(?P<name>.*),(?P<hash>.*)(?:\n|$)"

    def __init__(self, package_line: str) -> None:
        """Constructor"""
        m = re.match(self.CSV_HASH_REGEX, package_line)
        if not m:
            raise ValueError(
                f"PackageHashManager: the line {package_line} does not match the package format"
            )
        self.vendor = m.groupdict()["vendor"]
        self.type = m.groupdict()["type"]
        self.name = m.groupdict()["name"]
        self.hash = m.groupdict()["hash"]

        if self.name == "scaffold":
            return

        if self.type not in (
            "connections",
            "agents",
            "protocols",
            "services",
            "skills",
            "contracts",
        ):
            raise ValueError(
                f"Package: unknown package type in hashes.csv: {self.type}"
            )
        self.type = self.type[:-1]  # remove last s

        self.last_version = None
        yaml_file_path = Path(
            ROOT_DIR,
            "packages",
            self.vendor,
            self.type + "s",
            self.name,
            f"{'aea-config' if self.type == 'agent' else self.type}.yaml",
        )
        with open(yaml_file_path, "r", encoding="utf-8") as file:
            content = yaml.load_all(file, Loader=yaml.FullLoader)
            for resource in content:
                if "version" in resource:
                    self.last_version = resource["version"]
                    break

    def get_command(self) -> str:
        """Get the add command"""
        if self.type == "agent":
            return (
                f"aea fetch {self.vendor}/{self.name}:{self.last_version}:{self.hash}"
            )
        return f"aea add {self.type} {self.vendor}/{self.name}:{self.last_version}:{self.hash}"


class PackageHashManager:
    """Class that represents the packages in hashes.csv"""

    def __init__(self) -> None:
        """Constructor"""
        hashes_file = Path("packages", "hashes.csv").relative_to(".")
        with open(hashes_file, "r", encoding="utf-8") as file_:
            self.packages = [Package(line) for line in file_.readlines()]
            self.packages = [p for p in self.packages if p.name != "scaffold"]

        self.package_tree: Dict = {}
        for p in self.packages:
            self.package_tree.setdefault(p.vendor, {})
            self.package_tree[p.vendor].setdefault(p.type, {})
            self.package_tree[p.vendor][p.type].setdefault(p.name, p)

    def get_package_by_hash(self, package_hash: str) -> Optional[Package]:
        """Get a package given its hash"""
        packages = list(filter(lambda p: p.hash == package_hash, self.packages))
        if not packages:
            return None
        if len(packages) > 1:
            raise ValueError(
                f"PackageHashManager: hash search for {package_hash} returned more than 1 result in hashes.csv"
            )
        return packages[0]

    def get_hash_by_package_line(
        self, package_line: str, md_file: str
    ) -> Optional[str]:
        """Get a hash given its package line"""

        try:
            m = re.match(AEA_COMMAND_REGEX, package_line)

            # No match
            if not m:
                print(
                    f"Docs [{md_file}]: line '{package_line}' does not match an aea command format"
                )
                return None
            d = m.groupdict()

            # Underspecified commands that only use the hash
            if not d["vendor"] and not d["package"]:
                package = self.get_package_by_hash(d["hash"])

                # This hash exists in hashes.csv
                if package:
                    return package.hash

                # This hash does not exist in hashes.csv
                print(
                    f"Docs [{md_file}]: unknown IPFS hash in line '{package_line}'. Can't fix because this command just uses the hash"
                )
                return None

            # Complete command, succesfully retrieved
            package_type = "agent" if d["cmd"] == "fetch" else d["cmd"].split(" ")[-1]
            return self.package_tree[d["vendor"]][package_type][d["package"]].hash

        # Otherwise log the error
        except KeyError:
            print(
                f"Docs [{md_file}]: could not find the corresponding hash for line '{package_line}'"
            )
            return None


def update_test_files(old_to_new_hashes: Dict[str, str]) -> None:
    """Update IPFS hashes in test md files"""
    all_test_files = Path("tests", "test_docs", "test_bash_yaml", "md_files").rglob(
        "*.md"
    )
    for md_file in all_test_files:
        content = read_file(str(md_file))
        for old_hash, new_hash in old_to_new_hashes.items():
            content = content.replace(old_hash, new_hash)
        with open(str(md_file), "w", encoding="utf-8") as qs_file:
            qs_file.write(content)


def check_ipfs_hashes(fix: bool = False) -> None:  # pylint: disable=too-many-locals
    """Fix ipfs hashes in the docs"""

    all_md_files = Path("docs").rglob("*.md")
    errors = False
    hash_mismatches = False
    old_to_new_hashes = {}
    package_manager = PackageHashManager()

    for md_file in all_md_files:
        content = read_file(str(md_file))
        for match in re.findall(AEA_COMMAND_REGEX, content):
            doc_full_cmd = match[0]
            doc_hash = match[-1]
            expected_hash = package_manager.get_hash_by_package_line(
                doc_full_cmd, str(md_file)
            )
            if not expected_hash:
                errors = True
                continue
            expected_package = package_manager.get_package_by_hash(expected_hash)
            if not expected_package:
                errors = True
                continue

            new_command = expected_package.get_command()

            # Overwrite with new hash
            if doc_hash == expected_hash:
                continue

            hash_mismatches = True

            if fix:
                new_content = content.replace(doc_full_cmd, new_command)

                with open(str(md_file), "w", encoding="utf-8") as qs_file:
                    qs_file.write(new_content)
                print(f"Fixed an IPFS hash on doc file {md_file}")
                old_to_new_hashes[doc_hash] = expected_hash
            else:
                print(
                    f"IPFS hash mismatch on doc file {md_file}. Expected {expected_hash}, got {doc_hash}:\n    {doc_full_cmd}"
                )

    if fix:
        update_test_files(old_to_new_hashes)

    if fix and errors:
        raise ValueError(
            "There were some errors while processing the docs. Check the logs."
        )

    if not fix and (hash_mismatches or errors):
        print("There are mismatching IPFS hashes in the docs.")
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()
    check_ipfs_hashes(fix=args.fix)
