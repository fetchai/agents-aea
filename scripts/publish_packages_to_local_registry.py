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

"""This CLI tool publishes the local packages to an IPFS node."""

from argparse import ArgumentParser, Namespace
from glob import glob
from pathlib import Path
from subprocess import run
from typing import List, Union


def get_arguments() -> Namespace:
    """Returns cli arguments."""
    parser = ArgumentParser()
    parser.add_argument(
        "--package_dir", "-pd", type=str, default="./packages", required=False
    )
    return parser.parse_args()


def get_package_list(packages_dir: Union[str, Path]) -> List[Path]:
    """Returns a list of package directories."""
    packages_dir = Path(packages_dir).absolute() / "*" / "*" / "*"
    return [
        Path(package_path)
        for package_path in glob(str(packages_dir))
        if Path(package_path).is_dir()
    ]


def main() -> None:
    """Main function."""
    args = get_arguments()
    packages = get_package_list(args.package_dir)
    for package_path in packages:
        print(f"Processing package: {package_path}")
        run(["python3", "-m", "aea.cli", "ipfs", "add", str(package_path)], check=False)
    print("Done!")


if __name__ == "__main__":
    main()
