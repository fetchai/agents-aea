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
    DEFAULT_SERVICE_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PACKAGE_TYPE_TO_CONFIG_FILE,
    PROTOCOL,
    SERVICE,
    SKILL,
    VENDOR,
)
from aea.configurations.data_types import PackageId, PublicId
from aea.exceptions import AEAPackageLoadingError
from aea.helpers.yaml_utils import _AEAYamlDumper, _AEAYamlLoader


COMPONENTS = [
    (AGENT, DEFAULT_AEA_CONFIG_FILE),
    (SKILL, DEFAULT_SKILL_CONFIG_FILE),
    (CONTRACT, DEFAULT_CONTRACT_CONFIG_FILE),
    (CONNECTION, DEFAULT_CONNECTION_CONFIG_FILE),
    (PROTOCOL, DEFAULT_PROTOCOL_CONFIG_FILE),
    (SERVICE, DEFAULT_SERVICE_CONFIG_FILE),
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


def without_hash(public_id: str) -> PublicId:
    """Convert to public id."""
    try:
        return PublicId.from_str(public_id)
    except ValueError:
        return PublicId.from_json(PublicId.from_str(public_id).json)


def to_plural(string: str) -> str:
    """Convert component to plural"""
    return string + "s"


def reduce_sets(list_of_sets: List[Set]) -> Set[PackageId]:
    """Reduce a list of sets to one dimentional set."""
    reduced: Set[PackageId] = set()
    for s in list_of_sets:
        reduced = reduced.union(s)
    return reduced


def to_package_id(public_id: str, package_type: str) -> PackageId:
    """Convert to public id."""
    return PackageId(package_type, PublicId.from_str(public_id)).without_hash()


class DependencyTree:
    """This class represents the dependency tree for a registry."""

    @staticmethod
    def get_all_dependencies(item_config: Dict) -> List[PackageId]:
        """Returns a list of all available dependencies."""
        return list(
            reduce_sets(
                [
                    {
                        to_package_id(dependency, component_type)
                        for dependency in item_config.get(
                            to_plural(component_type), set()
                        )
                    }
                    for component_type, _ in COMPONENTS[1:]
                ]
            )
        )

    @classmethod
    def resolve_tree(cls, dependency_list: Dict[PackageId, List[PackageId]]) -> Dict:
        """
        Resolve dependency tree.

        :param dependency_list: the adjacency list of the dependency graph
        :return: the dependency tree
        """
        tree: Dict[PackageId, Dict] = {root_node: {} for root_node in dependency_list}
        # auxiliary variables to keep track during recursive calls :
        #  visited: a set for fast checking of already visited nodes in the current path of DFS
        #  stack:   the current stack of nodes in the depth-first visiting of nodes
        visited: Set[PackageId] = set()
        stack: List[PackageId] = []
        cls._resolve_tree_aux(dependency_list, tree, visited, stack)

        # _resolve_tree_aux did side-effect on the 'tree' object
        return tree

    @classmethod
    def _resolve_tree_aux(
        cls,
        dependency_list: Dict[PackageId, List[PackageId]],
        tree: Dict,
        visited: Set[PackageId],
        stack: List[PackageId],
    ) -> None:
        """
        Resolve dependency tree (auxiliary method of resolve_tree).

        IMPORTANT: This method does side-effect on the parameter 'tree', 'visited' and 'stack'.

        :param dependency_list: the adjacency list of hte dependency graph
        :param tree: the dependency tree
        :param visited: the set of visited nodes in the current path
        :param stack: the current path stored in a LIFO data structure
        """
        for root_package in tree:
            if root_package in visited:
                # cycle found; raise error
                cls._raise_circular_dependency_error(root_package, stack)
                return

            # add current package to the stack - needed to check if there are circular dependencies
            visited.add(root_package)
            stack.append(root_package)

            # build the root of the subtree according to the dependency list
            root_dependencies: List[PackageId] = dependency_list.get(root_package, [])
            tree[root_package] = {p: {} for p in root_dependencies}
            # do a recursive call on the newly created subtree
            cls._resolve_tree_aux(dependency_list, tree[root_package], visited, stack)

            # the current search node can be removed from the stack
            visited.discard(root_package)
            stack.pop()

    @classmethod
    def flatten_tree(
        cls, dependency_tree: Dict, flat_tree: List[List[PackageId]], level: int
    ) -> None:
        """Flatten tree."""
        try:
            flat_tree[level]
        except IndexError:
            flat_tree.insert(level, [])
        for package, dependencies in dependency_tree.items():
            flat_tree[level].append(package)
            cls.flatten_tree(dependencies, flat_tree, level + 1)

    @staticmethod
    def find_packages_in_a_project(
        project_dir: Path,
    ) -> List[Tuple[str, Path]]:
        """Find packages in an AEA project."""

        packages = []
        for package_type, config_file in COMPONENTS:
            _packages = [
                *Path(project_dir, VENDOR).glob(f"*/{package_type}s/*/{config_file}"),
                *Path(project_dir, f"{package_type}s").glob(f"*/{config_file}"),
            ]
            packages += [
                (package_type, package_path.parent) for package_path in _packages
            ]

        return packages

    @staticmethod
    def find_packages_in_a_local_repository(
        packages_dir: Path,
    ) -> List[Tuple[str, Path]]:
        """Find packages in a local repository."""

        packages = []
        for package_type, config_file in COMPONENTS:
            packages += [
                (package_type, package_path.parent)
                for package_path in Path(packages_dir).glob(
                    f"*/{package_type}s/*/{config_file}"
                )
            ]

        return packages

    @classmethod
    def generate(
        cls, packages_dir: Path, from_project: bool = False
    ) -> List[List[PackageId]]:
        """Returns PublicId to hash mapping."""
        package_to_dependency_mappings = {}
        packages_list = []

        if from_project or (packages_dir / VENDOR).exists():
            packages_list = cls.find_packages_in_a_project(packages_dir)
        else:
            packages_list = cls.find_packages_in_a_local_repository(packages_dir)

        for package_type, package_path in packages_list:
            item_config, _ = load_yaml(
                package_path / PACKAGE_TYPE_TO_CONFIG_FILE[package_type]
            )
            item_config["name"] = item_config.get("name", item_config.get("agent_name"))
            public_id = PublicId.from_json(item_config)
            package_to_dependency_mappings[
                to_package_id(str(public_id), package_type)
            ] = cls.get_all_dependencies(item_config)

        flat_tree: List[List[PackageId]] = []
        flat_tree_dirty: List[List[PackageId]] = []
        dirty_packages: List[PackageId] = []

        dep_tree = cls.resolve_tree(package_to_dependency_mappings)
        cls.flatten_tree(dep_tree, flat_tree_dirty, 0)

        for tree_level in reversed(flat_tree_dirty[:-1]):
            flat_tree.append(
                sorted(
                    {package for package in tree_level if package not in dirty_packages}
                )
            )
            dirty_packages += tree_level

        return flat_tree

    @classmethod
    def _raise_circular_dependency_error(
        cls, package: PackageId, stack: List[PackageId]
    ) -> None:
        # find first occurrence of the package in the stack:
        start = stack.index(package)
        start_node = stack[start]
        cycle = stack[start:]
        if len(cycle) == 1:
            raise AEAPackageLoadingError(
                f"Found a self-loop dependency while resolving dependency tree in package {cycle[0]}"
            )
        raise AEAPackageLoadingError(
            "Found a circular dependency while resolving dependency tree: "
            + " -> ".join(map(str, cycle + [start_node]))
        )
