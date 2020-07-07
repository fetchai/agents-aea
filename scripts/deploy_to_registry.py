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
This script deploys all new packages to registry.
"""

import os
import shutil
import sys
from itertools import chain
from pathlib import Path
from typing import Set

from click.testing import CliRunner

import yaml

from aea.cli import cli
from aea.configurations.base import PackageId, PackageType, PublicId

CLI_LOG_OPTION = ["-v", "OFF"]

DEFAULT_CONFIG_FILE_PATHS = [
    Path("aea", "connections", "stub", "connection.yaml"),
    Path("aea", "protocols", "default", "protocol.yaml"),
    Path("aea", "protocols", "signing", "protocol.yaml"),
    Path("aea", "protocols", "state_update", "protocol.yaml"),
    Path("aea", "skills", "error", "skill.yaml"),
]


def default_config_file_paths():
    """Get (generator) the default config file paths."""
    for item in DEFAULT_CONFIG_FILE_PATHS:
        yield item


def get_public_id_from_yaml(configuration_file: Path):
    """
    Get the public id from yaml.

    :param configuration_file: the path to the config yaml
    """
    data = yaml.safe_load(configuration_file.open())
    author = data["author"]
    # handle the case when it's a package or agent config file.
    name = data["name"] if "name" in data else data["agent_name"]
    version = data["version"]
    return PublicId(author, name, version)


def find_all_packages_ids() -> Set[PackageId]:
    """Find all packages ids."""
    package_ids: Set[PackageId] = set()
    packages_dir = Path("packages")
    for configuration_file in chain(
        packages_dir.glob("*/*/*/*.yaml"), default_config_file_paths()
    ):
        package_type = PackageType(configuration_file.parts[-3][:-1])
        package_public_id = get_public_id_from_yaml(configuration_file)
        package_id = PackageId(package_type, package_public_id)
        package_ids.add(package_id)

    return package_ids


ALL_PACKAGE_IDS: Set[PackageId] = find_all_packages_ids()


def check_correct_author(runner: CliRunner) -> None:
    """
    Check whether the correct author is locally configured.

    :return: None
    """
    result = runner.invoke(cli, [*CLI_LOG_OPTION, "init"], standalone_mode=False,)
    if "{'author': 'fetchai'}" not in result.output:
        print("Log in with fetchai credentials. Stopping...")
        sys.exit(0)
    else:
        print("Logged in with fetchai credentials. Continuing...")


def push_package(package_id: PackageId, runner: CliRunner) -> None:
    """
    Pushes a package (protocol/contract/connection/skill) to registry.

    Specifically:
    - creates an empty agent project
    - adds the relevant package from local 'packages' dir (and its dependencies)
    - moves the relevant package out of vendor dir
    - pushes the relevant package to registry

    :param package_id: the package id
    :param runner: the cli runner
    :return: None
    """
    print(
        "Trying to push {}: {}".format(
            package_id.package_type.value, str(package_id.public_id)
        )
    )
    try:
        cwd = os.getcwd()
        agent_name = "some_agent"
        result = runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", "--empty", agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(agent_name)
        result = runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add",
                "--local",
                package_id.package_type.value,
                str(package_id.public_id),
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        src = os.path.join(
            "vendor",
            package_id.public_id.author,
            package_id.package_type.value + "s",
            package_id.public_id.name,
        )
        dest = os.path.join(
            package_id.package_type.value + "s", package_id.public_id.name
        )
        shutil.copytree(src, dest)
        result = runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "push",
                package_id.package_type.value,
                str(package_id.public_id),
            ],
            standalone_mode=False,
        )
        assert (
            result.exit_code == 0
        ), "Publishing {} with public_id '{}' failed with: {}".format(
            package_id.package_type, package_id.public_id, result.output
        )
    except Exception as e:  # pylint: disable=broad-except
        print("An exception occured: {}".format(e))
    finally:
        os.chdir(cwd)
        result = runner.invoke(
            cli, [*CLI_LOG_OPTION, "delete", agent_name], standalone_mode=False,
        )
        assert result.exit_code == 0
    print(
        "Successfully pushed {}: {}".format(
            package_id.package_type.value, str(package_id.public_id)
        )
    )


def publish_agent(package_id: PackageId, runner: CliRunner) -> None:
    """
    Publishes an agent to registry.

    Specifically:
    - fetches an agent project from local 'packages' dir (and its dependencies)
    - publishes the agent project to registry

    :param package_id: the package id
    :param runner: the cli runner
    :return: None
    """
    print(
        "Trying to push {}: {}".format(
            package_id.package_type.value, str(package_id.public_id)
        )
    )
    try:
        cwd = os.getcwd()
        result = runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fetch", "--local", str(package_id.public_id)],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(str(package_id.public_id.name))
        result = runner.invoke(
            cli, [*CLI_LOG_OPTION, "publish"], standalone_mode=False,
        )
        assert (
            result.exit_code == 0
        ), "Pushing {} with public_id '{}' failed with: {}".format(
            package_id.package_type, package_id.public_id, result.output
        )
    except Exception as e:  # pylint: disable=broad-except
        print("An exception occured: {}".format(e))
    finally:
        os.chdir(cwd)
        result = runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "delete", str(package_id.public_id.name)],
            standalone_mode=False,
        )
        assert result.exit_code == 0
    print(
        "Successfully pushed {}: {}".format(
            package_id.package_type.value, str(package_id.public_id)
        )
    )


def check_and_upload(package_id: PackageId, runner: CliRunner) -> None:
    """
    Check and upload.

    Checks whether a package is missing from registry. If it is missing, uploads it.

    :param package_id: the package id
    :param runner: the cli runner
    :return: None
    """
    result = runner.invoke(
        cli,
        [
            *CLI_LOG_OPTION,
            "search",
            package_id.package_type.value + "s",
            "--query",
            package_id.public_id.name,
        ],
        standalone_mode=False,
    )
    if not str(package_id.public_id) in result.output:
        if package_id.package_type == PackageType.AGENT:
            publish_agent(package_id, runner)
        else:
            push_package(package_id, runner)
    else:
        print(
            "The {} '{}' is already in the registry".format(
                package_id.package_type.value, str(package_id.public_id)
            )
        )


def upload_new_packages(runner: CliRunner) -> None:
    """
    Upload new packages.

    Checks whether packages are missing from registry in the dependency order.

    :param runner: the cli runner
    :return: None
    """
    print("\nPushing protocols:")
    for package_id in ALL_PACKAGE_IDS:
        if package_id.package_type != PackageType.PROTOCOL:
            continue
        check_and_upload(package_id, runner)
    print("\nPushing connections and contracts:")
    for package_id in ALL_PACKAGE_IDS:
        if package_id.package_type not in {
            PackageType.CONNECTION,
            PackageType.CONTRACT,
        }:
            continue
        check_and_upload(package_id, runner)
    print("\nPushing skills:")
    for package_id in ALL_PACKAGE_IDS:
        if package_id.package_type != PackageType.SKILL:
            continue
        check_and_upload(package_id, runner)
    print("\nPublishing agents:")
    for package_id in ALL_PACKAGE_IDS:
        if package_id.package_type != PackageType.AGENT:
            continue
        check_and_upload(package_id, runner)


if __name__ == "__main__":
    runner = CliRunner()
    check_correct_author(runner)
    upload_new_packages(runner)
    print("Done!")
    sys.exit(0)
