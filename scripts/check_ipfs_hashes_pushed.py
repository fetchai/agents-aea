#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the tools for checking that all packages have been pushed to the ipfs registry."""

import subprocess  # nosec
import sys
from typing import Optional

import requests


IPFS_ENDPOINT = "https://gateway.autonolas.tech/ipfs"


def check_ipfs_hash_pushed(ipfs_hash: str) -> bool:
    """Check that the given ipfs hash exists in the registry"""
    try:
        url = f"{IPFS_ENDPOINT}/{ipfs_hash.strip()}"
        res = requests.get(url, timeout=120)
        return res.status_code == 200
    except requests.RequestException:
        return False


def get_latest_git_tag() -> str:
    """Get the latest git tag"""
    res = subprocess.run(  # nosec
        [
            "git",
            "tag",
            "--sort=-committerdate",
        ],  # sort by commit date in descending order
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    stdout = res.stdout.decode("utf-8")
    return stdout.split("\n")[0].strip()


def get_file_from_tag(file_path: str, latest_tag: Optional[str] = None) -> str:
    """Get a specific file version from the commit history given a tag/commit"""
    latest_tag = latest_tag or get_latest_git_tag()
    print(f"Checking hashes for tag {latest_tag}")
    res = subprocess.run(  # nosec
        ["git", "show", f"{latest_tag}:{file_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return res.stdout.decode("utf-8")


if __name__ == "__main__":
    # Get all hashes from the latest tag, excluding the scaffold ones (that are not pushed)
    # need to fix this after the release
    hashes = [
        line.split(",")[-1]
        for line in get_file_from_tag("packages/hashes.csv").split("\n")
        if line and "/scaffold," not in line
    ]

    errors = []
    for h in hashes:
        if not check_ipfs_hash_pushed(h):
            errors.append(h)

    if errors:
        print(f"The following hashes were not found in IPFS registry: {errors}")
        sys.exit(1)
    print("OK")
