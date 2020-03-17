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
from enum import Enum
from pathlib import Path
from typing import Dict, Set

from aea.aea import AEA
from aea.configurations.base import (
    AgentConfig,
    PackageConfiguration,
    PublicId,
)
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Address
from aea.registries.base import Resources


class PackageType(Enum):
    PROTOCOL = "protocol"
    CONNECTION = "connection"
    SKILL = "skill"
    CONTRACT = "contract"


class PackageId:
    """A package identifier."""

    def __init__(self, package_type: PackageType, public_id: PublicId):
        """
        Initialize the package id.

        :param package_type: the package type.
        :param public_id: the public id.
        """
        self._package_type = package_type
        self._public_id = public_id

    @property
    def package_type(self) -> PackageType:
        """Get the package type."""
        return self._package_type

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return self._public_id


class _Package:
    def __init__(
        self, package_type: PackageType, package_configuration: PackageConfiguration
    ):
        """
        Initialize a package.

        :param package_type: the type of the package.
        :param package_configuration: the package configuration.
        """
        self._package_type = package_type  # one of protocol, skill, connection etc.
        self._package_config = package_configuration
        self._modules = {}  # type: Dict

        self._package_id = PackageId(package_type, self._package_config.public_id)

    @property
    def package_id(self) -> PackageId:
        """Ge the package id."""
        return self._package_id

    @classmethod
    def load(cls, package_type) -> "_Package":
        """Load package from dir"""
        # read config file
        # load modules


class _DependencyGraph:
    """Class to handle a dependency graph for agent packages."""

    def __init__(self):
        """Initialize the dependency graph."""
        self._dependency_relation = {}  # type: Dict[PackageId, Set[_Package]]


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

        # from package id to packages it depends on.
        # we should detect loops at "add" time, by inspecting the component config file.
        self._dependency_graph = {}  # type: Dict[PackageId, Set[_Package]]

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

    def add_package(self, package_type: PackageType, directory: Path) -> None:
        """
        Load a package, given its type and the directory.

        :param package_type: the package type.
        :param directory: the directory path.
        :return: None
        """
        # load config, check fingerprint, handle errors
        # from config, check package dependencies
        # visit dependency graph, load modules in sys.modules when going backward
        # try to load the package (e.g. the same we do for Skill.from_dir, but for any type
        # _Package.load(package_type, directory)
        # remove all the modules from sys.modules
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
        self.add_package(PackageType.PROTOCOL, directory)

    def remove_protocol(self, public_id: PublicId):
        """Remove protocol"""
        # call remove_package
        self.remove_package(PackageId(PackageType.PROTOCOL, public_id))

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
