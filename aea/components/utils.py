# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""This module contains the component loading utils."""


import re
import sys
from pathlib import Path
from typing import Dict, List

from aea.components.base import perform_load_aea_package
from aea.configurations.constants import CONNECTIONS, CONTRACTS, PROTOCOLS, SKILLS


PACKAGES_RE = re.compile(r"^packages\.(\w+)\.(\w+)\.(\w+)$", re.I)


def _enlist_component_packages() -> Dict[str, List[Dict[str, str]]]:
    """List all components packages already loaded."""
    result: Dict[str, List[Dict[str, str]]] = {}

    for name, mod in sys.modules.items():
        match = PACKAGES_RE.match(name)
        if not match:
            continue
        author, package_type, package_name = match.groups()
        packages = result.get(package_type, [])
        package_data = {
            "author": author,
            "package_type": package_type,
            "package_name": package_name,
            "dir": mod.__dict__["__path__"][0],
        }
        packages.append(package_data)
        result[package_type] = packages
    return result


# no cover cause executed in a subprocess, not possible to track
def _populate_packages(packages: dict) -> None:  # pragma: nocover
    """Load packages as python modules."""
    for package_type in [PROTOCOLS, CONTRACTS, CONNECTIONS, SKILLS]:
        for package in packages.get(package_type, []):
            # load package
            print(11, package)
            perform_load_aea_package(
                dir_=Path(package["dir"]),
                author=package["author"],
                package_type_plural=package["package_type"],
                package_name=package["package_name"],
            )
