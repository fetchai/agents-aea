#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

import json
import logging
import subprocess  # nosec
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple

import requests


IPFS_ENDPOINT = "https://gateway.autonolas.tech/ipfs"
MAX_WORKERS = 10
REQUEST_TIMEOUT = 10  # seconds


def check_ipfs_hash_pushed(ipfs_hash: str, retries: int = 5) -> Tuple[str, bool]:
    """Check that the given ipfs hash exists in the registry"""

    def check_ipfs() -> Tuple[str, bool]:
        try:
            url = f"{IPFS_ENDPOINT}/{ipfs_hash.strip()}"
            res = requests.get(url, timeout=REQUEST_TIMEOUT)
            logging.info(f"check_ipfs_hash_pushed response: {res.status_code}")
            return ipfs_hash, res.status_code == 200
        except requests.RequestException as e:
            logging.error(
                f"check_ipfs_hash_pushed failed to find {ipfs_hash} on IPFS: {e}"
            )
            return ipfs_hash, False

    found = check_ipfs()[1]
    while not found and retries:
        retries -= 1
        found = check_ipfs()[1]

    return ipfs_hash, found


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

    packages_json = json.loads(get_file_from_tag("packages/packages.json"))["dev"]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []

        for k, v in packages_json.items():
            print(f"Checking {k}:{v}...")
            futures.append(executor.submit(check_ipfs_hash_pushed, v))

        # Awaiting for results is blocking
        print("Awaiting for results...")
        future_results = [future.result() for future in futures]

        errors = []
        for future_result in future_results:
            # future_results is of the form [(checked_hash, check_result),]
            if not future_result[1]:
                errors.append(future_result[0])

        if errors:
            print(f"The following hashes were not found in IPFS registry: {errors}")
            sys.exit(1)
        print("OK")
