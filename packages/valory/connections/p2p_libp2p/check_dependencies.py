#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Check that the dependencies 'gcc' and 'go' are installed in the system."""
import asyncio
import os
import platform
import re
import shutil
import subprocess  # nosec
import sys
import tempfile
from distutils.dir_util import copy_tree
from itertools import islice
from subprocess import Popen, TimeoutExpired  # nosec
from typing import Iterable, List, Optional, Pattern, Tuple

from aea.helpers.base import ensure_dir


try:
    # flake8: noqa
    # pylint: disable=unused-import,ungrouped-imports
    from .consts import (  # type: ignore
        LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT,
        LIBP2P_NODE_MODULE,
        LIBP2P_NODE_MODULE_NAME,
    )
except ImportError:  # pragma: nocover
    # flake8: noqa
    # pylint: disable=unused-import,ungrouped-imports
    from consts import (  # type: ignore
        LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT,
        LIBP2P_NODE_MODULE,
        LIBP2P_NODE_MODULE_NAME,
    )

from aea.exceptions import AEAException


ERROR_MESSAGE_TEMPLATE_BINARY_NOT_FOUND = "'{command}' is required by the libp2p connection, but it is not installed, or it is not accessible from the system path."
ERROR_MESSAGE_TEMPLATE_VERSION_TOO_LOW = "The installed version of '{command}' is too low: expected at least {lower_bound}; found {actual_version}."

# for the purposes of this script,
# a version is a tuple of integers: (major, minor, patch)
VERSION = Tuple[int, int, int]
MINIMUM_GO_VERSION: VERSION = (1, 13, 0)
MINIMUM_GCC_VERSION: VERSION = (7, 5, 0)


def nth(iterable: Iterable, n: int, default: int = 0) -> int:
    """Returns the nth item or a default value"""
    return next(islice(iterable, n, None), default)


def get_version(*args: int) -> VERSION:
    """
    Get the version from a list of arguments.

    Set to '0' if there are not enough arguments.

    :param args: positional arguments
    :return: the version
    """
    major = nth(args, 0, 0)
    minor = nth(args, 1, 0)
    patch = nth(args, 2, 0)
    return major, minor, patch


def version_to_string(version: VERSION) -> str:
    """
    Transform version to string.

    :param version: the version.
    :return: the string representation.
    """
    return ".".join(map(str, version))


def print_ok_message(
    binary_name: str, actual_version: VERSION, version_lower_bound: VERSION
) -> None:
    """
    Print OK message.

    :param binary_name: the binary binary_name.
    :param actual_version: the actual version.
    :param version_lower_bound: the version lower bound.
    """
    print(
        f"check '{binary_name}'>={version_to_string(version_lower_bound)}, found {version_to_string(actual_version)}"
    )


def check_binary(
    binary_name: str,
    args: List[str],
    version_regex: Pattern,
    version_lower_bound: VERSION,
) -> None:
    """
    Check a binary is accessible from the terminal.

    It breaks down in:
    1) check if the binary is reachable from the system path;
    2) check that the version number is higher or equal than the minimum required version.

    :param binary_name: the name of the binary.
    :param args: the arguments to provide to the binary to retrieve the version.
    :param version_regex: the regex used to extract the version from the output.
    :param version_lower_bound: the minimum required version.
    """
    path = shutil.which(binary_name)
    if not path:
        raise AEAException(
            ERROR_MESSAGE_TEMPLATE_BINARY_NOT_FOUND.format(command=binary_name)
        )

    version_getter_command = [binary_name, *args]
    stdout = subprocess.check_output(version_getter_command).decode("utf-8")  # nosec
    version_match = version_regex.search(stdout)
    if version_match is None:
        print(
            f"Warning: cannot parse '{binary_name}' version from command: {version_getter_command}. stdout: {stdout}"
        )
        return
    actual_version: VERSION = get_version(*map(int, version_match.groups(default="0")))
    if actual_version < version_lower_bound:
        raise AEAException(
            ERROR_MESSAGE_TEMPLATE_VERSION_TOO_LOW.format(
                command=binary_name,
                lower_bound=version_to_string(version_lower_bound),
                actual_version=version_to_string(actual_version),
            )
        )

    print_ok_message(binary_name, actual_version, version_lower_bound)


def check_versions() -> None:
    """Check versions."""
    check_binary(
        "go",
        ["version"],
        re.compile(r"go version go([0-9]+)\.([0-9]+)"),
        MINIMUM_GO_VERSION,
    )
    if platform.system() == "Darwin":
        check_binary(  # pragma: nocover
            "gcc",
            ["--version"],
            re.compile(r"clang version.* ([0-9]+)\.([0-9]+)\.([0-9]+) "),
            MINIMUM_GCC_VERSION,
        )
    else:
        check_binary(
            "gcc",
            ["--version"],
            re.compile(r"gcc.* ([0-9]+)\.([0-9]+)\.([0-9]+)"),
            MINIMUM_GCC_VERSION,
        )


def main() -> None:  # pragma: nocover
    """The main entrypoint of the script."""
    if len(sys.argv) < 2:
        raise ValueError("Please provide build directory path as an argument!")
    build_dir = sys.argv[1]
    check_versions()
    build_node(build_dir)


def _golang_module_build(
    path: str,
    timeout: float = LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT,
) -> Optional[str]:
    """
    Builds go module located at `path`, downloads necessary dependencies

    :param path: the path to the node code
    :param timeout: the build timeout
    :return: str with logs or error description if happens
    """
    proc = Popen(  # nosec
        ["go", "build"],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=path,
        env=os.environ,
    )

    try:
        stdout, _ = proc.communicate(timeout=timeout)  # type: ignore
    except TimeoutExpired:  # pragma: nocover
        proc.terminate()
        proc.wait(timeout=timeout)
        return "terminated by timeout"

    if proc.returncode != 0:  # pragma: nocover
        return stdout.decode()  # type: ignore
    return None


def build_node(build_dir: str) -> None:
    """Build node placed inside build_dir."""
    with tempfile.TemporaryDirectory() as dirname:
        copy_tree(LIBP2P_NODE_MODULE, dirname)
        err_str = _golang_module_build(dirname)
        if err_str:  # pragma: nocover
            raise Exception(f"Node build failed: {err_str}")
        ensure_dir(build_dir)
        shutil.copy(
            os.path.join(dirname, LIBP2P_NODE_MODULE_NAME),
            os.path.join(build_dir, LIBP2P_NODE_MODULE_NAME),
        )
    print(f"{LIBP2P_NODE_MODULE_NAME} built successfully!")


if __name__ == "__main__":
    main()  # pragma: nocover
