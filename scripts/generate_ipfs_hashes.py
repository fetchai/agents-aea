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
import argparse
import collections
import csv
import operator
import os
import pprint
import re
import shutil
import signal
import subprocess  # nosec
import sys
import time
import traceback
from pathlib import Path
from typing import Collection, Dict, List, Optional, Tuple, Type, cast

import ipfshttpclient

from aea.configurations.base import (
    AgentConfig,
    ConnectionConfig,
    ContractConfig,
    PackageConfiguration,
    PackageType,
    ProtocolConfig,
    SkillConfig,
    _compute_fingerprint,
)
from aea.configurations.loader import ConfigLoaders
from aea.helpers.yaml_utils import yaml_dump, yaml_dump_all


AUTHOR = "fetchai"
CORE_PATH = Path("aea")
TEST_PATH = Path("tests") / "data"
PACKAGE_HASHES_PATH = "packages/hashes.csv"
TEST_PACKAGE_HASHES_PATH = "tests/data/hashes.csv"

type_to_class_config = {
    PackageType.AGENT: AgentConfig,
    PackageType.PROTOCOL: ProtocolConfig,
    PackageType.CONNECTION: ConnectionConfig,
    PackageType.SKILL: SkillConfig,
    PackageType.CONTRACT: ContractConfig,
}  # type: Dict[PackageType, Type[PackageConfiguration]]


def _get_all_packages() -> List[Tuple[PackageType, Path]]:
    """
    Get all the hashable package of the repository.

    In particular, get them from:
    - aea/*
    - packages/*
    - tests/data/*

    :return: pairs of (package-type, path-to-the-package)
    """

    def package_type_and_path(package_path: Path) -> Tuple[PackageType, Path]:
        """Extract the package type from the path."""
        item_type_plural = package_path.parent.name
        item_type_singular = item_type_plural[:-1]
        return PackageType(item_type_singular), package_path

    CORE_PACKAGES = list(
        map(
            package_type_and_path,
            [
                CORE_PATH / "protocols" / "scaffold",
                CORE_PATH / "connections" / "scaffold",
                CORE_PATH / "contracts" / "scaffold",
                CORE_PATH / "skills" / "scaffold",
            ],
        )
    )

    PACKAGES = list(
        map(
            package_type_and_path,
            filter(operator.methodcaller("is_dir"), Path("packages").glob("*/*/*/")),
        )
    )

    TEST_PACKAGES = [
        (PackageType.AGENT, TEST_PATH / "dummy_aea"),
        (PackageType.CONNECTION, TEST_PATH / "dummy_connection"),
        (PackageType.CONTRACT, TEST_PATH / "dummy_contract"),
        (PackageType.PROTOCOL, TEST_PATH / "generator" / "t_protocol"),
        (PackageType.PROTOCOL, TEST_PATH / "generator" / "t_protocol_no_ct"),
        (PackageType.SKILL, TEST_PATH / "dependencies_skill"),
        (PackageType.SKILL, TEST_PATH / "exception_skill"),
        (PackageType.SKILL, TEST_PATH / "dummy_skill"),
    ]

    ALL_PACKAGES = CORE_PACKAGES + PACKAGES + TEST_PACKAGES
    return ALL_PACKAGES


def sort_configuration_file(config: PackageConfiguration) -> None:
    """Sort the order of the fields in the configuration files."""
    # load config file to get ignore patterns, dump again immediately to impose ordering
    assert config.directory is not None
    configuration_filepath = config.directory / config.default_configuration_filename
    if config.package_type == PackageType.AGENT:
        json_data = config.ordered_json
        component_configurations = json_data.pop("component_configurations")
        yaml_dump_all(
            [json_data] + component_configurations, configuration_filepath.open("w")
        )
    else:
        yaml_dump(config.ordered_json, configuration_filepath.open("w"))


def ipfs_hashing(
    client: ipfshttpclient.Client,
    configuration: PackageConfiguration,
    package_type: PackageType,
) -> Tuple[str, str, List[Dict]]:
    """
    Hashes a package and its components.

    :param client: a connected IPFS client.
    :param configuration: the package configuration.
    :param package_type: the package type.
    :return: the identifier of the hash (e.g. 'fetchai/protocols/default')
           | and the hash of the whole package.
    """
    # hash again to get outer hash (this time all files)
    # we still need to ignore some files
    #      use ignore patterns somehow
    # ignore_patterns = configuration.fingerprint_ignore_patterns # noqa: E800
    assert configuration.directory is not None
    result_list = client.add(
        configuration.directory,
        recursive=True,
        period_special=False,
        follow_symlinks=False,
    )
    key = os.path.join(
        configuration.author, package_type.to_plural(), configuration.directory.name,
    )
    # check that the last result of the list is for the whole package directory
    assert result_list[-1]["Name"] == configuration.directory.name
    directory_hash = result_list[-1]["Hash"]
    return key, directory_hash, result_list


def to_csv(package_hashes: Dict[str, str], path: str) -> None:
    """Outputs a dictionary to CSV."""
    try:
        ordered = collections.OrderedDict(sorted(package_hashes.items()))
        with open(path, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(ordered.items())
    except IOError:
        print("I/O error")


def from_csv(path: str) -> Dict[str, str]:
    """Load a CSV into a dictionary."""
    result = collections.OrderedDict({})  # type: Dict[str, str]
    with open(path, "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            assert len(row) == 2
            key, value = row
            result[key] = value
    return result


class IPFSDaemon:
    """
    Set up the IPFS daemon.

    :raises Exception: if IPFS is not installed.
    """

    def __init__(self, timeout: float = 15.0):
        """Initialise IPFS daemon."""
        # check we have ipfs
        self.timeout = timeout
        res = shutil.which("ipfs")
        if res is None:
            raise Exception("Please install IPFS first!")
        process = subprocess.Popen(  # nosec
            ["ipfs", "--version"], stdout=subprocess.PIPE, env=os.environ.copy(),
        )
        output, _ = process.communicate()
        if b"0.6.0" not in output:
            raise Exception(
                "Please ensure you have version 0.6.0 of IPFS daemon installed."
            )
        self.process = None  # type: Optional[subprocess.Popen]

    def __enter__(self) -> None:
        """Run the ipfs daemon."""
        self.process = subprocess.Popen(  # nosec
            ["ipfs", "daemon"], stdout=subprocess.PIPE, env=os.environ.copy(),
        )
        print("Waiting for {} seconds the IPFS daemon to be up.".format(self.timeout))
        time.sleep(self.timeout)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Terminate the ipfs daemon."""
        if self.process is None:
            return
        self.process.send_signal(signal.SIGTERM)
        self.process.wait(timeout=30)
        poll = self.process.poll()
        if poll is None:
            self.process.terminate()
            self.process.wait(2)


def load_configuration(
    package_type: PackageType, package_path: Path
) -> PackageConfiguration:
    """
    Load a configuration, knowing the type and the path to the package root.

    :param package_type: the package type.
    :param package_path: the path to the package root.
    :return: the configuration object.
    """
    configuration_class = type_to_class_config[package_type]
    configuration_filepath = (
        package_path / configuration_class.default_configuration_filename
    )

    loader = ConfigLoaders.from_package_type(package_type)
    with configuration_filepath.open() as fp:
        configuration_obj = loader.load(fp)
    configuration_obj._directory = package_path  # pylint: disable=protected-access
    return cast(PackageConfiguration, configuration_obj)


def assert_hash_consistency(
    fingerprint: Dict[str, str], path_prefix: Path, client: ipfshttpclient.Client
) -> None:
    """
    Check that our implementation of IPFS hashing for a package is correct against the true IPFS.

    :param fingerprint: the fingerprint dictionary.
    :param path_prefix: the path prefix to prepend.
    :param client: the client.
    """
    # confirm ipfs only generates same hash:
    for file_name, ipfs_hash in fingerprint.items():
        path = path_prefix / file_name
        expected_ipfs_hash = client.add(path)["Hash"]
        assert (
            expected_ipfs_hash == ipfs_hash
        ), "WARNING, hashes don't match for: {}".format(path)


def _replace_fingerprint_non_invasive(
    fingerprint_dict: Dict[str, str], text: str
) -> str:
    """
    Replace the fingerprint in a configuration file (not invasive).

    We need this function because libraries like `yaml` may modify the
    content of the .yaml file when loading/dumping. Instead,
    working with the content of the file gives us finer granularity.

    :param fingerprint_dict: the fingerprint dictionary.
    :param text: the content of a configuration file.
    :return: the updated content of the configuration file.
    """

    def to_row(x: Tuple[str, str]) -> str:
        return x[0] + ": " + x[1]

    replacement = "\nfingerprint:\n  {}\n".format(
        "\n  ".join(map(to_row, sorted(fingerprint_dict.items())))
    )
    return re.sub(r"\nfingerprint:\W*\n(?:\W+.*\n)*", replacement, text)


def compute_fingerprint(  # pylint: disable=unsubscriptable-object
    package_path: Path,
    fingerprint_ignore_patterns: Optional[Collection[str]],
    client: ipfshttpclient.Client,
) -> Dict[str, str]:
    """
    Compute the fingerprint of a package.

    :param package_path: path to the package.
    :param fingerprint_ignore_patterns: filename patterns whose matches will be ignored.
    :param client: the IPFS Client. It is used to compare our implementation with the true implementation of IPFS hashing.
    :return: the fingerprint
    """
    fingerprint = _compute_fingerprint(
        package_path, ignore_patterns=fingerprint_ignore_patterns,
    )
    assert_hash_consistency(fingerprint, package_path, client)
    return fingerprint


def update_fingerprint(
    configuration: PackageConfiguration, client: ipfshttpclient.Client
) -> None:
    """
    Update the fingerprint of a package.

    :param configuration: the configuration object.
    :param client: the IPFS Client. It is used to compare our implementation with the true implementation of IPFS hashing.
    :return: None
    """
    # we don't process agent configurations
    if isinstance(configuration, AgentConfig):
        return
    assert configuration.directory is not None
    fingerprint = compute_fingerprint(
        configuration.directory, configuration.fingerprint_ignore_patterns, client
    )
    config_filepath = (
        configuration.directory / configuration.default_configuration_filename
    )
    old_content = config_filepath.read_text()
    new_content = _replace_fingerprint_non_invasive(fingerprint, old_content)
    config_filepath.write_text(new_content)


def check_fingerprint(
    configuration: PackageConfiguration, client: ipfshttpclient.Client
) -> bool:
    """
    Check the fingerprint of a package, given the loaded configuration file.

    :param configuration: the configuration object.
    :param client: the IPFS Client. It is used to compare our implementation with the true implementation of IPFS hashing.
    :return: True if the fingerprint match, False otherwise.
    """
    # we don't process agent configurations
    if isinstance(configuration, AgentConfig):
        return True
    assert configuration.directory is not None
    expected_fingerprint = compute_fingerprint(
        configuration.directory, configuration.fingerprint_ignore_patterns, client
    )
    actual_fingerprint = configuration.fingerprint
    result = expected_fingerprint == actual_fingerprint
    if not result:
        print(
            "Fingerprints do not match for {} in {}".format(
                configuration.name, configuration.directory
            )
        )
    return result


def parse_arguments() -> argparse.Namespace:
    """Parse arguments."""
    script_name = Path(__file__).name
    parser = argparse.ArgumentParser(
        script_name, description="Generate/check hashes of packages."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Only check if the hashes are up-to-date.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Time to wait before IPFS daemon is up and running.",
    )

    arguments_ = parser.parse_args()
    return arguments_


def update_hashes(timeout: float = 15.0) -> int:
    """
    Process all AEA packages, update fingerprint, and update hashes.csv files.

    :param timeout: timeout to the update.
    :return: exit code. 0 for success, 1 if an exception occurred.
    """
    return_code_ = 0
    package_hashes = {}  # type: Dict[str, str]
    test_package_hashes = {}  # type: Dict[str, str]
    # run the ipfs daemon
    with IPFSDaemon(timeout=timeout):
        try:
            # connect ipfs client
            client = ipfshttpclient.connect(
                "/ip4/127.0.0.1/tcp/5001/http"
            )  # type: ipfshttpclient.Client

            # ipfs hash the packages
            for package_type, package_path in _get_all_packages():
                print(
                    "Processing package {} of type {}".format(
                        package_path.name, package_type
                    )
                )
                configuration_obj = load_configuration(package_type, package_path)
                sort_configuration_file(configuration_obj)
                update_fingerprint(configuration_obj, client)
                key, package_hash, _ = ipfs_hashing(
                    client, configuration_obj, package_type
                )
                if TEST_PATH in package_path.parents:
                    test_package_hashes[key] = package_hash
                else:
                    package_hashes[key] = package_hash

            # output the package hashes
            to_csv(package_hashes, PACKAGE_HASHES_PATH)
            to_csv(test_package_hashes, TEST_PACKAGE_HASHES_PATH)

            print("Done!")
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()
            return_code_ = 1

    return return_code_


def check_same_ipfs_hash(
    client: ipfshttpclient,
    configuration: PackageConfiguration,
    package_type: PackageType,
    all_expected_hashes: Dict[str, str],
) -> bool:
    """
    Compute actual package hash and compare with expected hash.

    :param client: the IPFS client.
    :param configuration: the configuration object of the package.
    :param package_type: the type of package.
    :param all_expected_hashes: the dictionary of all the expected hashes.
    :return: True if the IPFS hash match, False otherwise.
    """
    # if configuration.name in [
    #     "erc1155",
    #     "carpark_detection",
    #     "p2p_libp2p",
    #     "Agent0",
    #     "dummy",
    # ]: # noqa: E800
    #     return True  # packages with nested dirs or symlinks, kept for reference # noqa: E800
    key, actual_hash, result_list = ipfs_hashing(client, configuration, package_type)
    expected_hash = all_expected_hashes[key]
    result = actual_hash == expected_hash
    if not result:
        print(
            f"IPFS Hashes do not match for {configuration.name} in {configuration.directory}"
        )
        print(f"Expected: {expected_hash}")
        print(f"Actual:   {actual_hash}")
        print("All the hashes: ", pprint.pformat(result_list))
    return result


def check_hashes(timeout: float = 15.0) -> int:
    """
    Check fingerprints and outer hash of all AEA packages.

    :param timeout: timeout to the check.
    :return: exit code. 1 if some fingerprint/hash don't match or if an exception occurs, 0 in case of success.
    """
    return_code_ = 0
    failed = False
    expected_package_hashes = from_csv(PACKAGE_HASHES_PATH)  # type: Dict[str, str]
    expected_test_package_hashes = from_csv(
        TEST_PACKAGE_HASHES_PATH
    )  # type: Dict[str, str]
    all_expected_hashes = {**expected_package_hashes, **expected_test_package_hashes}
    with IPFSDaemon(timeout=timeout):
        try:
            # connect ipfs client
            client = ipfshttpclient.connect(
                "/ip4/127.0.0.1/tcp/5001/http"
            )  # type: ipfshttpclient.Client

            for package_type, package_path in _get_all_packages():
                configuration_obj = load_configuration(package_type, package_path)
                failed = failed or not check_fingerprint(configuration_obj, client)
                failed = failed or not check_same_ipfs_hash(
                    client, configuration_obj, package_type, all_expected_hashes
                )
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()
            failed = True

    if failed:
        return_code_ = 1
    else:
        print("OK!")

    return return_code_


def clean_directory() -> None:
    """Clean the directory."""
    clean_command = ["make", "clean"]
    process = subprocess.Popen(clean_command, stdout=subprocess.PIPE)  # nosec
    _, _ = process.communicate()


if __name__ == "__main__":
    arguments = parse_arguments()
    if arguments.check:
        return_code = check_hashes(arguments.timeout)
    else:
        clean_directory()
        return_code = update_hashes(arguments.timeout)

    sys.exit(return_code)
