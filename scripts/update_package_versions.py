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
import operator
import os
import re
import shutil
import subprocess  # nosec
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set

import semver
import yaml
from click.testing import CliRunner

from aea.cli import cli
from aea.configurations.base import PackageId, PackageType, PublicId
from aea.configurations.loader import ConfigLoader
from scripts.common import (
    PACKAGES_DIR,
    get_protocol_specification_from_readme,
    get_protocol_specification_id_from_specification,
)
from scripts.generate_ipfs_hashes import update_hashes


DIRECTORIES = ["packages", "aea", "docs", "benchmark", "examples", "tests"]
CLI_LOG_OPTION = ["-v", "OFF"]
TYPES = set(map(lambda x: x.to_plural(), PackageType))
HASHES_CSV = "hashes.csv"
TYPE_TO_CONFIG_FILE = {
    "connections": "connection.yaml",
    "protocols": "protocol.yaml",
    "contracts": "contract.yaml",
    "skills": "skill.yaml",
    "agents": "aea-config.yaml",
}
PUBLIC_ID_REGEX = PublicId.PUBLIC_ID_REGEX[1:-1]
TEST_PROTOCOLS = ["t_protocol", "t_protocol_no_ct"]


def get_protocol_specification_header_regex(public_id: PublicId) -> Pattern:
    """Get the regex to match."""
    return re.compile(
        rf"(name: {public_id.name}\n"
        + rf"author: {public_id.author}\n)"
        + rf"version: {public_id.version}\n"
        + r"(description:)",
        re.MULTILINE,
    )


def check_positive(value: Any) -> int:
    """Check value is an int."""
    try:
        ivalue = int(value)
        assert ivalue <= 0
    except (AssertionError, ValueError):
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return ivalue


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
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
    return parser.parse_args()


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


def unified_yaml_load(configuration_file: Path) -> Dict:
    """
    Load YAML file, unified (both single- and multi-paged).

    :param configuration_file: the configuration file path.
    :return: the data.
    """
    package_type = configuration_file.parent.parent.name
    with configuration_file.open() as fp:
        if package_type != "agents":
            return yaml.safe_load(fp)
        # when it is an agent configuration file,
        # we are interested only in the first page of the YAML,
        # because the dependencies are contained only there.
        data = yaml.safe_load_all(fp)
        return list(data)[0]


def get_public_id_from_yaml(configuration_file_path: Path) -> PublicId:
    """
    Get the public id from yaml.

    :param configuration_file_path: the path to the config yaml
    :return: public id
    """
    data = unified_yaml_load(configuration_file_path)
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


def get_all_protocol_spec_ids() -> Set[PublicId]:
    """
    Get all protocol specification ids.

    We return package ids with type "protocol" even though
    they are not exactly protocol. The reason is that
    they are only used to find clashes with protocol ids.

    :return: a set of package ids.
    """
    result: Set[PublicId] = set()
    protocol_packages = set(PACKAGES_DIR.rglob("**/**/protocols/**")) - set(
        PACKAGES_DIR.rglob("**/**/protocols")
    )
    for protocol_package_path in protocol_packages:
        if "connections" in str(protocol_package_path):
            continue
        content = get_protocol_specification_from_readme(protocol_package_path)
        spec_id = get_protocol_specification_id_from_specification(content)
        result.add(PublicId.from_str(spec_id))
    return result


def get_all_package_ids() -> Set[PackageId]:
    """Get all the package ids in the local repository."""
    result: Set[PackageId] = set()
    now = get_hashes_from_current_release()
    now_by_type = split_hashes_by_type(now)
    for type_, name_to_hashes in now_by_type.items():
        for name, _ in name_to_hashes.items():
            if name in TEST_PROTOCOLS:
                continue
            configuration_file_path = get_configuration_file_path(type_, name)
            public_id = get_public_id_from_yaml(configuration_file_path)
            package_id = PackageId(PackageType(type_[:-1]), public_id)
            result.add(package_id)
    return result


def get_public_ids_to_update() -> Set[PackageId]:
    """
    Get all the public ids to be updated.

    In particular, a package DOES NOT NEED a version bump if:
    - the package is a "scaffold" package;
    - the package is no longer present
    - the package hasn't change since the last release;
    - the public ids of the local package and the package in the registry
      are already the same.

    :return: set of package ids to update
    """
    result: Set[PackageId] = set()
    last = get_hashes_from_last_release()
    now = get_hashes_from_current_release()
    last_by_type = split_hashes_by_type(last)
    now_by_type = split_hashes_by_type(now)
    for type_ in TYPES:
        for key, value in last_by_type[type_].items():
            # if the package is a "scaffold" package, skip;
            if key == "scaffold":
                print("Package `{}` of type `{}` is never bumped!".format(key, type_))
                continue
            # if the package is no longer present, skip;
            if key not in now_by_type[type_]:
                print("Package `{}` of type `{}` no longer present!".format(key, type_))
                continue
            # if the package hasn't change since the last release, skip;
            if now_by_type[type_][key] == value:
                print(
                    "Package `{}` of type `{}` has not changed since last release!".format(
                        key, type_
                    )
                )
                continue
            # load public id in the registry if any
            name = key
            configuration_file_path = get_configuration_file_path(type_, name)
            current_public_id = get_public_id_from_yaml(configuration_file_path)
            deployed_public_id = public_id_in_registry(type_, name)
            difference = minor_version_difference(current_public_id, deployed_public_id)
            # check if the public ids of the local package and the package in the registry are already the same.
            package_info = f"Package `{name}` of type `{type_}`"
            public_id_info = f"current id `{current_public_id}` and deployed id `{deployed_public_id}`"
            if difference == 0:
                print(f"{package_info} needs to be bumped!")
                result.add(PackageId(type_[:-1], current_public_id))
            elif difference == 1:
                print(f"{package_info} already at correct version!")
                continue
            else:
                print(f"{package_info} has {public_id_info}. Error!")
                sys.exit(1)
    return result


def _get_ambiguous_public_ids() -> Set[PublicId]:
    """Get the public ids that are the public ids of more than one package id."""
    all_package_ids = get_all_package_ids()
    result: Set[PublicId] = set(
        map(
            operator.itemgetter(0),
            filter(
                lambda x: x[0].name != "scaffold" and x[1] > 1,
                Counter(id_.public_id for id_ in all_package_ids).items(),
            ),
        )
    )
    return result


def _sort_in_update_order(package_ids: Set[PackageId]) -> List[PackageId]:
    """
    Sort the set of package id in the order of update.

    In particular, they are sorted from the greatest version number to the lowest.

    The reason is to avoid that consecutive package ids (i.e. whose minors difference is 1)
    gets updated in ascending order, resulting in all the updates collapsing to the greatest version.
    For example, consider two package ids with prefix 'author/package' and with versions
    0.1.0 and 0.2.0, respectively. If we bump first the former and then the latter,
    the new replacements associated to the first updated are taken into account in
    the second update.

    :param package_ids: set of package ids
    :return: sorted list of package ids
    """
    return sorted(
        package_ids,
        key=lambda x: (
            semver.VersionInfo.parse(x.public_id.version),
            x.public_id.author,
            x.public_id.name,
            x.package_type.value,
        ),
        reverse=True,
    )


def process_packages(
    all_package_ids_to_update: Set[PackageId], ambiguous_public_ids: Set[PublicId]
) -> None:
    """Process the package versions."""
    print("*" * 100)

    conflicts = {p.public_id for p in all_package_ids_to_update}.intersection(
        ambiguous_public_ids
    )
    print(f"Ambiguous public ids: {ambiguous_public_ids}")
    print(f"Conflicts with public ids to update: {conflicts}",)

    print("*" * 100)
    print("Start processing.")
    # we need to include this in case some protocol id == spec id of that protocol.
    spec_protocol_ids = get_all_protocol_spec_ids()
    sorted_package_ids_list = _sort_in_update_order(all_package_ids_to_update)
    for package_id in sorted_package_ids_list:
        print("#" * 50)
        print(f"Processing {package_id}")
        is_ambiguous = package_id.public_id in ambiguous_public_ids.union(
            spec_protocol_ids
        )
        process_package(package_id, is_ambiguous)


def minor_version_difference(
    current_public_id: PublicId, deployed_public_id: PublicId
) -> int:
    """Check the minor version difference."""
    diff = semver.compare(current_public_id.version, deployed_public_id.version)
    return diff


def bump_package_version(
    current_public_id: PublicId,
    configuration_file_path: Path,
    type_: str,
    is_ambiguous: bool = False,
) -> None:
    """
    Bump the version references of the package in the repo.

    Includes, bumping the package itself.

    :param current_public_id: the current public id
    :param configuration_file_path: the path to the configuration file
    :param type_: the type of package
    :param is_ambiguous: whether or not the package id is ambiguous
    """
    ver = semver.VersionInfo.parse(current_public_id.version)
    new_version = str(ver.bump_minor())
    new_public_id = PublicId(
        current_public_id.author, current_public_id.name, new_version
    )
    for rootdir in DIRECTORIES:
        for path in Path(rootdir).glob("**/*"):
            if path.is_file() and str(path).endswith((".py", ".yaml", ".md")):
                inplace_change(
                    path, current_public_id, new_public_id, type_, is_ambiguous,
                )

    bump_version_in_yaml(configuration_file_path, type_, new_public_id.version)


def _can_disambiguate_from_context(
    line: str, old_string: str, type_: str
) -> Optional[bool]:
    """
    Check whether we can disambiguate the public id given contextual information.

    For example:
    - whether the public id appears in a line of the form 'aea fetch ...' (we know it's an agent)
    - whether the public id appears in a line of the form 'aea add ...' (we know the component type)
    - whether the type appears in the same line where the public id occurs.

    :param line: the line
    :param old_string: the old string
    :param type_: the type of package
    :return: if True/False, the old string can/cannot be replaced. If None, we don't know.
    """
    match = re.search(
        fr"aea +add +(skill|protocol|connection|contract) +{old_string}", line
    )
    if match is not None:
        return match.group(1) == type_[:-1]
    if re.search(fr"aea +fetch +{old_string}", line) is not None:
        return type_ == "agents"
    match = re.search(
        "(skill|SKILL|"
        + "protocol|PROTOCOL|"
        + "connection|CONNECTION|"
        + "contract|CONTRACT|"
        + "agent|AGENT"
        + f")s?.*{old_string}",
        line,
    )
    if match is not None:
        return (match.group(1) + "s") == type_

    # for protocol specification id only:
    # - if the line contains 'protocol_specification_id: {old_public_id}' or
    # - if the line contains 'protocol_specification_id = PublicId.from_str("{old_public_id}")'
    # then DON'T replace it (we only bump protocol ids here).
    # otherwise, we don't know -> return None and ask to user.
    case_1 = f"protocol_specification_id: {old_string}"
    case_2 = rf'protocol_specification_id = PublicId.from_str([\'"]{old_string}[\'"])'
    if re.search(case_1, line) or re.search(case_2, line):
        return True
    return None


def _ask_to_user(
    lines: List[str], line: str, idx: int, old_string: str, type_: str
) -> str:
    print("=" * 50)
    above_rows = lines[idx - arguments.context : idx]
    below_rows = lines[idx + 1 : idx + arguments.context]
    print("".join(above_rows))
    print(line.rstrip().replace(old_string, "\033[91m" + old_string + "\033[0m"))
    print("".join(below_rows))
    answer = input(f"Replace for component ({type_}, {old_string})? [y/N]: ",)  # nosec
    return answer


def _ask_to_user_and_replace_if_allowed(
    content: str, old_string: str, new_string: str, type_: str
) -> str:
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

    lines = content.splitlines(keepends=True)
    for idx, line in enumerate(lines[:]):
        if old_string not in line:
            continue

        can_replace = _can_disambiguate_from_context(line, old_string, type_)
        # if we managed to replace all the occurrences, then save this line and continue
        if can_replace is not None:
            lines[idx] = line.replace(old_string, new_string) if can_replace else line
            continue

        # otherwise, forget the attempts and ask to the user.
        answer = _ask_to_user(lines, line, idx, old_string, type_)
        if answer == "y":
            lines[idx] = line.replace(old_string, new_string)
    return "".join(lines)


def replace_aea_fetch_statements(
    content: str, old_string: str, new_string: str, type_: str
) -> str:
    """Replace statements of the type: 'aea fetch <old_string>'."""
    if type_ == "agents":
        content = re.sub(
            fr"aea +fetch +{old_string}", f"aea fetch {new_string}", content
        )
    return content


def replace_aea_add_statements(
    content: str, old_string: str, new_string: str, type_: str
) -> str:
    """Replace statements of the type: 'aea add <type> <old_string>'."""
    if type_ != "agents":
        content = re.sub(
            fr"aea +add +{type_} +{old_string}",
            f"aea add {type_} {new_string}",
            content,
        )
    return content


def replace_type_and_public_id_occurrences(
    line: str, old_string: str, new_string: str, type_: str
) -> str:
    """Replace the public id whenever the type and the id occur in the same row, and NOT when other type names occur."""
    if re.match(f"{type_}.*{old_string}", line) and all(
        _type not in line for _type in TYPES.difference({type_})
    ):
        line = line.replace(old_string, new_string)
    return line


def replace_in_yamls(
    content: str, old_public_id: PublicId, new_public_id: PublicId, type_: str
) -> str:
    """
    Replace the public id in configuration files (also nested in .md files).

    1) replace package dependencies:
        |protocols:
        |- author/name:version
        |...
        |- old_string
    2) replace in configuration headers:
        |name: package_name
        |author: package_author
        |version: package_version -> bump up
        |type: package_type

    :param content: the content
    :param old_public_id: the old public id
    :param new_public_id: the new public id
    :param type_: the type of the package
    :return: replaced content
    """
    # case 1:
    regex = re.compile(f"({type_}:\n(-.*\n)*)(- *{str(old_public_id)})", re.MULTILINE)
    content = regex.sub(rf"\g<1>- {str(new_public_id)}", content)

    # case 2:
    regex = re.compile(
        rf"(name: {old_public_id.name}\nauthor: {old_public_id.author}\n)version: {old_public_id.version}\n(type: {type_[:-1]})",
        re.MULTILINE,
    )
    content = regex.sub(rf"\g<1>version: {new_public_id.version}\n\g<2>", content)
    return content


def replace_in_protocol_readme(
    fp: Path, content: str, old_public_id: PublicId, new_public_id: PublicId, type_: str
) -> str:
    """
    Replace the version id in the protocol specification in the protcol's README.

    That is, bump the version in cases like:

        |name: package_name
        |author: package_author
        |version: package_version -> bump up
        ...

    :param fp: path to the file being edited.
    :param content: the content of the file.
    :param old_public_id: the old public id.
    :param new_public_id: the new public id.
    :param type_: the type of the package.
    :return: the new content.
    """
    if (
        type_ == fp.parent.parent.name == "protocols"
        and fp.name == "README.md"
        and fp.parent.name == old_public_id.name
    ):
        regex = get_protocol_specification_header_regex(old_public_id)
        content = regex.sub(rf"\g<1>version: {new_public_id.version}\n\g<2>", content)
    return content


def file_should_be_processed(content: str, old_public_id: PublicId) -> bool:
    """Check if the file should be processed."""
    old_string = str(old_public_id)
    return (
        old_string in content
        or get_protocol_specification_header_regex(old_public_id).search(content)
        is not None
    )


def inplace_change(
    fp: Path,
    old_public_id: PublicId,
    new_public_id: PublicId,
    type_: str,
    is_ambiguous: bool,
) -> None:
    """Replace the occurrence of a string with a new one in the provided file."""

    content = fp.read_text()
    if not file_should_be_processed(content, old_public_id):
        return

    old_string = str(old_public_id)
    new_string = str(new_public_id)
    print(
        f"Processing file {fp} for replacing {old_string} with {new_string} (is_ambiguous: {is_ambiguous})"
    )

    content = replace_in_yamls(content, old_public_id, new_public_id, type_)
    content = replace_in_protocol_readme(
        fp, content, old_public_id, new_public_id, type_
    )
    if not is_ambiguous:
        content = content.replace(old_string, new_string)
    else:
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


def process_package(package_id: PackageId, is_ambiguous: bool) -> None:
    """
    Process a package.

    - check version in registry
    - make sure, version is exactly one above the one in registry
    - change all occurrences in packages/tests/aea/examples/benchmark/docs to new reference
    - change yaml version number

    :param package_id: the id of the package
    :param is_ambiguous: whether the public id is ambiguous.
    """
    type_plural = package_id.package_type.to_plural()
    configuration_file_path = get_configuration_file_path(type_plural, package_id.name)
    current_public_id = get_public_id_from_yaml(configuration_file_path)
    bump_package_version(
        current_public_id, configuration_file_path, type_plural, is_ambiguous
    )


def run_once() -> bool:
    """Run the upgrade logic once."""
    all_package_ids_to_update = get_public_ids_to_update()
    if len(all_package_ids_to_update) == 0:
        print("No packages to update. Done!")
        return False
    ambiguous_public_ids = _get_ambiguous_public_ids()
    process_packages(all_package_ids_to_update, ambiguous_public_ids)
    return True


def check_if_svn_installed() -> None:
    """Check if svn is installed."""
    res = shutil.which("svn")
    if res is None:
        print("Install svn first!")
        sys.exit(1)


if __name__ == "__main__":
    """
    First, check all hashes are up to date, exit if not.
    Then, run the bumping algo, re-hashing upon each bump.
    """
    arguments = parse_arguments()
    check_if_svn_installed()
    run_hashing()
    check_if_running_allowed()
    while run_once():
        run_hashing()
    sys.exit(0)
