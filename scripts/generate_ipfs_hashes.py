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

"""
This script generates the IPFS hashes for all packages.

This script requires that you have IPFS installed:
- https://docs.ipfs.io/guides/guides/install/
"""

import collections
import csv
import os
import shutil
import signal
import subprocess  # nosec
import sys
import time
from pathlib import Path
from typing import Dict

import ipfshttpclient

import yaml

from aea.configurations.base import _compute_fingerprint
from aea.helpers.ipfs.base import IPFSHashOnly

AUTHOR = "fetchai"
CORE_PATH = "aea"
CORE_PACKAGES = {
    "contracts": ["scaffold"],
    "connections": ["stub", "scaffold"],
    "protocols": ["default", "scaffold"],
    "skills": ["error", "scaffold"],
}
PACKAGE_PATH = "packages/fetchai"
PACKAGE_TYPES = ["agents", "connections", "contracts", "protocols", "skills"]
PACKAGE_HASHES_PATH = "packages/hashes.csv"
TEST_PACKAGE_HASHES_PATH = "tests/data/hashes.csv"
TEST_PATH = "tests/data"
TEST_PACKAGES = {
    "connections": ["dummy_connection"],
    "skills": ["dependencies_skill", "exception_skill", "dummy_skill"],
}


def ipfs_hashing(
    package_hashes: Dict[str, str],
    target_dir: str,
    package_type: str,
    package_name: str,
    ipfs_hash_only: IPFSHashOnly,
):
    """Hashes a package and its components."""
    print("Processing package {} of type {}".format(package_name, package_type))

    # load config file to get ignore patterns
    config = yaml.safe_load(next(Path(target_dir).glob("*.yaml")).open())
    ignore_patterns = config.get("fingerprint_ignore_patterns", [])
    if package_type != "agents":
        # hash inner components
        fingerprints_dict = _compute_fingerprint(Path(target_dir), ignore_patterns)
        # confirm ipfs only generates same hash:
        for file_name, ipfs_hash in fingerprints_dict.items():
            path = os.path.join(target_dir, file_name)
            ipfsho_hash = ipfs_hash_only.get(path)
            if ipfsho_hash != ipfs_hash:
                print("WARNING, hashes don't match for: {}".format(path))

        # update fingerprints
        file_name = package_type[:-1] + ".yaml"
        yaml_path = os.path.join(target_dir, file_name)
        file = open(yaml_path, mode="r")

        # read all lines at once
        whole_file = file.read()

        # close the file
        file.close()

        file = open(yaml_path, mode="r")

        # find and replace
        # TODO this can be simplified after https://github.com/fetchai/agents-aea/issues/932
        existing = ""
        fingerprint_block = False
        for line in file:
            if line.find("fingerprint:") == 0:
                existing += line
                fingerprint_block = True
            elif fingerprint_block:
                if line.find("  ") == 0:
                    # still inside fingerprint block
                    existing += line
                else:
                    # fingerprint block has ended
                    break

        if len(fingerprints_dict) > 0:
            replacement = "fingerprint:\n"
            ordered_fingerprints_dict = collections.OrderedDict(
                sorted(fingerprints_dict.items())
            )
            for file_name, ipfs_hash in ordered_fingerprints_dict.items():
                replacement += "  " + file_name + ": " + ipfs_hash + "\n"
        else:
            replacement = "fingerprint: {}\n"
        whole_file = whole_file.replace(existing, replacement)

        # close the file
        file.close()

        # update fingerprints
        with open(yaml_path, "w") as f:
            f.write(whole_file)

    # hash again to get outer hash (this time all files):
    # TODO we still need to ignore some files
    result_list = client.add(target_dir)
    for result_dict in result_list:
        if package_name == result_dict["Name"]:
            key = os.path.join(AUTHOR, package_type, package_name)
            package_hashes[key] = result_dict["Hash"]


def to_csv(package_hashes: Dict[str, str], path: str):
    """Outputs a dictionary to CSV."""
    try:
        ordered = collections.OrderedDict(sorted(package_hashes.items()))
        with open(path, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(ordered.items())
    except IOError:
        print("I/O error")


if __name__ == "__main__":

    # check we have ipfs
    res = shutil.which("ipfs")
    if res is None:
        print("Please install IPFS first!")
        sys.exit(1)

    package_hashes = {}  # type: Dict[str, str]
    test_package_hashes = {}  # type: Dict[str, str]

    try:
        # run the ipfs daemon
        process = subprocess.Popen(  # nosec
            ["ipfs", "daemon"], stdout=subprocess.PIPE, env=os.environ.copy(),
        )
        time.sleep(4.0)

        # connect ipfs client
        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
        ipfs_hash_only = IPFSHashOnly()

        # ipfs hash the core packages
        for package_type, package_names in CORE_PACKAGES.items():
            for package_name in package_names:
                target_dir = os.path.join(CORE_PATH, package_type, package_name)
                ipfs_hashing(
                    package_hashes,
                    target_dir,
                    package_type,
                    package_name,
                    ipfs_hash_only,
                )

        # ipfs hash the registry packages
        for package_type in PACKAGE_TYPES:
            path = os.path.join(PACKAGE_PATH, package_type)
            for (dirpath, dirnames, _filenames) in os.walk(path):
                if dirpath.count("/") > 2:
                    # don't hash subdirs
                    break
                for dirname in dirnames:
                    target_dir = os.path.join(dirpath, dirname)
                    ipfs_hashing(
                        package_hashes,
                        target_dir,
                        package_type,
                        dirname,
                        ipfs_hash_only,
                    )

        # ipfs hash the test packages
        for package_type, package_names in TEST_PACKAGES.items():
            for package_name in package_names:
                target_dir = os.path.join(TEST_PATH, package_name)
                ipfs_hashing(
                    test_package_hashes,
                    target_dir,
                    package_type,
                    package_name,
                    ipfs_hash_only,
                )

        # output the package hashes
        to_csv(package_hashes, PACKAGE_HASHES_PATH)
        to_csv(test_package_hashes, TEST_PACKAGE_HASHES_PATH)

    except Exception as e:
        print(e)

    finally:
        # terminate the ipfs daemon
        process.send_signal(signal.SIGINT)
        process.wait(timeout=10)

        poll = process.poll()
        if poll is None:
            process.terminate()
            process.wait(2)
