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
import inspect
import itertools
import json
import logging
import os
import re
import types
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Collection, Dict, List, Optional, Set, Tuple, Union, cast

import jsonschema

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConfigurationType,
    DEFAULT_AEA_CONFIG_FILE,
    Dependencies,
    PublicId,
    ProtocolConfig, ConnectionConfig, SkillConfig, ContractConfig)
from aea.configurations.components import Component
from aea.configurations.loader import ConfigLoader
from aea.connections.base import Connection
from aea.context.base import AgentContext
from aea.contracts.base import Contract
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import (
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE,
    _create_ethereum_private_key,
    _create_fetchai_private_key,
    _try_validate_ethereum_private_key_path,
    _try_validate_fet_private_key_path,
)
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import SUPPORTED_CRYPTOS, Wallet
from aea.helpers.base import _SysModules, load_module
from aea.identity.base import Identity
from aea.mail.base import Address
from aea.protocols.base import Protocol
from aea.registries.resources import Resources
from aea.skills.base import Skill, SkillContext, Handler, Behaviour, Model

PathLike = Union[os.PathLike, Path, str]

logger = logging.getLogger(__name__)


class _DependenciesManager:
    """Class to manage dependencies of agent packages."""

    def __init__(self):
        """Initialize the dependency graph."""
        # adjacency list of the dependency DAG
        # an arc means "depends on"
        self._dependencies = {}  # type: Dict[ComponentId, ComponentConfiguration]
        self._all_dependencies_by_type = (
            {}
        )  # type: Dict[ComponentType, Dict[ComponentId, ComponentConfiguration]]
        self._prefix_to_components = (
            {}
        )  # type: Dict[Tuple[ComponentType, str, str], Set[ComponentId]]
        self._inverse_dependency_graph = {}  # type: Dict[ComponentId, Set[ComponentId]]

    @property
    def all_dependencies(self) -> Set[ComponentId]:
        """Get all dependencies."""
        result = set(self._dependencies.keys())
        return result

    @property
    def dependencies_highest_version(self) -> Set[ComponentId]:
        """Get the dependencies with highest version."""
        return {max(ids) for _, ids in self._prefix_to_components.items()}

    @property
    def protocols(self) -> Dict[ComponentId, ProtocolConfig]:
        """Get the protocols."""
        return cast(
            Dict[ComponentId, ProtocolConfig],
            self._all_dependencies_by_type.get(ComponentType.PROTOCOL, {}),
        )

    @property
    def connections(self) -> Dict[ComponentId, ConnectionConfig]:
        """Get the connections."""
        return cast(
            Dict[ComponentId, ConnectionConfig],
            self._all_dependencies_by_type.get(ComponentType.CONNECTION, {}),
        )

    @property
    def skills(self) -> Dict[ComponentId, SkillConfig]:
        """Get the skills."""
        return cast(
            Dict[ComponentId, SkillConfig],
            self._all_dependencies_by_type.get(ComponentType.SKILL, {}),
        )

    @property
    def contracts(self) -> Dict[ComponentId, ContractConfig]:
        """Get the contracts."""
        return cast(
            Dict[ComponentId, ContractConfig],
            self._all_dependencies_by_type.get(ComponentType.CONTRACT, {}),
        )

    def add_component(self, configuration: ComponentConfiguration) -> None:
        """
        Add a component to the dependency manager..

        :param configuration: the component configuration to add.
        :return: None
        """
        # add to main index
        self._dependencies[configuration.component_id] = configuration
        # add to index by type
        self._all_dependencies_by_type.setdefault(configuration.component_type, {})[
            configuration.component_id
        ] = configuration
        # add to prefix to id index
        self._prefix_to_components.setdefault(
            configuration.component_id.component_prefix, set()
        ).add(configuration.component_id)
        # populate inverse dependency
        for dependency in configuration.package_dependencies:
            self._inverse_dependency_graph.setdefault(dependency, set()).add(
                configuration.component_id
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
        # remove from prefix to id index
        self._prefix_to_components.get(component_id.component_prefix, set()).discard(
            component_id
        )
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

    @property
    def pypi_dependencies(self) -> Dependencies:
        """Get all the PyPI dependencies."""
        all_pypi_dependencies = {}  # type: Dependencies
        for configuration in self._dependencies.values():
            # TODO implement merging of two PyPI dependencies.
            all_pypi_dependencies.update(configuration.pypi_dependencies)
        return all_pypi_dependencies

    @staticmethod
    def _build_dotted_part(component, relative_import_path) -> str:
        """Given a component, build a dotted path for import."""
        if relative_import_path == "":
            return component.prefix_import_path
        else:
            return component.prefix_import_path + "." + relative_import_path


class AEABuilder:
    """
    This class helps to build an AEA.

    It follows the fluent interface. Every method of the builder
    returns the instance of the builder itself.
    """

    def __init__(self, with_default_packages: bool = True):
        """
        Initialize the builder.

        :param with_default_packages: add the default packages.
        """
        self._name = None  # type: Optional[str]
        self._resources = Resources()
        self._private_key_paths = {}  # type: Dict[str, str]
        self._ledger_apis_configs = {}  # type: Dict[str, Dict[str, Union[str, int]]]
        self._default_key = None  # set by the user, or instantiate a default one.
        self._default_ledger = (
            "fetchai"  # set by the user, or instantiate a default one.
        )
        self._default_connection = PublicId("fetchai", "stub", "0.1.0")

        self._package_dependency_manager = _DependenciesManager()

        if with_default_packages:
            self._add_default_packages()

    def _add_default_packages(self) -> None:
        """Add default packages."""
        # add default protocol
        self.add_protocol(Path(AEA_DIR, "protocols", "default"))
        # add stub connection
        self.add_connection(Path(AEA_DIR, "connections", "stub"))
        # add error skill
        self.add_skill(Path(AEA_DIR, "skills", "error"))

    def _check_can_remove(self, component_id: ComponentId) -> None:
        """
        Check if a component can be removed.

        :param component_id: the component id.
        :return: None
        :raises ValueError: if the component is already present.
        """
        if component_id not in self._package_dependency_manager.all_dependencies:
            raise ValueError(
                "Component {} of type {} not present.".format(
                    component_id.public_id, component_id.component_type
                )
            )

    def _check_can_add(self, configuration: ComponentConfiguration) -> None:
        """
        Check if the component can be added, given its configuration.

        :param configuration: the configuration of the component.
        :return: None
        :raises ValueError: if the component is not present.
        """
        self._check_configuration_not_already_added(configuration)
        self._check_package_dependencies(configuration)

    def set_name(self, name: str) -> "AEABuilder":
        """
        Set the name of the agent.

        :param name: the name of the agent.
        :return: the AEABuilder
        """
        self._name = name
        return self

    def set_default_connection(self, public_id: PublicId) -> "AEABuilder":
        """
        Set the default connection.

        :param public_id: the public id of the default connection package.
        :return: the AEABuilder
        """
        self._default_connection = public_id
        return self

    def add_private_key(
        self, identifier: str, private_key_path: PathLike
    ) -> "AEABuilder":
        """
        Add a private key path.

        :param identifier: the identifier for that private key path.
        :param private_key_path: path to the private key file.
        :return: the AEABuilder
        """
        self._private_key_paths[identifier] = str(private_key_path)
        return self

    def remove_private_key(self, identifier: str) -> "AEABuilder":
        """
        Remove a private key path by identifier, if present.

        :param identifier: the identifier of the private key.
        :return: the AEABuilder
        """
        self._private_key_paths.pop(identifier, None)
        return self

    @property
    def private_key_paths(self) -> Dict[str, str]:
        """Get the private key paths."""
        return self._private_key_paths

    def add_ledger_api_config(self, identifier: str, config: Dict) -> "AEABuilder":
        """
        Add a configuration for a ledger API to be supported by the agent.

        :param identifier: the identifier of the ledger api
        :param config: the configuration of the ledger api
        :return: the AEABuilder
        """
        self._ledger_apis_configs[identifier] = config
        return self

    def remove_ledger_api_config(self, identifier: str) -> "AEABuilder":
        """
        Remove a ledger API configuration.

        :param identifier: the identifier of the ledger api
        :return: the AEABuilder
        """
        self._ledger_apis_configs.pop(identifier, None)
        return self

    @property
    def ledger_apis_config(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """Get the ledger api configurations."""
        return self._ledger_apis_configs

    def set_default_ledger(self, identifier: str) -> "AEABuilder":
        """
        Set a default ledger API to use.

        :param identifier: the identifier of the ledger api
        :return: the AEABuilder
        """
        self._default_ledger = identifier
        return self

    def add_component(
        self,
        component_type: ComponentType,
        directory: PathLike,
        skip_consistency_check: bool = False,
    ) -> "AEABuilder":
        """
        Add a component, given its type and the directory.

        :param component_type: the component type.
        :param directory: the directory path.
        :param skip_consistency_check: if True, the consistency check are skipped.
        :raises ValueError: if a component is already registered with the same component id.
        :return: the AEABuilder
        """
        directory = Path(directory)
        configuration = ComponentConfiguration.load(
            component_type, directory, skip_consistency_check
        )
        self._check_can_add(configuration)
        # update dependency graph
        self._package_dependency_manager.add_component(configuration)
        configuration._directory = directory

        return self

    def _add_component_to_resources(self, component: Component) -> None:
        """Add component to the resources."""
        if component.component_type == ComponentType.CONNECTION:
            # Do nothing - we don't add connections to resources.
            return
        self._resources.add_component(component)

    def _remove_component_from_resources(self, component_id: ComponentId) -> None:
        """Remove a component from the resources."""
        if component_id.component_type == ComponentType.CONNECTION:
            return

        if component_id.component_type == ComponentType.PROTOCOL:
            self._resources.remove_protocol(component_id.public_id)
        elif component_id.component_type == ComponentType.SKILL:
            self._resources.remove_skill(component_id.public_id)

    def remove_component(self, component_id: ComponentId) -> "AEABuilder":
        """
        Remove a component.

        :param component_id: the public id of the component.
        :return: the AEABuilder
        """
        self._check_can_remove(component_id)
        self._remove(component_id)
        return self

    def _remove(self, component_id: ComponentId):
        self._package_dependency_manager.remove_component(component_id)
        self._remove_component_from_resources(component_id)

    def add_protocol(self, directory: PathLike) -> "AEABuilder":
        """
        Add a protocol to the agent.

        :param directory: the path to the protocol directory
        :return: the AEABuilder
        """
        self.add_component(ComponentType.PROTOCOL, directory)
        return self

    def remove_protocol(self, public_id: PublicId) -> "AEABuilder":
        """
        Remove protocol.

        :param public_id: the public id of the protocol
        :return: the AEABuilder
        """
        self.remove_component(ComponentId(ComponentType.PROTOCOL, public_id))
        return self

    def add_connection(self, directory: PathLike) -> "AEABuilder":
        """
        Add a connection to the agent.

        :param directory: the path to the connection directory
        :return: the AEABuilder
        """
        self.add_component(ComponentType.CONNECTION, directory)
        return self

    def remove_connection(self, public_id: PublicId) -> "AEABuilder":
        """
        Remove a connection.

        :param public_id: the public id of the connection
        :return: the AEABuilder
        """
        self.remove_component(ComponentId(ComponentType.CONNECTION, public_id))
        return self

    def add_skill(self, directory: PathLike) -> "AEABuilder":
        """
        Add a skill to the agent.

        :param directory: the path to the skill directory
        :return: the AEABuilder
        """
        self.add_component(ComponentType.SKILL, directory)
        return self

    def remove_skill(self, public_id: PublicId) -> "AEABuilder":
        """
        Remove protocol.

        :param public_id: the public id of the skill
        :return: the AEABuilder
        """
        self.remove_component(ComponentId(ComponentType.SKILL, public_id))
        return self

    def add_contract(self, directory: PathLike) -> "AEABuilder":
        """
        Add a contract to the agent.

        :param directory: the path to the contract directory
        :return: the AEABuilder
        """
        self.add_component(ComponentType.CONTRACT, directory)
        return self

    def remove_contract(self, public_id: PublicId) -> "AEABuilder":
        """
        Remove protocol.

        :param public_id: the public id of the contract
        :return: the AEABuilder
        """
        self.remove_component(ComponentId(ComponentType.CONTRACT, public_id))
        return self

    def _build_identity_from_wallet(self, wallet: Wallet) -> Identity:
        """
        Get the identity associated to a wallet.

        :param wallet: the wallet
        :return: the identity
        """
        assert self._name is not None, "You must set the name of the agent."
        if len(wallet.addresses) > 1:
            identity = Identity(
                self._name,
                addresses=wallet.addresses,
                default_address_key=self._default_ledger,
            )
        else:  # pragma: no cover
            identity = Identity(
                self._name, address=wallet.addresses[self._default_ledger],
            )
        return identity

    def _process_connection_ids(
        self, connection_ids: Optional[Collection[PublicId]] = None
    ) -> List[PublicId]:
        """
        Process connection ids.

        :param connection_ids: an optional list of connection ids
        :return: a list of connections
        """
        if connection_ids is not None:
            # check that all the connections are in the configuration file.
            connection_ids_set = set(connection_ids)
            all_supported_connection_ids = {
                cid.public_id
                for cid in self._package_dependency_manager.connections.keys()
            }
            non_supported_connections = connection_ids_set.difference(
                all_supported_connection_ids
            )
            if len(non_supported_connections) > 0:
                raise ValueError(
                    "Connection ids {} not declared in the configuration file.".format(
                        sorted(map(str, non_supported_connections))
                    )
                )
            selected_connections_ids = [
                component_id.public_id
                for component_id in self._package_dependency_manager.connections.keys()
                if component_id.public_id in connection_ids_set
            ]
        else:
            selected_connections_ids = [k.public_id for k in self._package_dependency_manager.connections.keys()]

        return selected_connections_ids

    def build(self, connection_ids: Optional[Collection[PublicId]] = None) -> AEA:
        """
        Build the AEA.

        :param connection_ids: select only these connections to run the AEA.
        :return: the AEA object.
        """
        wallet = Wallet(self.private_key_paths)
        identity = self._build_identity_from_wallet(wallet)
        connections = self._load_connections(identity.address, connection_ids)
        aea = AEA(
            identity,
            connections,
            wallet,
            LedgerApis(self.ledger_apis_config, self._default_ledger),
            self._resources,
            loop=None,
            timeout=0.0,
            is_debug=False,
            is_programmatic=True,
            max_reactions=20,
        )
        self._load_and_add_protocols()
        self._load_and_add_contracts()
        self._load_and_add_skills()
        self._set_agent_context_to_all_skills(aea.context)
        return aea

    def _set_agent_context_to_all_skills(self, context: AgentContext) -> None:
        """Set a skill context to all skills"""
        for skill in self._resources.get_all_skills():
            logger_name = "aea.{}.skills.{}.{}".format(
                context.agent_name, skill.configuration.author, skill.configuration.name
            )
            skill.skill_context.set_agent_context(context)
            skill.skill_context._logger = logging.getLogger(logger_name)

    def _check_configuration_not_already_added(self, configuration) -> None:
        if (
            configuration.component_id
            in self._package_dependency_manager.all_dependencies
        ):
            raise ValueError(
                "Component {} of type {} already added.".format(
                    configuration.public_id, configuration.component_type
                )
            )

    def _check_package_dependencies(self, configuration):
        self._package_dependency_manager.check_package_dependencies(configuration)

    @staticmethod
    def _find_component_directory_from_component_id(
        aea_project_directory: Path, component_id: ComponentId
    ) -> Path:
        """Find a component directory from component id."""
        # search in vendor first
        vendor_package_path = (
            aea_project_directory
            / "vendor"
            / component_id.public_id.author
            / component_id.component_type.to_plural()
            / component_id.public_id.name
        )
        if vendor_package_path.exists() and vendor_package_path.is_dir():
            return vendor_package_path

        # search in custom packages.
        custom_package_path = (
            aea_project_directory
            / component_id.component_type.to_plural()
            / component_id.public_id.name
        )
        if custom_package_path.exists() and custom_package_path.is_dir():
            return custom_package_path

        raise ValueError("Package {} not found.".format(component_id))

    @staticmethod
    def _try_to_load_agent_configuration_file(aea_project_path: Path) -> None:
        """Try to load the agent configuration file.."""
        try:
            configuration_file_path = Path(aea_project_path, DEFAULT_AEA_CONFIG_FILE)
            with configuration_file_path.open(mode="r", encoding="utf-8") as fp:
                loader = ConfigLoader.from_configuration_type(ConfigurationType.AGENT)
                agent_configuration = loader.load(fp)
                logging.config.dictConfig(agent_configuration.logging_config)
        except FileNotFoundError:
            raise Exception(
                "Agent configuration file '{}' not found in the current directory.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
        except jsonschema.exceptions.ValidationError:
            raise Exception(
                "Agent configuration file '{}' is invalid. Please check the documentation.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )

    @classmethod
    def from_aea_project(
        cls, aea_project_path: PathLike, skip_consistency_check: bool = False
    ) -> "AEABuilder":
        """
        Construct the builder from an AEA project

        - load agent configuration file
        - set name and default configurations
        - load private keys
        - load ledger API configurations
        - set default ledger
        - load every component

        :param aea_project_path: path to the AEA project.
        :param skip_consistency_check: if True, the consistency check are skipped.
        :return: an AEABuilder.
        """
        aea_project_path = Path(aea_project_path)
        cls._try_to_load_agent_configuration_file(aea_project_path)
        _verify_or_create_private_keys(aea_project_path)
        builder = AEABuilder(with_default_packages=False)

        # TODO isolate environment
        # load_env_file(str(aea_config_path / ".env"))

        # load agent configuration file
        configuration_file = aea_project_path / DEFAULT_AEA_CONFIG_FILE

        loader = ConfigLoader.from_configuration_type(ConfigurationType.AGENT)
        agent_configuration = loader.load(configuration_file.open())

        # set name and other configurations
        builder.set_name(agent_configuration.name)
        builder.set_default_ledger(agent_configuration.default_ledger)
        builder.set_default_connection(
            PublicId.from_str(agent_configuration.default_connection)
        )

        # load private keys
        for (
            ledger_identifier,
            private_key_path,
        ) in agent_configuration.private_key_paths_dict.items():
            builder.add_private_key(ledger_identifier, private_key_path)

        # load ledger API configurations
        for (
            ledger_identifier,
            ledger_api_conf,
        ) in agent_configuration.ledger_apis_dict.items():
            builder.add_ledger_api_config(ledger_identifier, ledger_api_conf)

        component_ids = itertools.chain(
            [
                ComponentId(ComponentType.PROTOCOL, p_id)
                for p_id in agent_configuration.protocols
            ],
            [
                ComponentId(ComponentType.CONTRACT, p_id)
                for p_id in agent_configuration.contracts
            ],
            [
                ComponentId(ComponentType.CONNECTION, p_id)
                for p_id in agent_configuration.connections
            ],
            [
                ComponentId(ComponentType.SKILL, p_id)
                for p_id in agent_configuration.skills
            ],
        )
        for component_id in component_ids:
            component_path = cls._find_component_directory_from_component_id(
                aea_project_path, component_id
            )
            builder.add_component(
                component_id.component_type,
                component_path,
                skip_consistency_check=skip_consistency_check,
            )

        return builder

    def _load_connections(self, address: Address, connection_ids: Optional[Collection[PublicId]] = None):
        connections_ids = self._process_connection_ids(connection_ids)
        def get_connection_configuration(connection_id):
            return self._package_dependency_manager.connections[ComponentId(ComponentType.CONNECTION, connection_id)]
        return [_load_connection(address, get_connection_configuration(connection_id)) for connection_id in connections_ids]

    def _load_and_add_protocols(self) -> None:
        for component_id, configuration in self._package_dependency_manager.protocols.items():
            protocol = Protocol.from_config(configuration)
            self._add_component_to_resources(protocol)

    def _load_and_add_contracts(self) -> None:
        for component_id, configuration in self._package_dependency_manager.contracts.items():
            contract = _load_contract(configuration)
            self._add_component_to_resources(contract)

    def _load_and_add_skills(self) -> None:
        for component_id, configuration in self._package_dependency_manager.skills.items():
            skill = Skill.from_config(configuration)
            self._add_component_to_resources(skill)


def _verify_or_create_private_keys(aea_project_path: Path) -> None:
    """Verify or create private keys."""
    path_to_configuration = aea_project_path / DEFAULT_AEA_CONFIG_FILE
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp_read = path_to_configuration.open(mode="r", encoding="utf-8")
    agent_configuration = agent_loader.load(fp_read)

    for identifier, _value in agent_configuration.private_key_paths.read_all():
        if identifier not in SUPPORTED_CRYPTOS:
            ValueError("Unsupported identifier in private key paths.")

    fetchai_private_key_path = agent_configuration.private_key_paths.read(FETCHAI)
    if fetchai_private_key_path is None:
        _create_fetchai_private_key(
            private_key_file=str(aea_project_path / FETCHAI_PRIVATE_KEY_FILE)
        )
        agent_configuration.private_key_paths.update(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
    else:
        try:
            _try_validate_fet_private_key_path(
                str(aea_project_path / fetchai_private_key_path), exit_on_error=False
            )
        except FileNotFoundError:  # pragma: no cover
            logger.error(
                "File {} for private key {} not found.".format(
                    repr(fetchai_private_key_path), FETCHAI,
                )
            )
            raise

    ethereum_private_key_path = agent_configuration.private_key_paths.read(ETHEREUM)
    if ethereum_private_key_path is None:
        _create_ethereum_private_key(
            private_key_file=str(aea_project_path / ETHEREUM_PRIVATE_KEY_FILE)
        )
        agent_configuration.private_key_paths.update(
            ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE
        )
    else:
        try:
            _try_validate_ethereum_private_key_path(
                str(aea_project_path / ethereum_private_key_path), exit_on_error=False
            )
        except FileNotFoundError:  # pragma: no cover
            logger.error(
                "File {} for private key {} not found.".format(
                    repr(ethereum_private_key_path), ETHEREUM,
                )
            )
            raise

    fp_write = path_to_configuration.open(mode="w", encoding="utf-8")
    agent_loader.dump(agent_configuration, fp_write)


def _load_connection(address: Address, configuration: ConnectionConfig) -> Connection:
    """
    Load a connection from a directory.

    :param address: the connection address.
    :param configuration: the connection configuration.
    :return: the connection.
    """
    try:
        directory = configuration.directory
        connection_module_path = directory / "connection.py"
        assert (
            connection_module_path.exists() and connection_module_path.is_file()
        ), "Connection module '{}' not found.".format(connection_module_path)
        connection_module = load_module(
            "connection_module", directory / "connection.py"
        )
        classes = inspect.getmembers(connection_module, inspect.isclass)
        connection_class_name = cast(str, configuration.class_name)
        connection_classes = list(
            filter(lambda x: re.match(connection_class_name, x[0]), classes)
        )
        name_to_class = dict(connection_classes)
        logger.debug("Processing connection {}".format(connection_class_name))
        connection_class = name_to_class.get(connection_class_name, None)
        assert connection_class is not None, "Connection class '{}' not found.".format(
            connection_class_name
        )
        return connection_class.from_config(address=address, configuration=configuration)
    except AssertionError as e:
        raise ValueError(str(e))


def _load_contract(configuration: ContractConfig) -> Contract:
    """
    Load a contract class from a directory.

    :param configuration: the contract configuration.
    :return: the contract object.
    """
    try:
        directory = configuration.directory
        contract_module = load_module("contracts", directory / "contract.py")
        classes = inspect.getmembers(contract_module, inspect.isclass)
        contract_class_name = cast(str, configuration.class_name)
        contract_classes = list(
            filter(lambda x: re.match(contract_class_name, x[0]), classes)
        )
        name_to_class = dict(contract_classes)
        logger.debug("Processing contract {}".format(contract_class_name))
        contract_class = name_to_class.get(contract_class_name, None)
        assert contract_class_name is not None, "Contract class '{}' not found.".format(
            contract_class_name
        )

        path = Path(directory, configuration.path_to_contract_interface)
        with open(path, "r") as interface_file:
            contract_interface = json.load(interface_file)

        return contract_class(configuration, contract_interface)
    except AssertionError as e:
        raise ValueError(str(e))
