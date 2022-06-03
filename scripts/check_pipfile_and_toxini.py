#!/usr/bin/env python3
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

"""This script checks that dependencies in tox.ini and Pipfile match."""

import sys
from typing import Dict


# specified in setup.py
WHITELIST = {"base58": ">=1.0.3"}


def get_deps_in_pipfile(file: str = "Pipfile") -> Dict[str, str]:
    """
    Get the dependencies of the Pipfile.

    :param file: the file to check.
    :return: dictionary with dependencies and their versions
    """
    result: Dict[str, str] = WHITELIST
    with open(file, "r") as f:
        is_dev_dependency = False
        for line in f:
            if line == "[dev-packages]\n":
                is_dev_dependency = True
                continue
            if line == "[packages]\n":
                is_dev_dependency = True
                continue
            if not is_dev_dependency:
                continue
            try:
                package, version = line.split(" = ")
                result[package] = version.strip("\n").strip('"')
            except Exception:  # nosec # pylint: disable=broad-except
                pass

    return result


def check_versions_in_tox_correct(file: str = "tox.ini") -> None:
    """
    Check the versions in tox are matching the ones in Pipfile.

    :param file: the file to check.
    """
    dependencies = get_deps_in_pipfile()
    skip_dependencies = False

    with open(file, "r") as f:
        for line in f:
            if line.strip().startswith("[testenv_multi]"):
                skip_dependencies = True

            if "commands =" in line:
                skip_dependencies = False

            if skip_dependencies:
                continue

            for match_type in ["==", ">="]:
                if match_type in line:
                    name_part, version_part = line.split(match_type)
                    check_match(
                        name_part.strip(" "),
                        version_part.strip("\n"),
                        dependencies,
                        match_type,
                    )


def check_match(
    name_part: str, version_part: str, dependencies: Dict[str, str], match_type: str
) -> None:
    """Check for a match independencies."""
    result = False
    for package, version_and_match_type in dependencies.items():
        if package == name_part:
            if version_and_match_type == f"{match_type}{version_part}":
                result = True
                break
            print(
                f"Non-matching versions for package={package}, {name_part}. Expected='{version_and_match_type}', found='{match_type}{version_part}'."
            )
            sys.exit(1)

    if not result:
        print(f"Package not found for: {name_part}")
        sys.exit(1)


if __name__ == "__main__":
    check_versions_in_tox_correct()
    print("OK")
    sys.exit(0)
