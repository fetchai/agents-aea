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

"""Script to update PublicIds to ExtendedPublicIds for package dependencies."""

from pathlib import Path
from typing import Dict

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
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.cli.utils.config import load_item_config

PACKAGES_PATH = Path(__file__).parent.parent / "packages"
COMPONENTS = [
    (AGENT, DEFAULT_AEA_CONFIG_FILE),
    (SKILL, DEFAULT_SKILL_CONFIG_FILE),
    (CONTRACT, DEFAULT_CONTRACT_CONFIG_FILE),
    (CONNECTION, DEFAULT_CONNECTION_CONFIG_FILE),
    (PROTOCOL, DEFAULT_PROTOCOL_CONFIG_FILE),
]


def generate_public_id_to_hash_mappings(package_dir: Path) -> Dict[str, str]:
    """Returns PublicId to hash mapping."""

    hash_tool = IPFSHashOnly()
    public_id_to_hash = {}

    for component_type, component_file in COMPONENTS:
        for file_path in package_dir.glob(f"**/{component_file}"):
            component_path = file_path.parent
            component_hash = hash_tool.hash_directory(str(component_path))
            item_config = load_item_config(component_type, component_path)
            public_id_to_hash[str(item_config.public_id)] = component_hash

    return public_id_to_hash


@click.command()
@click.option(
    "--package-dir",
    "-pd",
    type=click.Path(exists=True, dir_okay=True),
    default=PACKAGES_PATH,
)
def main(package_dir: Path) -> None:
    """Main function."""

    public_id_to_hash = generate_public_id_to_hash_mappings(package_dir)

    package_dir = Path(package_dir)
    for component_type, config_file in COMPONENTS:
        for file_path in package_dir.glob(f"**/{config_file}"):
            ...


if __name__ == "__main__":
    main()
