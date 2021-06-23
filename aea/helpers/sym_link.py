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
"""Sym link implementation for Linux, MacOS, and Windows."""

import contextlib
import os
from functools import reduce
from pathlib import Path
from typing import Generator


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
def cd(path: Path) -> Generator:
    """Change directory with context manager."""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
        os.chdir(old_cwd)
    except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
        os.chdir(old_cwd)
        raise e from e


def create_symlink(link_path: Path, target_path: Path, root_path: Path) -> int:
    """
    Change directory and call the cross-platform script.

    The working directory must be the parent of the symbolic link name
    when executing 'create_symlink_crossplatform.sh'. Hence, we
    need to translate target_path into the relative path from the
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

    :param link_path: the source path
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
