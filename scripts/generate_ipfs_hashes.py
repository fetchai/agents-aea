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
from typing import Dict

import ipfshttpclient

AUTHOR = "fetchai"
CORE_PATH = "aea"
CORE_PACKAGES = {"connections": "stub", "protocols": "default", "skills": "error"}
PACKAGE_PATH = "packages/fetchai"
PACKAGE_TYPES = ["agents", "connections", "protocols", "skills"]
PACKAGE_HASHES_PATH = "packages/hashes.csv"


def ipfs_hashing(
    package_hashes: Dict[str, str],
    target_dir: str,
    package_type: str,
    package_name: str,
):
    """Hashes a package and its components."""
    print("Processing package {} of type {}".format(package_name, package_type))

    if package_type == "agents":
        fingerprints = str({})
    else:
        # hash inner components (all `.py` files)
        result_list = client.add(target_dir, pattern="*.py")

        fingerprints_dict = {}
        # get hashes of all `.py` files
        for result_dict in result_list:
            if package_name == result_dict["Name"]:
                continue
            if not result_dict["Name"][-3:] == ".py":
                continue
            key = result_dict["Name"].replace(package_name + "/", "", 1)
            fingerprints_dict[key] = result_dict["Hash"]
        fingerprints = str(fingerprints_dict)

    # update fingerprints
    file_name = (
        "aea-config.yaml" if package_type == "agents" else package_type[:-1] + ".yaml"
    )
    yaml_path = os.path.join(target_dir, file_name)
    file = open(yaml_path, mode="r")

    # read all lines at once
    whole_file = file.read()

    # close the file
    file.close()

    file = open(yaml_path, mode="r")

    # find and replace
    for line in file:
        if line.find("fingerprint:") == 0:
            whole_file = whole_file.replace(line, "fingerprint: " + fingerprints + "\n")
            break

    # close the file
    file.close()

    # update fingerprints
    with open(yaml_path, "w") as f:
        f.write(whole_file)

    # hash again to get outer hash (this time all files):
    result_list = client.add(target_dir)
    for result_dict in result_list:
        if package_name == result_dict["Name"]:
            key = os.path.join(AUTHOR, package_type, package_name)
            package_hashes[key] = result_dict["Hash"]


def to_csv(package_hashes: Dict[str, str]):
    """Outputs a dictionary to CSV."""
    try:
        ordered = collections.OrderedDict(sorted(package_hashes.items()))
        with open(PACKAGE_HASHES_PATH, "w") as csv_file:
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

    # run the ipfs daemon
    process = subprocess.Popen(  # nosec
        ["ipfs", "daemon"], stdout=subprocess.PIPE, env=os.environ.copy(),
    )
    time.sleep(2.0)

    package_hashes = {}  # type: Dict[str, str]

    try:
        # connect ipfs client
        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")

        # ipfs hash the core packages
        for package_type, package_name in CORE_PACKAGES.items():
            target_dir = os.path.join(CORE_PATH, package_type, package_name)
            ipfs_hashing(package_hashes, target_dir, package_type, package_name)

        # ipfs hash the registry packages
        for package_type in PACKAGE_TYPES:
            path = os.path.join(PACKAGE_PATH, package_type)
            for (dirpath, dirnames, _filenames) in os.walk(path):
                if dirpath.count("/") > 2:
                    # don't hash subdirs
                    break
                for dirname in dirnames:
                    target_dir = os.path.join(dirpath, dirname)
                    ipfs_hashing(package_hashes, target_dir, package_type, dirname)

        # output the package hashes
        to_csv(package_hashes)

    except Exception as e:
        print(e)

    finally:
        # terminate the ipfs daemon
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
