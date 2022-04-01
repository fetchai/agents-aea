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
"""This module contains the code to generate dependency trees from registries."""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

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
from aea.helpers.yaml_utils import _AEAYamlDumper, _AEAYamlLoader


COMPONENTS = [
    (AGENT, DEFAULT_AEA_CONFIG_FILE),
    (SKILL, DEFAULT_SKILL_CONFIG_FILE),
    (CONTRACT, DEFAULT_CONTRACT_CONFIG_FILE),
    (CONNECTION, DEFAULT_CONNECTION_CONFIG_FILE),
    (PROTOCOL, DEFAULT_PROTOCOL_CONFIG_FILE),
]


def load_yaml(file_path: Path) -> Tuple[Dict, List[Dict]]:
    """Load yaml file."""
    with open(file_path, "r", encoding="utf-8") as fp:
        item_config, *extra_data = list(yaml.load_all(fp, Loader=_AEAYamlLoader))
        return item_config, extra_data


def dump_yaml(
    file_path: Path, data: Dict, extra_data: Optional[List[Dict]] = None
) -> None:
    """Dump yaml file."""
    if extra_data is not None and len(extra_data) > 0:
        with open(file_path, "w+", encoding="utf-8") as fp:
            yaml.dump_all([data, *extra_data], fp, Dumper=_AEAYamlDumper)
    else:
        with open(file_path, "w+", encoding="utf-8") as fp:
            yaml.dump(data, fp, Dumper=_AEAYamlDumper)


def to_public_id(public_id: str) -> PublicId:
    """Convert to public id."""
    try:
        return PublicId.from_str(public_id)
    except ValueError:
        return PublicId.from_json(ExtendedPublicId.from_str(public_id).json)


def to_plural(string: str) -> str:
    """Convert component to plural"""
    return string + "s"


def reduce_sets(list_of_sets: List[Set]) -> Set[str]:
    """Reduce a list of sets to one dimentional set."""
    reduced: Set[str] = set()
    for s in list_of_sets:
        reduced = reduced.union(s)
    return reduced


def from_package_id(public_id: str, separator: str = "-") -> str:
    """Convert to public id."""

    component_type, component_id = public_id.split(separator)
    component_id = str(to_public_id(component_id))
    return component_type + separator + component_id


def to_package_id(public_id: str, package_type: str, separator: str = "-") -> str:
    """Convert to public id."""
    return package_type + separator + public_id


class DependecyTree:
    """This class represents the dependency tree for a registry."""

    @staticmethod
    def get_all_dependencies(item_config: Dict) -> List[str]:
        """Returns a list of all available dependencies."""
        return list(
            reduce_sets(
                [
                    {
                        from_package_id(to_package_id(dependency, component_type))
                        for dependency in item_config.get(
                            to_plural(component_type), set()
                        )
                    }
                    for component_type, _ in COMPONENTS[1:]
                ]
            )
        )

    @classmethod
    def resolve_tree(cls, dependencies: Dict[str, List[str]], tree: Dict) -> None:
        """Resolve dependency tree"""
        for root_package in tree:
            root_dependencies = dependencies.get(root_package, [])
            for package in root_dependencies:
                package = from_package_id(package)
                tree[root_package][package] = {
                    p: {} for p in list(dependencies.get(package, []))
                }
                cls.resolve_tree(dependencies, tree[root_package][package])

    @classmethod
    def flatten_tree(
        cls, dependency_tree: Dict, flat_tree: List[List[str]], level: int
    ) -> None:
        """Flatten tree."""
        try:
            flat_tree[level]
        except IndexError:
            flat_tree.insert(level, [])
        for package, dependencies in dependency_tree.items():
            flat_tree[level].append(package)
            cls.flatten_tree(dependencies, flat_tree, level + 1)

    @classmethod
    def generate(cls, packages_dir: Path) -> List[List[str]]:
        """Returns PublicId to hash mapping."""
        package_to_dependency_mappings = {}
        for component_type, component_file in COMPONENTS:
            for file_path in packages_dir.glob(f"**/{component_file}"):
                item_config, extra_data = load_yaml(file_path)
                item_config["name"] = item_config.get(
                    "name", item_config.get("agent_name")
                )
                public_id = PublicId.from_json(item_config)
                package_to_dependency_mappings[
                    to_package_id(str(public_id), component_type)
                ] = cls.get_all_dependencies(item_config)

        dep_tree: Dict[str, Dict] = {
            package: {} for package in package_to_dependency_mappings
        }
        flat_tree: List[List[str]] = []
        flat_tree_dirty: List[List[str]] = []
        dirty_packages: List[str] = []

        cls.resolve_tree(package_to_dependency_mappings, dep_tree)
        cls.flatten_tree(dep_tree, flat_tree_dirty, 0)

        for tree_level in reversed(flat_tree_dirty[:-1]):
            flat_tree.append(
                sorted(
                    set(
                        [
                            package
                            for package in tree_level
                            if package not in dirty_packages
                        ]
                    )
                )
            )
            dirty_packages += tree_level

        return flat_tree
