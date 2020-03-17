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
import types
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Set, Tuple, List, cast

from aea.aea import AEA
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    PackageConfiguration,
    PublicId,
    PackageId,
)
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.helpers.base import _SysModules
from aea.identity.base import Identity
from aea.mail.base import Address
from aea.registries.base import Resources


class _Component:
    def __init__(
        self,
        component_type: ComponentType,
        component_configuration: ComponentConfiguration,
    ):
        """
        Initialize a package.

        :param component_type: the type of the package.
        :param component_configuration: the package configuration.
        """
        self._component_type = component_type  # one of protocol, skill, connection etc.
        self._component_config = component_configuration

        # mapping from import path to module object
        self.importpath_to_module = {}  # type: Dict[str, types.ModuleType]

        self._component_id = ComponentId(
            component_type, self._component_config.public_id
        )

    @property
    def component_id(self) -> ComponentId:
        """Ge the package id."""
        return self._component_id

    @classmethod
    def load(cls, component_type: ComponentType, directory: Path) -> "_Component":
        """Load package from dir"""
        configuration = ComponentConfiguration.load(component_type, directory)
        # load modules


class _DependenciesManager:
    """Class to manage dependencies of agent packages."""

    def __init__(self):
        """Initialize the dependency graph."""
        # adjacency list of the dependency DAG
        # an arc means "depends on"
        self.protocols = {}  # type: Dict[ComponentId, _Component]
        self.connections = {}  # type: Dict[ComponentId, _Component]
        self.skills = {}  # type: Dict[ComponentId, _Component]
        self.contracts = {}  # type: Dict[ComponentId, _Component]

        self._all_dependencies = {}  # type: Dict[ComponentId, _Component]

    @property
    def all_dependencies(self) -> Set:
        """Get all dependencies."""
        result = set(
            *self.protocols.keys(),
            *self.connections.keys(),
            *self.skills.keys(),
            *self.contracts.keys(),
        )
        return result

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
    def load_dependencies(
        self, component_configuration: ComponentConfiguration
    ) -> None:
        """
        Load dependencies of a component, so its modules can be loaded.

        :param component_configuration: the component configuration
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
            (import_path, module_obj)
            for component in self.protocols.values()
            for (import_path, module_obj) in component.importpath_to_module
        ]
        connections = [
            (import_path, module_obj)
            for component in self.connections.values()
            for (import_path, module_obj) in component.importpath_to_module
        ]
        skills = [
            (import_path, module_obj)
            for component in self.skills.values()
            for (import_path, module_obj) in component.importpath_to_module
        ]
        return cast(
            List[Tuple[str, types.ModuleType]], protocols + connections + skills
        )


class AEABuilder:
    """This class helps to build an AEA."""

    def __init__(self):
        self._wallet = Wallet({})  # TODO make Wallet mutable (add/remove_private_key)
        self._ledger_apis = LedgerApis({}, "")  # TODO make it mutable (add/remove api)

        self._resources = Resources()
        self._connections = []

        # identity
        self._name = None
        self._addresses = {}  # type: Dict[str, Address]
        self._default_key = None  # set by the user, or instantiate a default one.

        self._package_dependency_graph = _DependenciesManager()

        # add default protocol
        # self.add_protocol()
        # add error skill
        # self.add_skill()

    def set_name(self, name: str):
        self._name = name

    def add_address(self, identifier: str, address: Address):
        self._addresses[identifier] = address

    def remove_address(self, identifier: str):
        self._addresses.pop(identifier, None)

    def add_component(self, component_type: ComponentType, directory: Path) -> None:
        """
        Add a component, given its type and the directory.

        :param component_type: the component type.
        :param directory: the directory path.
        :return: None
        """
        # load config, check fingerprint, handle errors
        configuration = ComponentConfiguration.load(component_type, directory)
        configuration.check_fingerprint(directory)
        configuration.check_aea_version()

        # from config, check package dependencies
        self._package_dependency_graph.check_package_dependencies(configuration)

        # visit dependency graph, load modules in sys.modules when going backward
        with self._package_dependency_graph.load_dependencies(configuration):
            # try to load the package (e.g. the same we do for Skill.from_dir, but for any type
            _Component.load(component_type, directory)

        # add the loaded modules in self._agent_modules
        # update dependency graph
        # register new package in resources

    def remove_package(self, package_id: PackageId):
        """Remove a package"""
        # check dependency graph for pending packages
        # remove package
        # remove modules of package in internal indexes.

    def add_protocol(self, directory: Path):
        """Add a protocol to the agent."""
        # call add_package
        self.add_component(ComponentType.PROTOCOL, directory)

    def remove_protocol(self, public_id: PublicId):
        """Remove protocol"""
        # call remove_package
        self.remove_package(ComponentId(ComponentType.PROTOCOL, public_id))

    # def add_connection(self, path):
    # def remove_connection(self):
    # def add_skill(self, path):
    # def remove_skill(self):

    def build(self) -> AEA:
        """Get the AEA."""
        aea = AEA(
            Identity(self._name, addresses=self._addresses),
            self._connections,
            self._wallet,
            self._ledger_apis,
            self._resources,
            loop=None,
            timeout=0.0,
            is_debug=False,
            is_programmatic=True,
            max_reactions=20,
        )
        return aea

    def dump_config(self) -> AgentConfig:
        """Dump configurations"""

    def dump(self, directory):
        """Dump agent project."""


class AEAProject:
    """
    A kind of ORM for an AEA project. Ideally,
    it would support all the operations done with `aea`.
    """

    def __init__(self):

        self.agent_config = AgentConfig()

        self.package_configurations = {}  # type: Dict[PublicId, PackageConfiguration]
        self.vendor_package_configurations = (
            {}
        )  # type: Dict[PublicId, PackageConfiguration]
        # dependency graph also here?
        self._dependency_graph = {}

    @classmethod
    def from_directory(cls, directory):
        """Load agent project from directory"""
        # agent_configuration = ConfigLoader.from_configuration_type(
        #     ConfigurationType.AGENT
        # )
        # iterate over all the packages, do fingerprint checks etc. etc.

    def run(self):
        """Run the agent project"""
        # instantiate the builder
        # add protocols, then connections, then skills,
        #     in the order specified by the dependency graph (built from configs)
