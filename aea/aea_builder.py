# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains utilities for building an AEA."""
import logging
import os
import types
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union, cast

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    PublicId,
)
from aea.configurations.components import Component
from aea.connections.base import Connection
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.helpers.base import _SysModules
from aea.identity.base import Identity
from aea.mail.base import Address
from aea.protocols.base import Protocol
from aea.registries.base import Resources
from aea.skills.base import Skill

PathLike = Union[os.PathLike, Path, str]


class _DependenciesManager:
    """Class to manage dependencies of agent packages."""

    def __init__(self):
        """Initialize the dependency graph."""
        # adjacency list of the dependency DAG
        # an arc means "depends on"
        self._dependencies = {}  # type: Dict[ComponentId, Component]
        self._all_dependencies_by_type = (
            {}
        )  # type: Dict[ComponentType, Dict[ComponentId, Component]]
        self._inverse_dependency_graph = {}  # type: Dict[ComponentId, Set[ComponentId]]

    @property
    def all_dependencies(self) -> Set[ComponentId]:
        """Get all dependencies."""
        result = set(self._dependencies.keys())
        return result

    @property
    def protocols(self) -> Dict[ComponentId, Protocol]:
        """Get the protocols."""
        return cast(
            Dict[ComponentId, Protocol],
            self._all_dependencies_by_type.get(ComponentType.PROTOCOL, {}),
        )

    @property
    def connections(self) -> Dict[ComponentId, Connection]:
        """Get the connections."""
        return cast(
            Dict[ComponentId, Connection],
            self._all_dependencies_by_type.get(ComponentType.CONNECTION, {}),
        )

    @property
    def skills(self) -> Dict[ComponentId, Skill]:
        """Get the skills."""
        return cast(
            Dict[ComponentId, Skill],
            self._all_dependencies_by_type.get(ComponentType.SKILL, {}),
        )

    @property
    def contracts(self) -> Dict[ComponentId, Any]:
        """Get the contracts."""
        return cast(
            Dict[ComponentId, Any],
            self._all_dependencies_by_type.get(ComponentType.CONTRACT, {}),
        )

    def add_component(self, component: Component) -> None:
        """Add a component."""
        self._dependencies[component.component_id] = component
        self._all_dependencies_by_type.setdefault(component.component_type, {})[
            component.component_id
        ] = component
        for dependency in component.configuration.package_dependencies:
            self._inverse_dependency_graph.setdefault(dependency, set()).add(
                component.component_id
            )

    def remove_component(self, component_id: ComponentId):
        """
        Remove a component.

        :return None
        :raises ValueError: if some component depends on this package.
        """
        if component_id not in self.all_dependencies:
            raise ValueError(
                "Component {} of type {} not present.".format(
                    component_id.public_id, component_id.component_type
                )
            )
        dependencies = self._inverse_dependency_graph.get(component_id, set())
        if len(dependencies) != 0:
            raise ValueError(
                "Cannot remove component {} of type {}. Other components depends on it: {}".format(
                    component_id.public_id, component_id.component_type, dependencies
                )
            )

        # remove from the index of all dependencies
        component = self._dependencies.pop(component_id)
        # remove from the index of all dependencies grouped by type
        self._all_dependencies_by_type[component_id.component_type].pop(component_id)
        if len(self._all_dependencies_by_type[component_id.component_type]) == 0:
            self._all_dependencies_by_type.pop(component_id.component_type)
        # update inverse dependency graph
        for dependency in component.configuration.package_dependencies:
            self._inverse_dependency_graph[dependency].discard(component_id)

    def check_package_dependencies(
        self, component_configuration: ComponentConfiguration
    ) -> bool:
        """
        Check that we have all the dependencies needed to the package.

        return: True if all the dependencies are covered, False otherwise.
        """
        not_supported_packages = component_configuration.package_dependencies.difference(
            self.all_dependencies
        )
        return len(not_supported_packages) == 0

    @contextmanager
    def load_dependencies(self):
        """
        Load dependencies of a component, so its modules can be loaded.

        :return: None
        """
        modules = self._get_import_order()
        with _SysModules.load_modules(modules):
            yield

    def _get_import_order(self) -> List[Tuple[str, types.ModuleType]]:
        """
        Get the import order.

        At the moment:
        - a protocol has no dependencies.
        - a connection can depend on protocols.
        - a skill can depend on protocols.
        - a contract ...

        :return: a list of pairs: (import path, module object)
        """
        # get protocols first
        protocols = [
            (self.build_dotted_part(component, relative_import_path), module_obj)
            for component in self.protocols.values()
            for (
                relative_import_path,
                module_obj,
            ) in component.importpath_to_module.items()
        ]
        connections = [
            (self.build_dotted_part(component, relative_import_path), module_obj)
            for component in self.connections.values()
            for (
                relative_import_path,
                module_obj,
            ) in component.importpath_to_module.items()
        ]
        skills = [
            (self.build_dotted_part(component, relative_import_path), module_obj)
            for component in self.skills.values()
            for (
                relative_import_path,
                module_obj,
            ) in component.importpath_to_module.items()
        ]
        return cast(
            List[Tuple[str, types.ModuleType]], protocols + connections + skills
        )

    def build_dotted_part(self, component, relative_import_path) -> str:
        """Given a component, build a dotted path for import."""
        if relative_import_path == "":
            return component.prefix_import_path
        else:
            return component.prefix_import_path + "." + relative_import_path


class AEABuilder:
    """This class helps to build an AEA."""

    def __init__(self):
        self._resources = Resources()

        # identity
        self._name = None
        self._addresses = {}  # type: Dict[str, Address]
        self._default_key = None  # set by the user, or instantiate a default one.

        self._package_dependency_graph = _DependenciesManager()

        # add default protocol
        self.add_protocol(Path(AEA_DIR, "protocols", "default"))
        # add stub connection
        self.add_connection(Path(AEA_DIR, "connections", "stub"))
        # add error skill
        self.add_skill(Path(AEA_DIR, "skills", "error"))

    def set_name(self, name: str) -> "AEABuilder":
        self._name = name
        return self

    def add_address(self, identifier: str, address: Address) -> "AEABuilder":
        self._addresses[identifier] = address
        return self

    def remove_address(self, identifier: str) -> "AEABuilder":
        self._addresses.pop(identifier, None)
        return self

    def add_component(
        self, component_type: ComponentType, directory: PathLike
    ) -> "AEABuilder":
        """
        Add a component, given its type and the directory.

        :param component_type: the component type.
        :param directory: the directory path.
        :return: None
        :raises ValueError: if a component is already registered with the same component id.
        """
        directory = Path(directory)
        configuration = ComponentConfiguration.load(component_type, directory)
        if (
            configuration.component_id
            in self._package_dependency_graph.all_dependencies
        ):
            raise ValueError(
                "Component {} of type {} already added.".format(
                    configuration.public_id, configuration.component_type
                )
            )

        with self._package_dependency_graph.load_dependencies():
            component = Component.load_from_directory(component_type, directory)

        self._package_dependency_graph.check_package_dependencies(
            component.configuration
        )

        # update dependency graph
        self._package_dependency_graph.add_component(component)
        # register new package in resources
        self._add_component_to_resources(component)

        return self

    def _add_component_to_resources(self, component: Component):
        """Add component to the resources."""
        if component.component_type == ComponentType.CONNECTION:
            # Do nothing - we don't add connections to resources.
            return

        if component.component_type == ComponentType.PROTOCOL:
            protocol = cast(Protocol, component)
            self._resources.add_protocol(protocol)
        elif component.component_type == ComponentType.SKILL:
            skill = cast(Skill, component)
            self._resources.add_skill(skill)

    def _remove_component_from_resources(self, component_id: ComponentId):
        """Remove a component from the resources."""
        if component_id.component_type == ComponentType.CONNECTION:
            return

        if component_id.component_type == ComponentType.PROTOCOL:
            self._resources.remove_protocol(component_id.public_id)
        elif component_id.component_type == ComponentType.SKILL:
            self._resources.remove_skill(component_id.public_id)

    def remove_component(self, component_id: ComponentId) -> "AEABuilder":
        """Remove a package"""
        if component_id not in self._package_dependency_graph.all_dependencies:
            raise ValueError(
                "Component {} of type {} not present.".format(
                    component_id.public_id, component_id.component_type
                )
            )

        self._package_dependency_graph.remove_component(component_id)
        self._remove_component_from_resources(component_id)

        return self

    def add_protocol(self, directory: PathLike) -> "AEABuilder":
        """Add a protocol to the agent."""
        self.add_component(ComponentType.PROTOCOL, directory)
        return self

    def remove_protocol(self, public_id: PublicId) -> "AEABuilder":
        """Remove protocol"""
        self.remove_component(ComponentId(ComponentType.PROTOCOL, public_id))
        return self

    def add_connection(self, directory: PathLike) -> "AEABuilder":
        """Add a protocol to the agent."""
        self.add_component(ComponentType.CONNECTION, directory)
        return self

    def remove_connection(self, public_id: PublicId) -> "AEABuilder":
        """Remove protocol"""
        self.remove_component(ComponentId(ComponentType.CONNECTION, public_id))
        return self

    def add_skill(self, directory: PathLike) -> "AEABuilder":
        """Add a protocol to the agent."""
        self.add_component(ComponentType.SKILL, directory)
        return self

    def remove_skill(self, public_id: PublicId) -> "AEABuilder":
        """Remove protocol"""
        self.remove_component(ComponentId(ComponentType.SKILL, public_id))
        return self

    def build(self) -> AEA:
        """Get the AEA."""
        connections = list(self._package_dependency_graph.connections.values())
        aea = AEA(
            Identity(self._name, addresses=self._addresses),
            connections,
            Wallet({}),
            LedgerApis({}, ""),
            self._resources,
            loop=None,
            timeout=0.0,
            is_debug=False,
            is_programmatic=True,
            max_reactions=20,
        )
        self._set_context_to_all_skills(aea.context)
        return aea

    def dump_config(self) -> AgentConfig:
        """Dump configurations"""

    def dump(self, directory):
        """Dump agent project."""

    def _set_context_to_all_skills(self, context: AgentContext):
        """Set a skill context to all skills"""
        for skill in self._resources.get_all_skills():
            logger_name = "aea.{}.skills.{}.{}".format(
                context.agent_name, skill.configuration.author, skill.configuration.name
            )
            skill.skill_context._agent_context = context
            skill.skill_context._logger = logging.getLogger(logger_name)


#
# class AEAProject:
#     """
#     A kind of ORM for an AEA project. Ideally,
#     it would support all the operations done with `aea`.
#     """
#
#     def __init__(self):
#
#         self.agent_config = AgentConfig()
#
#         self.package_configurations = {}  # type: Dict[PublicId, PackageConfiguration]
#         self.vendor_package_configurations = (
#             {}
#         )  # type: Dict[PublicId, PackageConfiguration]
#         # dependency graph also here?
#         self._dependency_graph = {}
#
#     @classmethod
#     def from_directory(cls, directory):
#         """Load agent project from directory"""
#         # agent_configuration = ConfigLoader.from_configuration_type(
#         #     ConfigurationType.AGENT
#         # )
#         # iterate over all the packages, do fingerprint checks etc. etc.
#
#     def run(self):
#         """Run the agent project"""
#         # instantiate the builder
#         # add protocols, then connections, then skills,
#         #     in the order specified by the dependency graph (built from configs)
