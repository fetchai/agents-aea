#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This CLI tool publishes the local packages to an IPFS node."""

from argparse import ArgumentParser, Namespace
from glob import glob
from pathlib import Path
from typing import List, Union

from aea_cli_ipfs.core import register_package  # type: ignore
from aea_cli_ipfs.ipfs_utils import IPFSDaemon, IPFSTool  # type: ignore


def get_arguments() -> Namespace:
    """Returns cli arguments."""
    parser = ArgumentParser()
    parser.add_argument(
        "--package-dir", "-pd", type=str, default="./packages", required=False
    )
    return parser.parse_args()


def get_package_list(packages_dir: Union[str, Path]) -> List[Path]:
    """Returns a list of package directories."""
    packages_dir = Path(packages_dir).absolute() / "*" / "*" / "*"
    return [
        Path(package_path)
        for package_path in glob(str(packages_dir))
        if Path(package_path).is_dir() and "__pycache__" not in package_path
    ]


def main() -> None:
    """Main function."""
    args = get_arguments()
    packages = get_package_list(args.package_dir)
    ipfs_tool = IPFSTool(addr="/ip4/127.0.0.1/tcp/5001/http")
    with IPFSDaemon():
        for package_path in packages:
            register_package(
                ipfs_tool=ipfs_tool, dir_path=str(package_path), no_pin=False
            )
    print("Done!")


if __name__ == "__main__":
    main()
