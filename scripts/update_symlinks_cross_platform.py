#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

import contextlib
import inspect
import os
import sys
import traceback
from functools import reduce
from pathlib import Path
from typing import Generator, List, Tuple, Union


SCRIPTS_PATH = Path(os.path.dirname(inspect.getfile(inspect.currentframe())))  # type: ignore
ROOT_PATH = SCRIPTS_PATH.parent.absolute()
TEST_DATA = ROOT_PATH / "tests" / "data"
TEST_DUMMY_AEA_DIR = TEST_DATA / "dummy_aea"
FETCHAI_PACKAGES = ROOT_PATH / "packages" / "fetchai"
OPEN_AEA_PACKAGES = ROOT_PATH / "packages" / "open_aea"

SYMLINKS = [
    (TEST_DUMMY_AEA_DIR / "skills" / "dummy", TEST_DATA / "dummy_skill"),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "protocols" / "default",
        FETCHAI_PACKAGES / "protocols" / "default",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "open_aea" / "protocols" / "signing",
        OPEN_AEA_PACKAGES / "protocols" / "signing",
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
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "contracts" / "erc1155",
        FETCHAI_PACKAGES / "contracts" / "erc1155",
    ),
    (
        TEST_DUMMY_AEA_DIR / "vendor" / "fetchai" / "skills" / "error",
        FETCHAI_PACKAGES / "skills" / "error",
    ),
]  # type: List[Tuple[Path, Path]]
"""A list of pairs: (link_path, target_path)"""


def make_symlink(link_name: str, target: str) -> None:
    """
    Make a symbolic link, cross platform.

    :param link_name: the link name.
    :param target: the target.
    """
    try:
        Path(link_name).unlink()
    except FileNotFoundError:
        pass
    Path(link_name).symlink_to(target, target_is_directory=True)


@contextlib.contextmanager
def cd(path: Union[Path, str]) -> Generator:
    """Change directory with context manager."""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
        os.chdir(old_cwd)
    except Exception as e:  # pylint: disable=broad-except
        os.chdir(old_cwd)
        raise e from e


def create_symlink(link_path: Path, target_path: Path, root_path: Path) -> int:
    """
    Change directory and call the cross-platform script.

    The working directory must be the parent of the symbolic link name
    when executing 'create_symlink_crossplatform.sh'. Hence, we
    need to translate target_path into the relatve path from the
    symbolic link directory to the target directory.

    So:
    1) from link_path, extract the number of jumps to the parent directory
      in order to reach the repository root directory, and chain many "../" paths.
    2) from target_path, compute the relative path to the root
    3) relative_target_path is just the concatenation of the results from step (1) and (2).


    For instance, given
    - link_path: './directory_1//symbolic_link
    - target_path: './directory_2/target_path

    we want to compute:
    - link_path: 'symbolic_link' (just the last bit)
    - relative_target_path: '../../directory_1/target_path'

    The resulting command on UNIX systems will be:

        cd directory_1 && ln -s ../../directory_1/target_path symbolic_link

    :param link_path: the link path
    :param target_path: the target path
    :param root_path: the root path
    :return: exit code
    """
    working_directory = link_path.parent
    target_relative_to_root = target_path.relative_to(root_path)
    cwd_relative_to_root = working_directory.relative_to(root_path)
    nb_parents = len(cwd_relative_to_root.parents)
    root_relative_to_cwd = reduce(
        lambda x, y: x / y, [Path("../")] * nb_parents, Path(".")
    )
    link_name = link_path.name
    target = root_relative_to_cwd / target_relative_to_root
    with cd(working_directory.absolute()):
        make_symlink(str(link_name), str(target))
    return 0


def main() -> None:
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
