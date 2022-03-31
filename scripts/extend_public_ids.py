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

import json
from pathlib import Path
from typing import Dict, List, Set

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
from aea.configurations.data_types import ExtendedPublicId, PublicId
from aea.helpers.ipfs.base import IPFSHashOnly
import yaml
from aea.helpers.yaml_utils import _AEAYamlDumper, _AEAYamlLoader

PACKAGES_PATH = Path(__file__).parent.parent / "packages"
COMPONENTS = [
    (AGENT, DEFAULT_AEA_CONFIG_FILE),
    (SKILL, DEFAULT_SKILL_CONFIG_FILE),
    (CONTRACT, DEFAULT_CONTRACT_CONFIG_FILE),
    (CONNECTION, DEFAULT_CONNECTION_CONFIG_FILE),
    (PROTOCOL, DEFAULT_PROTOCOL_CONFIG_FILE),
]

COMPONENT_TO_FILE = dict(COMPONENTS)


def to_plural(string: str) -> str:
    """Convert component to plural"""
    return string + "s"


def reduce_set(list_of_sets: List[Set]) -> Set:
    """Reduce a list of sets to one dimentional set."""
    reduced = set()
    for s in list_of_sets:
        reduced = reduced.union(s)

    return reduced


def to_public_id(public_id: str) -> str:
    """Convert to public id."""
    try:
        return str(PublicId.from_str(public_id))
    except ValueError:
        return str(PublicId.from_json(ExtendedPublicId.from_str(public_id).json))


def normalize_package(public_id: str, separator: str = "-") -> str:
    """Convert to public id."""

    component_type, component_id = public_id.split(separator)
    component_id = to_public_id(component_id)
    return component_type + separator + component_id


def generate_dependency_tree(packages_dir: Path) -> List[List[str]]:
    """Returns PublicId to hash mapping."""

    package_to_dependency_mappings = {}

    for component_type, component_file in COMPONENTS:
        for file_path in packages_dir.glob(f"**/{component_file}"):
            with open(file_path, "r", encoding="utf-8") as fp:
                item_config, *_ = list(yaml.load_all(fp, Loader=yaml.CLoader))

            item_config["name"] = item_config.get("name", item_config.get("agent_name"))
            public_id = PublicId.from_json(item_config)

            package_to_dependency_mappings[
                f"{component_type}-{public_id}"
            ] = reduce_set(
                [
                    {
                        normalize_package(f"{c}-{dep}")
                        for dep in item_config.get(to_plural(c), {})
                    }
                    for c, _ in COMPONENTS[1:]
                ]
            )

    def _resolve_tree(dependencies: Dict, tree: Dict):
        """Resolve dependency tree"""

        for dep in tree:
            packages = dependencies.get(dep)
            for package in packages:
                package = normalize_package(package)
                dep_packages = list(dependencies.get(package))
                if dep in dep_packages:
                    raise ValueError("Found circular dependency.")

                tree[dep][package] = {p: {} for p in dep_packages}
                _resolve_tree(dependencies, tree[dep][package])

    dep_tree = {package: {} for package in package_to_dependency_mappings}
    _resolve_tree(package_to_dependency_mappings, dep_tree)

    def _flatten_tree(dependency_tree: Dict, flat_tree: List[List[str]], level: int):
        """Flatten tree."""
        try:
            flat_tree[level]
        except:
            flat_tree.insert(level, [])

        for package, deps in dependency_tree.items():
            flat_tree[level].append(package)
            _flatten_tree(deps, flat_tree, level + 1)

    flat_tree_dirty = []
    _flatten_tree(dep_tree, flat_tree_dirty, 0)

    flat_tree = []
    _packages = []
    for tree_level in reversed(flat_tree_dirty[:-1]):
        flat_tree.append(
            sorted(set([package for package in tree_level if package not in _packages]))
        )
        _packages += tree_level

    return flat_tree


@click.command()
@click.option(
    "--packages-dir",
    "-pd",
    type=click.Path(exists=True, dir_okay=True),
    default=PACKAGES_PATH,
)
def main(packages_dir: Path) -> None:
    """Main function."""

    dependency_tree = generate_dependency_tree(packages_dir)
    public_id_to_hash_mappings = {}
    hash_tool = IPFSHashOnly()

    for tree_level in dependency_tree:
        for package in tree_level:
            component_type, public_id_str = package.split("-")
            public_id = PublicId.from_str(public_id_str)
            package_path = (
                packages_dir
                / public_id.author
                / to_plural(component_type)
                / public_id.name
            )

            config_file = package_path / COMPONENT_TO_FILE.get(component_type)

            with open(config_file, "r", encoding="utf-8",) as fp:
                item_config, *extra_config = list(
                    yaml.load_all(fp, Loader=_AEAYamlLoader)
                )

            for _component_type, _ in COMPONENTS[1:]:
                _components = to_plural(_component_type)
                if _components in item_config:
                    item_config[_components] = [
                        str(
                            ExtendedPublicId.from_str(
                                f"{to_public_id(str(_dependency))}:{public_id_to_hash_mappings.get(to_public_id(str(_dependency)))}"
                            )
                        )
                        for _dependency in item_config.get(_components)
                    ]

            with open(config_file, "w+", encoding="utf-8") as fp:
                yaml.dump_all([item_config, *extra_config], fp, Dumper=_AEAYamlDumper)

            package_hash = hash_tool.hash_directory(package_path)
            public_id_to_hash_mappings[str(public_id)] = package_hash


if __name__ == "__main__":
    main()
