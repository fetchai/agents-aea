#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""This script checks that dependencies in tox.ini and Pipfile match."""
import configparser
import itertools
import sys
from typing import Set, Tuple

import tomli
from packaging.requirements import Requirement as BaseRequirement


TOX_INI = "tox.ini"
PIPFILE = "Pipfile"

# specified in setup.py
WHITELIST = {
    "base58",
    "tomte",
    "memory-profiler",
    "apduboy",
}


class Requirement(BaseRequirement):
    """Requirement with comparasion"""

    def __eq__(self, __value: object) -> bool:
        """Compare two objects."""
        return str(self) == str(__value)

    def __hash__(self) -> int:
        """Get hash for object."""
        return hash(self.__str__())


def load_pipfile(filename: str = PIPFILE) -> Set[Requirement]:
    """Load pipfile requirements."""
    with open(filename, "rb") as f:
        pipfile_data = tomli.load(f)

    packages = []
    for name, version in itertools.chain(
        pipfile_data.get("packages", {}).items(),
        pipfile_data.get("dev-packages", {}).items(),
    ):
        if isinstance(version, str):
            package_spec = f"{name}{version if version !='*' else ''}"
        else:
            assert isinstance(version, dict)
            extras = (
                ",".join(version.get("extras", [])) if version.get("extras", []) else ""
            )
            extras = f"[{extras}]" if extras else ""
            version_spec = version.get("version") if version.get("version") else ""
            package_spec = f"{name}{extras}{version_spec}"

        packages.append(Requirement(package_spec))

    return set(packages)


def load_tox_ini(file_name: str = TOX_INI) -> Set[Requirement]:
    """Load tox.ini requirements."""
    config = configparser.ConfigParser()
    config.read(file_name)
    packages = []
    for section in config.values():
        packages.extend(
            list(
                filter(
                    lambda x: (
                        x != "" and not x.startswith("{") and not x.startswith(".")
                    ),
                    section.get("deps", "").splitlines(),
                )
            )
        )
    return set(map(Requirement, packages))


def get_missing_packages() -> Tuple[Set[Requirement], Set[Requirement]]:
    """Get difference in tox.ini and pipfile."""
    in_pip = {package for package in load_pipfile() if package.name not in WHITELIST}
    in_tox = {package for package in load_tox_ini() if package.name not in WHITELIST}

    missing_in_tox = in_pip - in_tox
    missing_in_pip = in_tox - in_pip
    return missing_in_tox, missing_in_pip


def check_versions_are_correct() -> bool:
    """Check no missing packages."""
    missing_in_tox, missing_in_pip = get_missing_packages()
    if missing_in_tox:
        print("Packages defined in Pipfile and not found in tox.ini")
        for i in missing_in_tox:
            print("\t", str(i))

    if missing_in_pip:
        print("Packages defined in tox.ini and not found in Pipfile")
        for i in missing_in_pip:
            print("\t", str(i))

    return not (missing_in_pip or missing_in_tox)


if __name__ == "__main__":
    result = check_versions_are_correct()
    if not result:
        sys.exit(1)
    else:
        print("OK")
