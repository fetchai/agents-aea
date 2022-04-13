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

"""Script to update PublicIds to PublicIds for package dependencies."""

from pathlib import Path
from typing import Dict, cast

import click

from aea.configurations.constants import (
    AGENT,
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PROTOCOL,
    SKILL,
)
from aea.configurations.data_types import PublicId
from aea.helpers.dependency_tree import DependecyTree, dump_yaml, load_yaml, to_plural
from aea.helpers.ipfs.base import IPFSHashOnly


PACKAGES_PATH = Path(__file__).parent.parent / "packages"
COMPONENT_TO_FILE = {
    AGENT: DEFAULT_AEA_CONFIG_FILE,
    SKILL: DEFAULT_SKILL_CONFIG_FILE,
    CONTRACT: DEFAULT_CONTRACT_CONFIG_FILE,
    CONNECTION: DEFAULT_CONNECTION_CONFIG_FILE,
    PROTOCOL: DEFAULT_PROTOCOL_CONFIG_FILE,
}


def update_public_id_hash(
    public_id_str: str, public_id_to_hash_mappings: Dict[str, str]
) -> str:
    """Update hash for given public from available mappings."""
    public_id = PublicId.from_str(public_id_str).without_hash()
    return str(
        PublicId.from_json(
            {
                **public_id.json,
                "package_hash": cast(
                    str, public_id_to_hash_mappings.get(str(public_id))
                ),
            }
        )
    )


def extend_public_ids(
    item_config: Dict, public_id_to_hash_mappings: Dict[str, str]
) -> None:
    """Extend public id with hashes for given item config."""
    for component_type in COMPONENT_TO_FILE:
        if component_type == AGENT:
            continue

        components = to_plural(component_type)
        if components in item_config:
            item_config[components] = [
                update_public_id_hash(d, public_id_to_hash_mappings)
                for d in item_config.get(components, [])
            ]


@click.command()
@click.option(
    "--packages-dir",
    "-pd",
    type=click.Path(exists=True, dir_okay=True),
    default=PACKAGES_PATH,
)
def main(packages_dir: Path) -> None:
    """Main function."""

    hash_tool = IPFSHashOnly()

    public_id_to_hash_mappings: Dict = {}
    dependency_tree = DependecyTree.generate(packages_dir)

    for tree_level in dependency_tree:
        for package in tree_level:
            public_id = package.public_id
            package_path = (
                packages_dir
                / public_id.author
                / to_plural(package.package_type.value)
                / public_id.name
            )

            config_file = package_path / cast(
                str, COMPONENT_TO_FILE.get(package.package_type.value)
            )
            item_config, extra_config = load_yaml(config_file)

            extend_public_ids(item_config, public_id_to_hash_mappings)
            dump_yaml(config_file, item_config, extra_config)

            package_hash = hash_tool.hash_directory(str(package_path))
            public_id_to_hash_mappings[str(public_id)] = package_hash


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
