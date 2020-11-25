#!/usr/bin/env python3
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

"""Bump the AEA version throughout the code base."""

import argparse
import re
import sys
from pathlib import Path

from packaging.version import Version

from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)
from scripts.generate_ipfs_hashes import update_hashes


VERSION_NUMBER_PART_REGEX = r"(0|[1-9]\d*)"
VERSION_REGEX = fr"(any|latest|({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})\.({VERSION_NUMBER_PART_REGEX})(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"

PACKAGES_DIR = Path("packages")
TESTS_DIR = Path("tests")
AEA_DIR = Path("aea")
CONFIGURATION_FILENAME_REGEX = re.compile(
    "|".join(
        [
            DEFAULT_AEA_CONFIG_FILE,
            DEFAULT_SKILL_CONFIG_FILE,
            DEFAULT_CONNECTION_CONFIG_FILE,
            DEFAULT_CONTRACT_CONFIG_FILE,
            DEFAULT_PROTOCOL_CONFIG_FILE,
        ]
    )
)

IGNORE_DIRS = [Path(".git")]


def update_version_for_files(current_version: str, new_version: str) -> None:
    """
    Update the version.

    :param current_version: the current version
    :param new_version: the new version
    """
    files = [
        Path("benchmark", "run_from_branch.sh"),
        Path("deploy-image", "docker-env.sh"),
        Path("deploy-image", "Dockerfile"),
        Path("develop-image", "docker-env.sh"),
        Path("docs", "quickstart.md"),
        Path("scripts", "install.ps1"),
        Path("scripts", "install.sh"),
        Path("tests", "test_docs", "test_bash_yaml", "md_files", "bash-quickstart.md"),
        Path("user-image", "docker-env.sh"),
    ]
    for filepath in files:
        update_version_for_file(filepath, current_version, new_version)


def update_version_for_aea(new_version: str) -> str:
    """
    Update version for file.

    :param new_version: the new version
    :return: the current version
    """
    current_version = ""
    path = Path("aea", "__version__.py")
    with open(path, "rt") as fin:
        for line in fin:
            if "__version__" not in line:
                continue
            match = re.search(VERSION_REGEX, line)
            if match is None:
                raise ValueError("Current version is not well formatted.")
            current_version = match.group(1)
    if current_version == "":
        raise ValueError("No version found!")
    update_version_for_file(path, current_version, new_version)
    return current_version


def compute_specifier_from_version(version: Version) -> str:
    """
    Compute the specifier set from a version, by varying only on the patch number.

    I.e. from "{major}.{minor}.{patch}", return

    ">={major}.{minor}.0, <{major}.{minor + 1}.0"

    :param version: the version
    :return: the specifier set
    """
    new_major = version.major
    new_minor_low = version.minor
    new_minor_high = new_minor_low + 1
    lower_bound = Version(f"{new_major}.{new_minor_low}.0")
    upper_bound = Version(f"{new_major}.{new_minor_high}.0")
    specifier_set = f">={lower_bound}, <{upper_bound}"
    return specifier_set


def update_version_for_file(path: Path, current_version: str, new_version: str) -> None:
    """
    Update version for file.

    :param path: the file path
    :param current_version: the current version
    :param new_version: the new version
    """
    content = path.read_text()
    content = content.replace(current_version, new_version)
    path.write_text(content)


def update_aea_version_specifiers(old_version: Version, new_version: Version) -> bool:
    """
    Update aea_version specifier set in docs.

    :param old_version: the old version.
    :param new_version: the new version.
    :return: True if the update has been done, False otherwise.
    """
    old_specifier_set = compute_specifier_from_version(old_version)
    new_specifier_set = compute_specifier_from_version(new_version)
    print(f"Old version specifier: {old_specifier_set}")
    print(f"New version specifier: {new_specifier_set}")
    old_specifier_set_regex = re.compile(str(old_specifier_set).replace(" ", " *"))
    if old_specifier_set == new_specifier_set:
        print("Not updating version specifier - they haven't changed.")
        return False
    for file in filter(lambda p: not p.is_dir(), Path(".").rglob("*")):
        dir_root = Path(file.parts[0])
        if dir_root in IGNORE_DIRS:
            print(f"Skipping '{file}'...")
            continue
        print(
            f"Replacing '{old_specifier_set}' with '{new_specifier_set}' in '{file}'... ",
            end="",
        )
        try:
            content = file.read_text()
        except UnicodeDecodeError as e:
            print(f"Cannot read {file}: {str(e)}. Continue...")
        else:
            if old_specifier_set_regex.search(content) is not None:
                content = old_specifier_set_regex.sub(new_specifier_set, content)
                file.write_text(content)
    return True


def parse_args() -> argparse.Namespace:
    """Parse arguments."""

    parser = argparse.ArgumentParser("bump_aea_version")
    parser.add_argument(
        "--new-version", type=str, required=True, help="The new version."
    )
    parser.add_argument("--no-fingerprint", action="store_true")
    arguments_ = parser.parse_args()
    return arguments_


if __name__ == "__main__":
    arguments = parse_args()
    _new_version_str = arguments.new_version

    _current_version_str = update_version_for_aea(_new_version_str)
    update_version_for_files(_current_version_str, _new_version_str)

    _new_version: Version = Version(_new_version_str)
    _current_version: Version = Version(_current_version_str)
    have_updated_specifier_set = update_aea_version_specifiers(
        _current_version, _new_version
    )

    print("OK")
    return_code = 0
    if arguments.no_fingerprint:
        print("Not updating fingerprints, since --no-fingerprint was specified.")
    elif not have_updated_specifier_set:
        print("Not updating fingerprints, since no specifier set has been updated.")
    else:
        print("Updating hashes and fingerprints.")
        return_code = update_hashes()
    sys.exit(return_code)
