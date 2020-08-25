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
Updates package versions relative to last release.

Run this script from the root of the project directory:

    python scripts/update_package_versions.py

"""

import argparse
import os
import re
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Dict

from click.testing import CliRunner

import semver

import yaml

from aea.cli import cli
from aea.configurations.base import PublicId
from aea.configurations.loader import ConfigLoader

from scripts.generate_ipfs_hashes import update_hashes

DIRECTORIES = ["packages", "aea", "docs", "benchmark", "examples", "tests"]
CLI_LOG_OPTION = ["-v", "OFF"]
TYPES = ["protocols", "contracts", "connections", "skills", "agents"]
HASHES_CSV = "hashes.csv"
TYPE_TO_CONFIG_FILE = {
    "connections": "connection.yaml",
    "protocols": "protocol.yaml",
    "contracts": "contract.yaml",
    "skills": "skill.yaml",
    "agents": "aea-config.yaml",
}
PUBLIC_ID_REGEX = PublicId.PUBLIC_ID_REGEX[1:-1]


def check_positive(value):
    """Check value is an int."""
    try:
        ivalue = int(value)
        assert ivalue <= 0
    except (AssertionError, ValueError):
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return ivalue


parser = argparse.ArgumentParser()
parser.add_argument(
    "-n",
    "--no-interactive",
    action="store_true",
    default=False,
    help="Don't ask user confirmation for replacement.",
)
parser.add_argument(
    "-C",
    "--context",
    type=check_positive,
    default=3,
    help="The number of above/below rows to display",
)

parser.add_argument(
    "-r",
    "--replace-by-default",
    action="store_true",
    default=False,
    help="If --no-interactive is set, apply the replacement (default: False).",
)

arguments: argparse.Namespace = None  # type: ignore


def check_if_running_allowed() -> None:
    """
    Check if we can run the script.

    Script should only be run on a clean branch.
    """
    git_call = subprocess.Popen(["git", "diff"], stdout=subprocess.PIPE)  # nosec
    (stdout, _) = git_call.communicate()
    git_call.wait()
    if len(stdout) > 0:
        print("Cannot run script in unclean git state.")
        sys.exit(1)


def run_hashing() -> None:
    """Run the hashing script."""
    hashing_call = update_hashes()
    if hashing_call == 1:
        print("Problem when running IPFS script!")
        sys.exit(1)


def get_hashes_from_last_release() -> Dict[str, str]:
    """Get hashes from last release."""
    svn_call = subprocess.Popen(  # nosec
        [
            "svn",
            "export",
            "https://github.com/fetchai/agents-aea.git/trunk/packages/{}".format(
                HASHES_CSV
            ),
        ]
    )
    svn_call.wait()
    hashes = {}  # Dict[str, str]
    with open(HASHES_CSV) as f:
        for line in f:
            split = line.split(",")
            hashes[split[0]] = split[1].rstrip()
    os.remove(HASHES_CSV)
    return hashes


def get_hashes_from_current_release() -> Dict[str, str]:
    """Get hashes from last release."""
    hashes = {}  # Dict[str, str]
    with open(os.path.join("packages", HASHES_CSV)) as f:
        for line in f:
            split = line.split(",")
            hashes[split[0]] = split[1].rstrip()
    return hashes


def split_hashes_by_type(all_hashes: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """Split hashes by type."""
    result = {
        "agents": {},
        "protocols": {},
        "contracts": {},
        "connections": {},
        "skills": {},
    }  # type: Dict[str, Dict[str, str]]
    for key, value in all_hashes.items():
        if "fetchai" not in key:
            print("Non-fetchai packages not allowed!")
            sys.exit(1)
        _, type_, name = key.split("/")
        result[type_][name] = value
    return result


def get_configuration_file_path(type_: str, name: str) -> Path:
    """Get the configuration file path."""
    fp = os.path.join("packages", "fetchai", type_, name, TYPE_TO_CONFIG_FILE[type_])
    if os.path.isfile(fp):
        return Path(fp)
    fp = os.path.join("aea", type_, name, TYPE_TO_CONFIG_FILE[type_])
    if os.path.isfile(fp):
        return Path(fp)
    print("Cannot find folder for package `{}` of type `{}`".format(name, type_))
    sys.exit(1)


def get_public_id_from_yaml(configuration_file_path: Path) -> PublicId:
    """
    Get the public id from yaml.

    :param configuration_file: the path to the config yaml
    """
    data = yaml.safe_load(configuration_file_path.open())
    author = data["author"]
    # handle the case when it's a package or agent config file.
    name = data["name"] if "name" in data else data["agent_name"]
    version = data["version"]
    return PublicId(author, name, version)


def public_id_in_registry(type_: str, name: str) -> PublicId:
    """
    Check if a package id is in the registry.

    :param type_: the package type
    :param name: the name of the package
    :return: public id
    """
    runner = CliRunner()
    result = runner.invoke(
        cli, [*CLI_LOG_OPTION, "search", type_, "--query", name], standalone_mode=False,
    )
    reg = r"({}/{}:{})".format("fetchai", name, PublicId.VERSION_REGEX)
    ids = re.findall(reg, result.output,)
    p_ids = []
    highest = PublicId.from_str("fetchai/{}:0.1.0".format(name))
    for id_ in ids:
        p_id = PublicId.from_str(id_[0])
        p_ids.append(p_id)
        if p_id > highest:
            highest = p_id
    return highest


def process_packages(
    last_by_type: Dict[str, Dict[str, str]], now_by_type: Dict[str, Dict[str, str]]
) -> bool:
    """Process the package versions."""
    is_bumped = False
    for type_ in TYPES:
        for key, value in last_by_type[type_].items():
            if key == "scaffold":
                print("Package `{}` of type `{}` is never bumped!".format(key, type_))
                continue
            if key not in now_by_type[type_]:
                print("Package `{}` of type `{}` no longer present!".format(key, type_))
                continue
            if now_by_type[type_][key] == value:
                print(
                    "Package `{}` of type `{}` has not changed since last release!".format(
                        key, type_
                    )
                )
            else:
                is_bumped = process_package(type_, key)
            if is_bumped:
                break
        else:
            continue
        break
    return is_bumped


def minor_version_difference(
    current_public_id: PublicId, deployed_public_id: PublicId
) -> int:
    """Check the minor version difference."""
    diff = semver.compare(current_public_id.version, deployed_public_id.version)
    return diff


def bump_package_version(
    current_public_id: PublicId, configuration_file_path: Path, type_: str
) -> None:
    """
    Bump the version references of the package in the repo.

    Includes, bumping the package itself.
    """
    ver = semver.VersionInfo.parse(current_public_id.version)
    new_version = str(ver.bump_minor())
    new_public_id = PublicId(
        current_public_id.author, current_public_id.name, new_version
    )
    for rootdir in DIRECTORIES:
        for path in Path(rootdir).glob("**/*"):
            if path.is_file() and str(path).endswith((".py", ".yaml", ".md")):
                inplace_change(path, str(current_public_id), str(new_public_id), type_)

    bump_version_in_yaml(configuration_file_path, type_, new_public_id.version)


def _ask_to_user_and_replace_if_allowed(content, old_string, new_string, type_) -> str:
    """
    Ask to user if the line should be replaced or not, If the script arguments allow that.

    :param content: the content.
    :param old_string: the old string.
    :param new_string: the new string.
    :param type_: the type of the package.
    :return: the updated content.
    """
    if arguments.no_interactive and arguments.replace_by_default:
        content = content.replace(old_string, new_string)
        return content

    lines = content.splitlines()
    for idx, line in enumerate(lines[:]):
        if old_string not in line:
            continue
        above_rows = lines[idx - arguments.context : idx]
        below_rows = lines[idx + 1 : idx + arguments.context]
        print("\n".join(above_rows))
        print(line.replace(old_string, "\033[91m" + old_string + "\033[0m"))
        print("\n".join(below_rows))
        answer = input(  # nosec
            f"Replace for component ({type_}, {old_string})? [y/N]: ",
        )
        if answer == "y":
            lines[idx] = line.replace(old_string, new_string)
    return "\n".join(lines)


def replace_aea_fetch_statements(content, old_string, new_string, type_) -> str:
    """Replace statements of the type: 'aea fetch <old_string>'."""
    if type_ == "agent":
        content = re.sub(
            fr"aea +fetch +{old_string}", f"aea fetch {new_string}", content
        )
    return content


def replace_type_and_public_id_occurrences(
    content, old_string, new_string, type_
) -> str:
    """Replace the public id whenever the type and the id occur in the same row."""
    lines = content.splitlines(keepends=False)
    for idx, line in enumerate(lines[:]):
        if old_string not in line:
            continue
        if re.match(f"{type_}.*{old_string}", line):
            lines[idx] = line.replace(old_string, new_string)
    return "\n".join(lines)


def replace_in_yamls(content, old_string, new_string, type_) -> str:
    """
    Replace the public id in configuration files (also nested in .md files).

    1) replace in cases like:
        |protocols:
        |- author/name:version
        |...
        |- old_string
    2) replace in cases like:
        |name: package_name
        |author: package_author
        |version: package_version -> bump up
        |type: package_type
    """

    # case 1:
    regex = re.compile(f"({type_}:\n(-.*\n)*)(- *{old_string})", re.MULTILINE)
    content = regex.sub(rf"\g<1>- {new_string}", content)

    # case 1:
    old_public_id = PublicId.from_str(old_string)
    new_public_id = PublicId.from_str(new_string)
    regex = re.compile(
        rf"(name: {old_public_id.name}\nauthor: {old_public_id.author}\n)version: {old_public_id.version}\n(type: {type_[:-1]})",
        re.MULTILINE,
    )
    content = regex.sub(rf"\g<1>version: {new_public_id.version}\n\g<2>", content)
    return content


def inplace_change(fp: Path, old_string: str, new_string: str, type_: str) -> None:
    """Replace the occurrence of a string with a new one in the provided file."""

    content = fp.read_text()
    if old_string not in content:
        return

    content = replace_aea_fetch_statements(content, old_string, new_string, type_)
    content = replace_type_and_public_id_occurrences(
        content, old_string, new_string, type_
    )
    content = replace_in_yamls(content, old_string, new_string, type_)
    content = _ask_to_user_and_replace_if_allowed(
        content, old_string, new_string, type_
    )

    with fp.open(mode="w") as f:
        f.write(content)


def bump_version_in_yaml(
    configuration_file_path: Path, type_: str, version: str
) -> None:
    """Bump the package version in the package yaml."""
    loader = ConfigLoader.from_configuration_type(type_[:-1])
    config = loader.load(configuration_file_path.open())
    config.version = version
    loader.dump(config, open(configuration_file_path, "w"))


def process_package(type_: str, name: str) -> bool:
    """
    Process a package.

    - check version in registry
    - make sure, version is exactly one above the one in registry
    - change all occurences in packages/tests/aea/examples/benchmark/docs to new reference
    - change yaml version number

    :return: whether a package was bumped or not
    """
    configuration_file_path = get_configuration_file_path(type_, name)
    current_public_id = get_public_id_from_yaml(configuration_file_path)
    deployed_public_id = public_id_in_registry(type_, name)
    difference = minor_version_difference(current_public_id, deployed_public_id)
    is_bumped = False
    if difference == 0:
        print("Bumping package `{}` of type `{}`!".format(name, type_))
        bump_package_version(current_public_id, configuration_file_path, type_)
        is_bumped = True
    elif difference == 1:
        print(
            "Package `{}` of type `{}` already at correct version!".format(name, type_)
        )
    else:
        print(
            "Package `{}` of type `{}` has current id `{}` and deployed id `{}`. Error!".format(
                name, type_, current_public_id, deployed_public_id
            )
        )
        sys.exit(1)
    return is_bumped


def run_once() -> bool:
    """Run the upgrade logic once."""
    last = get_hashes_from_last_release()
    now = get_hashes_from_current_release()
    last_by_type = split_hashes_by_type(last)
    now_by_type = split_hashes_by_type(now)
    is_bumped = process_packages(last_by_type, now_by_type)
    return is_bumped


if __name__ == "__main__":
    """
    First, check all hashes are up to date, exit if not.
    Then, run the bumping algo, re-hashing upon each bump.
    """
    arguments = parser.parse_args()
    run_hashing()
    check_if_running_allowed()
    while run_once():
        run_hashing()
    sys.exit(0)
