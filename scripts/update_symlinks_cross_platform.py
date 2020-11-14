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
# pylint: disable=cyclic-import

"""This script will update the symlinks of the project, cross-platform compatible."""

import inspect
import os
import sys
import traceback
from pathlib import Path
from typing import List, Tuple

from aea.helpers.sym_link import create_symlink


SCRIPTS_PATH = Path(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore
ROOT_PATH = SCRIPTS_PATH.parent.absolute()
TEST_DATA = ROOT_PATH / "tests" / "data"
TEST_DUMMY_AEA_DIR = TEST_DATA / "dummy_aea"
FETCHAI_PACKAGES = ROOT_PATH / "packages" / "fetchai"

SYMLINKS = [
    (TEST_DUMMY_AEA_DIR / "skills" / "dummy", TEST_DATA / "dummy_skill"),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "protocols" / "default",
        FETCHAI_PACKAGES / "protocols" / "default",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "protocols" / "signing",
        FETCHAI_PACKAGES / "protocols" / "signing",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "protocols" / "state_update",
        FETCHAI_PACKAGES / "protocols" / "state_update",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "protocols" / "fipa",
        FETCHAI_PACKAGES / "protocols" / "fipa",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "protocols" / "oef_search",
        FETCHAI_PACKAGES / "protocols" / "oef_search",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "connections" / "local",
        FETCHAI_PACKAGES / "connections" / "local",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "connections" / "p2p_libp2p",
        FETCHAI_PACKAGES / "connections" / "p2p_libp2p",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "contracts" / "erc1155",
        FETCHAI_PACKAGES / "contracts" / "erc1155",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "skills" / "error",
        FETCHAI_PACKAGES / "skills" / "error",
    ),
]  # type: List[Tuple[Path, Path]]
"""A list of pairs: (link_path, target_path)"""


def main():
    """Run main script."""
    failed = False
    for link_name, target in SYMLINKS:
        print("Linking {} to {}".format(link_name, target))
        try:
            link_name.unlink()
        except FileNotFoundError:
            pass
        try:
            return_code = create_symlink(link_name, target, ROOT_PATH)
        except Exception as e:  # pylint: disable=broad-except
            exception = e
            return_code = 1
            traceback.print_exc()
            print(
                "Last command failed with return code {} and exception {}".format(
                    return_code, exception
                )
            )
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
