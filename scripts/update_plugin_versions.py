#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
Bump the versions of AEA plugins throughout the code base.

    python scripts/update_plugin_versions.py --update "plugin-name,version" [--update ...]

Example of usage:

    python scripts/update_plugin_versions.py --update "open-aea-ledger-fetchai,0.2.0" --update "open-aea-ledger-ethereum,0.3.0"

"""

import argparse
import pprint
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from aea.cli.ipfs_hash import update_hashes
from aea.helpers.base import compute_specifier_from_version


ROOT_DIR = Path(__file__).parent.parent
PLUGINS_DIR = Path("plugins")
SETUP_PY_NAME_REGEX = re.compile(r"\Wname=\"(.*)\",")
SETUP_PY_VERSION_REGEX = re.compile(r"\Wversion=\"(.*)\",")


IGNORE_DIRS = [Path(".git")]


def update_plugin_setup(
    plugin_name: str, old_version: Version, new_version: Version
) -> bool:
    """Update plugin setup.py script with new version.

    :param plugin_name: the plugin name.
    :param old_version: the old version.
    :param new_version: the new version.
    :return: True if an update has been done, False otherwise.
    """
    setup_file = PLUGINS_DIR / plugin_name.strip("open-") / "setup.py"
    content = setup_file.read_text()
    new_content = re.sub(
        rf"version=['\"]{old_version}['\"],", f'version="{new_version}",', content
    )
    setup_file.write_text(new_content)
    return content != new_content


def process_plugin(
    plugin_name: str, old_version: Version, new_version: Version
) -> bool:
    """
    Process the plugin version.

    :param plugin_name: the plugin name.
    :param old_version: the old version.
    :param new_version: the new version.
    :return: True if an update has been done, False otherwise.
    """
    result = False
    result = update_plugin_setup(plugin_name, old_version, new_version) or result
    result = (
        update_plugin_version_specifiers(plugin_name, old_version, new_version)
        or result
    )
    return result


def update_plugin_version_specifiers(
    plugin_name: str, old_version: Version, new_version: Version
) -> bool:
    """
    Update aea_version specifier set in docs.

    :param plugin_name: the plugin name.
    :param old_version: the old version.
    :param new_version: the new version.
    :return: True if the update has been done, False otherwise.
    """
    old_specifier_set = compute_specifier_from_version(old_version)
    new_specifier_set = compute_specifier_from_version(new_version)
    print(f"Old version specifier: {old_specifier_set}")
    print(f"New version specifier: {new_specifier_set}")
    if old_specifier_set == new_specifier_set:
        print("Not updating version specifier - they haven't changed.")
        return False
    has_changed = False
    new_specifier_set = str(SpecifierSet(new_specifier_set))
    old_specifier_set = str(SpecifierSet(old_specifier_set))
    old_specifier_set_regex = re.compile(str(old_specifier_set).replace(" ", " *"))
    for file in filter(lambda p: not p.is_dir(), Path(".").rglob("*")):
        dir_root = Path(file.parts[0])
        if dir_root in IGNORE_DIRS:
            print(f"Skipping '{file}'...")
            continue
        print(
            f"Replacing '{old_specifier_set}' with '{new_specifier_set}' in '{file}'... ",
            end="",
        )
        try:
            content = file.read_text()
        except UnicodeDecodeError as e:
            print(f"Cannot read {file}: {str(e)}. Continue...")
        else:
            if old_specifier_set_regex.search(content) is None:
                print("No version to update found.")
                continue
            new_content = _replace_patterns(
                content, plugin_name, old_specifier_set, new_specifier_set
            )
            has_changed = has_changed or content != new_content
            file.write_text(new_content)
            print("Done!")
    return has_changed


def _replace_patterns(
    content: str, plugin_name: str, old_specifier: str, new_specifier: str
) -> str:
    """
    Replace specific patterns.

    It identifies three patterns:

    1) strings of the form:
    <plugin-name><old_specifier_set>
    2) YAML strings of the form:
    plugin-name:
      version: <old_specifier_set>
    3) strings of the form
    "<plugin-name>": {"version": "<old_specifier_set>"}

    :param content: the file content
    :param plugin_name: the plugin name
    :param old_specifier: the old specifier
    :param new_specifier: the new specifier
    :return: the new content.
    """
    # check pattern (1)
    content = re.sub(
        f"{plugin_name}{old_specifier}", f"{plugin_name}{new_specifier}", content
    )
    # check pattern (2)
    content = re.sub(
        f"({plugin_name}:\n *version: ){old_specifier}",
        rf"\g<1>{new_specifier}",
        content,
    )
    # check pattern (3)
    content = re.sub(
        f'"{plugin_name}": {{"version": "{old_specifier}"}}',
        f'"{plugin_name}": {{"version": "{new_specifier}"}}',
        content,
    )
    return content


def exit_with_message(message: str, exit_code: int = 1) -> None:
    """Exit the program with a message and an exit code."""
    print(message)
    sys.exit(exit_code)


def get_plugin_names_and_versions() -> Dict[str, Version]:
    """Get all the plugins names and versions."""
    result: Dict[str, Version] = {}
    for plugin_setup_script in PLUGINS_DIR.glob("*/setup.py"):
        content = plugin_setup_script.read_text()
        name_matches: List[str] = SETUP_PY_NAME_REGEX.findall(content)
        version_matches: List[str] = SETUP_PY_VERSION_REGEX.findall(content)
        if len(name_matches) != 1 or len(version_matches) != 1:
            exit_with_message(
                f"Unexpected result: in {result}, found plugin names: {name_matches} and versions: {version_matches}"
            )
        name, version = name_matches[0], version_matches[0]
        if name in result:
            print(f"Warning, duplicate plugin name: '{name}'.")
        result[name] = Version(version)
    return result


def name_version_pair(s: str) -> Tuple[str, str]:
    """
    Parse a name-version pair.

    :param s: the parameter string.
    :return: a pair of string (name, new_version)
    """
    try:
        name, version = [part.strip() for part in s.split(",")]
        return name, version
    except Exception:
        raise argparse.ArgumentTypeError(f"Name-version pair not correct: '{s}'")


def parse_args() -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser("bump_aea_version")
    parser.add_argument(
        "--update",
        type=name_version_pair,
        metavar="'NAME,VERSION'",
        required=True,
        action="append",
        help="A comma-separated pair: 'plugin-name, new-version'.",
    )
    parser.add_argument("--no-fingerprint", action="store_true")
    arguments_ = parser.parse_args()
    return arguments_


def main() -> None:
    """Run the script."""
    arguments = parse_args()
    current_versions_by_name: Dict[str, Version] = get_plugin_names_and_versions()
    new_versions_by_name: Dict[str, Version] = dict(
        (name, Version(version)) for name, version in arguments.update
    )

    print(
        f"Found plugin names and versions:\n{pprint.pformat(current_versions_by_name)}"
    )
    print(f"Plugins to update:\n{pprint.pformat(new_versions_by_name)}")

    not_found_plugins = set(new_versions_by_name.keys()).difference(
        current_versions_by_name.keys()
    )
    if len(not_found_plugins) > 0:
        exit_with_message(
            f"Error: These plugins have not been found:\n{pprint.pformat(not_found_plugins)}"
        )

    have_updated_specifier_set = False

    for current_plugin_name, new_version in new_versions_by_name.items():
        old_version = current_versions_by_name[current_plugin_name]
        print(
            f"Processing {current_plugin_name}, old_version={old_version}, new_version={new_version}"
        )
        if new_version == old_version:
            print("Skipping, as old and new versions are equal.")
            continue

        have_updated_specifier_set = (
            process_plugin(current_plugin_name, old_version, new_version)
            or have_updated_specifier_set
        )

    return_code = 0
    if arguments.no_fingerprint:
        print("Not updating fingerprints, since --no-fingerprint was specified.")
    elif not have_updated_specifier_set:
        print("Not updating fingerprints, since no specifier set has been updated.")
    else:
        print("Updating hashes and fingerprints.")
        return_code = update_hashes(
            packages_dir=ROOT_DIR / "packages",
        )
    exit_with_message("Done!", exit_code=return_code)


if __name__ == "__main__":
    main()
