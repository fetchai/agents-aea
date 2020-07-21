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
import itertools
import json
import logging
import logging.config
import os
import pprint
from collections import defaultdict, deque
from copy import copy, deepcopy
from pathlib import Path
from typing import (
    Any,
    Collection,
    Deque,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import jsonschema

from packaging.specifiers import SpecifierSet

from aea import AEA_DIR
from aea.aea import AEA
from aea.components.base import Component
from aea.components.loader import load_component_from_config
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    DEFAULT_AEA_CONFIG_FILE,
    Dependencies,
    PackageType,
    ProtocolConfig,
    PublicId,
    SkillConfig,
)
from aea.configurations.constants import (
    DEFAULT_CONNECTION,
    DEFAULT_LEDGER,
    DEFAULT_PROTOCOL,
    DEFAULT_SKILL,
)
from aea.configurations.loader import ConfigLoader
from aea.contracts import contract_registry
from aea.crypto.helpers import (
    IDENTIFIER_TO_KEY_FILES,
    create_private_key,
    try_validate_private_key_path,
)
from aea.crypto.registries import crypto_registry
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMakerHandler
from aea.decision_maker.default import (
    DecisionMakerHandler as DefaultDecisionMakerHandler,
)
from aea.exceptions import AEAException
from aea.helpers.base import load_aea_package, load_module
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.helpers.logging import AgentLoggerAdapter
from aea.helpers.pypi import is_satisfiable
from aea.helpers.pypi import merge_dependencies
from aea.identity.base import Identity
from aea.registries.resources import Resources

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

    def get_components_by_type(
        self, component_type: ComponentType
    ) -> Dict[ComponentId, ComponentConfiguration]:
        """Get the components by type."""
        return self._all_dependencies_by_type.get(component_type, {})

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
        for dependency in component.package_dependencies:
            self._inverse_dependency_graph[dependency].discard(component_id)

    @property
    def pypi_dependencies(self) -> Dependencies:
        """
        Get all the PyPI dependencies.

        We currently consider only dependency that have the
        default PyPI index url and that specify only the
        version field.

        :return: the merged PyPI dependencies
        """
        all_pypi_dependencies = {}  # type: Dependencies
        for configuration in self._dependencies.values():
            all_pypi_dependencies = merge_dependencies(
                all_pypi_dependencies, configuration.pypi_dependencies
            )
        return all_pypi_dependencies


class AEABuilder:
    """
    This class helps to build an AEA.

    It follows the fluent interface. Every method of the builder
    returns the instance of the builder itself.

    Note: the method 'build()' is guaranteed of being
    re-entrant with respect to the 'add_component(path)'
    method. That is, you can invoke the building method
    many times against the same builder instance, and the
    returned agent instance will not share the
    components with other agents, e.g.:

        builder = AEABuilder()
        builder.add_component(...)
        ...

        # first call
        my_aea_1 = builder.build()

        # following agents will have different components.
        my_aea_2 = builder.build()  # all good

    However, if you manually loaded some of the components and added
    them with the method 'add_component_instance()', then calling build
    more than one time is prevented:

        builder = AEABuilder()
        builder.add_component_instance(...)
        ...  # other initialization code

        # first call
        my_aea_1 = builder.build()

        # second call to `build()` would raise a Value Error.
        # call reset
        builder.reset()

        # re-add the component and private keys
        builder.add_component_instance(...)
        ... # add private keys

        # second call
        my_aea_2 = builder.builder()

    """

    DEFAULT_AGENT_LOOP_TIMEOUT = 0.05
    DEFAULT_EXECUTION_TIMEOUT = 0
    DEFAULT_MAX_REACTIONS = 20
    DEFAULT_DECISION_MAKER_HANDLER_CLASS: Type[
        DecisionMakerHandler
    ] = DefaultDecisionMakerHandler
    DEFAULT_SKILL_EXCEPTION_POLICY = ExceptionPolicyEnum.propagate
    DEFAULT_LOOP_MODE = "async"
    DEFAULT_RUNTIME_MODE = "threaded"
    DEFAULT_SEARCH_SERVICE_ADDRESS = "fetchai/soef:*"

    # pylint: disable=attribute-defined-outside-init

    def __init__(self, with_default_packages: bool = True):
        """
        Initialize the builder.

        :param with_default_packages: add the default packages.
        """
        self._with_default_packages = with_default_packages
        self._reset(is_full_reset=True)

    def reset(self, is_full_reset: bool = False) -> None:
        """
        Reset the builder.

        A full reset causes a reset of all data on the builder. A partial reset
        only resets:
            - name,
            - private keys, and
            - component instances

        :param is_full_reset: whether it is a full reset or not.
        :return: None
        """
        self._reset(is_full_reset)

    def _reset(self, is_full_reset: bool = False) -> None:
        """
        Reset the builder (private usage).

        :param is_full_reset: whether it is a full reset or not.
        :return: None.
        """
        self._name = None  # type: Optional[str]
        self._private_key_paths = {}  # type: Dict[str, Optional[str]]
        self._connection_private_key_paths = {}  # type: Dict[str, Optional[str]]
        if not is_full_reset:
            self._remove_components_from_dependency_manager()
        self._component_instances = {
            ComponentType.CONNECTION: {},
            ComponentType.CONTRACT: {},
            ComponentType.PROTOCOL: {},
            ComponentType.SKILL: {},
        }  # type: Dict[ComponentType, Dict[ComponentConfiguration, Component]]
        self._to_reset: bool = False
        self._build_called: bool = False
        if not is_full_reset:
            return
        self._default_ledger = DEFAULT_LEDGER
        self._default_connection: PublicId = DEFAULT_CONNECTION
        self._context_namespace = {}  # type: Dict[str, Any]
        self._timeout: Optional[float] = None
        self._execution_timeout: Optional[float] = None
        self._max_reactions: Optional[int] = None
        self._decision_maker_handler_class: Optional[Type[DecisionMakerHandler]] = None
        self._skill_exception_policy: Optional[ExceptionPolicyEnum] = None
        self._default_routing: Dict[PublicId, PublicId] = {}
        self._loop_mode: Optional[str] = None
        self._runtime_mode: Optional[str] = None
        self._search_service_address: Optional[str] = None

        self._package_dependency_manager = _DependenciesManager()
        if self._with_default_packages:
            self._add_default_packages()

    def _remove_components_from_dependency_manager(self) -> None:
        """Remove components added via 'add_component' from the dependency manager."""
        for component_type in self._component_instances.keys():
            for component_config in self._component_instances[component_type].keys():
                self._package_dependency_manager.remove_component(
                    component_config.component_id
                )

    def set_timeout(self, timeout: Optional[float]) -> "AEABuilder":
        """
        Set agent loop idle timeout in seconds.

        :param timeout: timeout in seconds

        :return: self
        """
        self._timeout = timeout
        return self

    def set_execution_timeout(self, execution_timeout: Optional[float]) -> "AEABuilder":
        """
        Set agent execution timeout in seconds.

        :param execution_timeout: execution_timeout in seconds

        :return: self
        """
        self._execution_timeout = execution_timeout
        return self

    def set_max_reactions(self, max_reactions: Optional[int]) -> "AEABuilder":
        """
        Set agent max reaction in one react.

        :param max_reactions: int

        :return: self
        """
        self._max_reactions = max_reactions
        return self

    def set_decision_maker_handler(
        self, decision_maker_handler_dotted_path: str, file_path: Path
    ) -> "AEABuilder":
        """
        Set decision maker handler class.

        :param decision_maker_handler_dotted_path: the dotted path to the decision maker handler
        :param file_path: the file path to the file which contains the decision maker handler

        :return: self
        """
        dotted_path, class_name = decision_maker_handler_dotted_path.split(":")
        module = load_module(dotted_path, file_path)

        try:
            _class = getattr(module, class_name)
            self._decision_maker_handler_class = _class
        except Exception as e:  # pragma: nocover
            logger.error(
                "Could not locate decision maker handler for dotted path '{}', class name '{}' and file path '{}'. Error message: {}".format(
                    dotted_path, class_name, file_path, e
                )
            )
            raise  # log and re-raise because we should not build an agent from an. invalid configuration

        return self

    def set_skill_exception_policy(
        self, skill_exception_policy: Optional[ExceptionPolicyEnum]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set skill exception policy.

        :param skill_exception_policy: the policy

        :return: self
        """
        self._skill_exception_policy = skill_exception_policy
        return self

    def set_default_routing(
        self, default_routing: Dict[PublicId, PublicId]
    ) -> "AEABuilder":
        """
        Set default routing.

        This is a map from public ids (protocols) to public ids (connections).

        :param default_routing: the default routing mapping

        :return: self
        """
        self._default_routing = default_routing  # pragma: nocover
        return self

    def set_loop_mode(
        self, loop_mode: Optional[str]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the loop mode.

        :param loop_mode: the agent loop mode
        :return: self
        """
        self._loop_mode = loop_mode
        return self

    def set_runtime_mode(
        self, runtime_mode: Optional[str]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the runtime mode.

        :param runtime_mode: the agent runtime mode
        :return: self
        """
        self._runtime_mode = runtime_mode
        return self

    def set_search_service_address(
        self, search_service_address: str
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the search service address.

        :param search_service_address: the search service address
        :return: self
        """
        self._search_service_address = search_service_address
        return self

    def _add_default_packages(self) -> None:
        """Add default packages."""
        # add default protocol
        self.add_protocol(Path(AEA_DIR, "protocols", DEFAULT_PROTOCOL.name))
        # add stub connection
        self.add_connection(Path(AEA_DIR, "connections", DEFAULT_CONNECTION.name))
        # add error skill
        self.add_skill(Path(AEA_DIR, "skills", DEFAULT_SKILL.name))

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
        """
        self._check_configuration_not_already_added(configuration)
        self._check_package_dependencies(configuration)
        self._check_pypi_dependencies(configuration)

    def set_name(self, name: str) -> "AEABuilder":  # pragma: nocover
        """
        Set the name of the agent.

        :param name: the name of the agent.
        :return: the AEABuilder
        """
        self._name = name
        return self

    def set_default_connection(
        self, public_id: PublicId
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the default connection.

        :param public_id: the public id of the default connection package.
        :return: the AEABuilder
        """
        self._default_connection = public_id
        return self

    def add_private_key(
        self,
        identifier: str,
        private_key_path: Optional[PathLike] = None,
        is_connection: bool = False,
    ) -> "AEABuilder":
        """
        Add a private key path.

        :param identifier: the identifier for that private key path.
        :param private_key_path: an (optional) path to the private key file.
            If None, the key will be created at build time.
        :param is_connection: if the pair is for the connection cryptos
        :return: the AEABuilder
        """
        if is_connection:
            self._connection_private_key_paths[identifier] = (
                str(private_key_path) if private_key_path is not None else None
            )
        else:
            self._private_key_paths[identifier] = (
                str(private_key_path) if private_key_path is not None else None
            )
        if private_key_path is not None:
            self._to_reset = True
        return self

    def remove_private_key(
        self, identifier: str, is_connection: bool = False
    ) -> "AEABuilder":
        """
        Remove a private key path by identifier, if present.

        :param identifier: the identifier of the private key.
        :param is_connection: if the pair is for the connection cryptos
        :return: the AEABuilder
        """
        if is_connection:
            self._connection_private_key_paths.pop(identifier, None)
        else:
            self._private_key_paths.pop(identifier, None)
        return self

    @property
    def private_key_paths(self) -> Dict[str, Optional[str]]:
        """Get the private key paths."""
        return self._private_key_paths

    @property
    def connection_private_key_paths(self) -> Dict[str, Optional[str]]:
        """Get the connection private key paths."""
        return self._connection_private_key_paths

    def set_default_ledger(self, identifier: str) -> "AEABuilder":  # pragma: nocover
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
        :raises AEAException: if a component is already registered with the same component id.
                            | or if there's a missing dependency.
        :return: the AEABuilder
        """
        directory = Path(directory)
        configuration = ComponentConfiguration.load(
            component_type, directory, skip_consistency_check
        )
        self._check_can_add(configuration)
        # update dependency graph
        self._package_dependency_manager.add_component(configuration)
        configuration.directory = directory

        return self

    def add_component_instance(self, component: Component) -> "AEABuilder":
        """
        Add already initialized component object to resources or connections.

        Please, pay attention, all dependencies have to be already loaded.

        Notice also that this will make the call to 'build()' non re-entrant.
        You will have to `reset()` the builder before calling `build()` again.

        :params component: Component instance already initialized.
        """
        self._to_reset = True
        self._check_can_add(component.configuration)
        # update dependency graph
        self._package_dependency_manager.add_component(component.configuration)
        self._component_instances[component.component_type][
            component.configuration
        ] = component
        return self

    def set_context_namespace(
        self, context_namespace: Dict[str, Any]
    ) -> "AEABuilder":  # pragma: nocover
        """Set the context namespace."""
        self._context_namespace = context_namespace
        return self

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
                self._name,
                address=wallet.addresses[self._default_ledger],
                default_address_key=self._default_ledger,
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
            selected_connections_ids = [
                component_id.public_id
                for component_id in self._package_dependency_manager.connections.keys()
            ]

        # sort default id to be first
        if self._default_connection in selected_connections_ids:
            selected_connections_ids.remove(self._default_connection)
            sorted_selected_connections_ids = [
                self._default_connection
            ] + selected_connections_ids
        else:
            raise ValueError(
                "Default connection not a dependency. Please add it and retry."
            )

        return sorted_selected_connections_ids

    def build(self, connection_ids: Optional[Collection[PublicId]] = None,) -> AEA:
        """
        Build the AEA.

        This method is re-entrant only if the components have been
        added through the method 'add_component'. If some of them
        have been loaded with 'add_component_instance', it
        can be called only once, and further calls are only possible
        after a call to 'reset' and re-loading of the components added
        via 'add_component_instance' and the private keys.

        :param connection_ids: select only these connections to run the AEA.
        :return: the AEA object.
        :raises ValueError: if we cannot
        """
        self._check_we_can_build()
        resources = Resources()
        wallet = Wallet(
            copy(self.private_key_paths), copy(self.connection_private_key_paths)
        )
        identity = self._build_identity_from_wallet(wallet)
        self._load_and_add_components(ComponentType.PROTOCOL, resources, identity.name)
        self._load_and_add_components(ComponentType.CONTRACT, resources, identity.name)
        self._load_and_add_components(
            ComponentType.CONNECTION,
            resources,
            identity.name,
            identity=identity,
            crypto_store=wallet.connection_cryptos,
        )
        connection_ids = self._process_connection_ids(connection_ids)
        aea = AEA(
            identity,
            wallet,
            resources,
            loop=None,
            timeout=self._get_agent_loop_timeout(),
            execution_timeout=self._get_execution_timeout(),
            is_debug=False,
            max_reactions=self._get_max_reactions(),
            decision_maker_handler_class=self._get_decision_maker_handler_class(),
            skill_exception_policy=self._get_skill_exception_policy(),
            default_routing=self._get_default_routing(),
            default_connection=self._get_default_connection(),
            loop_mode=self._get_loop_mode(),
            runtime_mode=self._get_runtime_mode(),
            connection_ids=connection_ids,
            search_service_address=self._get_search_service_address(),
            **deepcopy(self._context_namespace),
        )
        self._load_and_add_components(
            ComponentType.SKILL, resources, identity.name, agent_context=aea.context
        )
        self._build_called = True
        self._populate_contract_registry()
        return aea

    def _get_agent_loop_timeout(self) -> float:
        """
        Return agent loop idle timeout.

        :return: timeout in seconds if set else default value.
        """
        return (
            self._timeout
            if self._timeout is not None
            else self.DEFAULT_AGENT_LOOP_TIMEOUT
        )

    def _get_execution_timeout(self) -> float:
        """
        Return execution timeout.

        :return: timeout in seconds if set else default value.
        """
        return (
            self._execution_timeout
            if self._execution_timeout is not None
            else self.DEFAULT_EXECUTION_TIMEOUT
        )

    def _get_max_reactions(self) -> int:
        """
        Return agent max_reaction.

        :return: max-reactions if set else default value.
        """
        return (
            self._max_reactions
            if self._max_reactions is not None
            else self.DEFAULT_MAX_REACTIONS
        )

    def _get_decision_maker_handler_class(self) -> Type[DecisionMakerHandler]:
        """
        Return the decision maker handler class.

        :return: decision maker handler class
        """
        return (
            self._decision_maker_handler_class
            if self._decision_maker_handler_class is not None
            else self.DEFAULT_DECISION_MAKER_HANDLER_CLASS
        )

    def _get_skill_exception_policy(self) -> ExceptionPolicyEnum:
        """
        Return the skill exception policy.

        :return: the skill exception policy.
        """
        return (
            self._skill_exception_policy
            if self._skill_exception_policy is not None
            else self.DEFAULT_SKILL_EXCEPTION_POLICY
        )

    def _get_default_routing(self) -> Dict[PublicId, PublicId]:
        """
        Return the default routing.

        :return: the default routing
        """
        return self._default_routing

    def _get_default_connection(self) -> PublicId:
        """
        Return the default connection.

        :return: the default connection
        """
        return self._default_connection

    def _get_loop_mode(self) -> str:
        """
        Return the loop mode name.

        :return: the loop mode name
        """
        return (
            self._loop_mode if self._loop_mode is not None else self.DEFAULT_LOOP_MODE
        )

    def _get_runtime_mode(self) -> str:
        """
        Return the runtime mode name.

        :return: the runtime mode name
        """
        return (
            self._runtime_mode
            if self._runtime_mode is not None
            else self.DEFAULT_RUNTIME_MODE
        )

    def _get_search_service_address(self) -> str:
        """
        Return the search service address.

        :return: the search service address.
        """
        return (
            self._search_service_address
            if self._search_service_address is not None
            else self.DEFAULT_SEARCH_SERVICE_ADDRESS
        )

    def _check_configuration_not_already_added(
        self, configuration: ComponentConfiguration
    ) -> None:
        """
        Check the component configuration has not already been added.

        :param configuration: the configuration being added
        :return: None
        :raises AEAException: if the component is already present.
        """
        if (
            configuration.component_id
            in self._package_dependency_manager.all_dependencies
        ):
            raise AEAException(
                "Component '{}' of type '{}' already added.".format(
                    configuration.public_id, configuration.component_type
                )
            )

    def _check_package_dependencies(
        self, configuration: ComponentConfiguration
    ) -> None:
        """
        Check that we have all the dependencies needed to the package.

        :return: None
        :raises AEAException: if there's a missing dependency.
        """
        not_supported_packages = configuration.package_dependencies.difference(
            self._package_dependency_manager.all_dependencies
        )  # type: Set[ComponentId]
        has_all_dependencies = len(not_supported_packages) == 0
        if not has_all_dependencies:
            raise AEAException(
                "Package '{}' of type '{}' cannot be added. Missing dependencies: {}".format(
                    configuration.public_id,
                    configuration.component_type.value,
                    pprint.pformat(sorted(map(str, not_supported_packages))),
                )
            )

    def _check_pypi_dependencies(self, configuration: ComponentConfiguration):
        """
        Check that PyPI dependencies of a package don't conflict with the existing ones.

        :param configuration: the component configuration.
        :return: None
        :raises AEAException: if some PyPI dependency is conflicting.
        """
        all_pypi_dependencies = self._package_dependency_manager.pypi_dependencies
        all_pypi_dependencies = merge_dependencies(
            all_pypi_dependencies, configuration.pypi_dependencies
        )
        for pkg_name, dep_info in all_pypi_dependencies.items():
            set_specifier = SpecifierSet(dep_info.get("version", ""))
            if not is_satisfiable(set_specifier):
                raise AEAException(
                    f"Conflict on package {pkg_name}: specifier set '{dep_info['version']}' not satisfiable."
                )

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
                loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
                agent_configuration = loader.load(fp)
                logging.config.dictConfig(agent_configuration.logging_config)  # type: ignore
        except FileNotFoundError:  # pragma: nocover
            raise Exception(
                "Agent configuration file '{}' not found in the current directory.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
        except jsonschema.exceptions.ValidationError:  # pragma: nocover
            raise Exception(
                "Agent configuration file '{}' is invalid. Please check the documentation.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )

    def set_from_configuration(
        self,
        agent_configuration: AgentConfig,
        aea_project_path: Path,
        skip_consistency_check: bool = False,
    ) -> None:
        """
        Set builder variables from AgentConfig.

        :params agent_configuration: AgentConfig to get values from.
        :params aea_project_path: PathLike root directory of the agent project.
        :param skip_consistency_check: if True, the consistency check are skipped.

        :return: None
        """
        # set name and other configurations
        self.set_name(agent_configuration.name)
        self.set_default_ledger(agent_configuration.default_ledger)
        self.set_default_connection(
            PublicId.from_str(agent_configuration.default_connection)
        )
        self.set_timeout(agent_configuration.timeout)
        self.set_execution_timeout(agent_configuration.execution_timeout)
        self.set_max_reactions(agent_configuration.max_reactions)
        if agent_configuration.decision_maker_handler != {}:
            dotted_path = agent_configuration.decision_maker_handler["dotted_path"]
            file_path = agent_configuration.decision_maker_handler["file_path"]
            self.set_decision_maker_handler(dotted_path, file_path)
        if agent_configuration.skill_exception_policy is not None:
            self.set_skill_exception_policy(
                ExceptionPolicyEnum(agent_configuration.skill_exception_policy)
            )
        self.set_default_routing(agent_configuration.default_routing)
        self.set_loop_mode(agent_configuration.loop_mode)
        self.set_runtime_mode(agent_configuration.runtime_mode)

        if (
            agent_configuration._default_connection  # pylint: disable=protected-access
            is None
        ):
            self.set_default_connection(DEFAULT_CONNECTION)
        else:
            self.set_default_connection(
                PublicId.from_str(agent_configuration.default_connection)
            )

        # load private keys
        for (
            ledger_identifier,
            private_key_path,
        ) in agent_configuration.private_key_paths_dict.items():
            self.add_private_key(ledger_identifier, private_key_path)

        # load connection private keys
        for (
            ledger_identifier,
            private_key_path,
        ) in agent_configuration.connection_private_key_paths_dict.items():
            self.add_private_key(
                ledger_identifier, private_key_path, is_connection=True
            )

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
        )
        for component_id in component_ids:
            component_path = self._find_component_directory_from_component_id(
                aea_project_path, component_id
            )
            self.add_component(
                component_id.component_type,
                component_path,
                skip_consistency_check=skip_consistency_check,
            )

        skill_ids = [
            ComponentId(ComponentType.SKILL, p_id)
            for p_id in agent_configuration.skills
        ]

        if len(skill_ids) == 0:
            return

        skill_import_order = self._find_import_order(
            skill_ids, aea_project_path, skip_consistency_check
        )
        for skill_id in skill_import_order:
            component_path = self._find_component_directory_from_component_id(
                aea_project_path, skill_id
            )
            self.add_component(
                skill_id.component_type,
                component_path,
                skip_consistency_check=skip_consistency_check,
            )

    def _find_import_order(
        self,
        skill_ids: List[ComponentId],
        aea_project_path: Path,
        skip_consistency_check: bool,
    ) -> List[ComponentId]:
        """Find import order for skills.

        We need to handle skills separately, since skills can depend on each other.

        That is, we need to:
        - load the skill configurations to find the import order
        - detect if there are cycles
        - import skills from the leaves of the dependency graph, by finding a topological ordering.
        """
        # the adjacency list for the dependency graph
        depends_on: Dict[ComponentId, Set[ComponentId]] = defaultdict(set)
        # the adjacency list for the inverse dependency graph
        supports: Dict[ComponentId, Set[ComponentId]] = defaultdict(set)
        # nodes with no incoming edges
        roots = copy(skill_ids)
        for skill_id in skill_ids:
            component_path = self._find_component_directory_from_component_id(
                aea_project_path, skill_id
            )
            configuration = cast(
                SkillConfig,
                ComponentConfiguration.load(
                    skill_id.component_type, component_path, skip_consistency_check
                ),
            )

            if len(configuration.skills) != 0:
                roots.remove(skill_id)

            depends_on[skill_id].update(
                [
                    ComponentId(ComponentType.SKILL, skill)
                    for skill in configuration.skills
                ]
            )
            for dependency in configuration.skills:
                supports[ComponentId(ComponentType.SKILL, dependency)].add(skill_id)

        # find topological order (Kahn's algorithm)
        queue: Deque[ComponentId] = deque()
        order = []
        queue.extend(roots)
        while len(queue) > 0:
            current = queue.pop()
            order.append(current)
            for node in supports[
                current
            ]:  # pragma: nocover # TODO: extract method and test properly
                depends_on[node].discard(current)
                if len(depends_on[node]) == 0:
                    queue.append(node)

        if any(len(edges) > 0 for edges in depends_on.values()):
            raise AEAException("Cannot load skills, there is a cyclic dependency.")

        return order

    @classmethod
    def from_aea_project(
        cls, aea_project_path: PathLike, skip_consistency_check: bool = False
    ) -> "AEABuilder":
        """
        Construct the builder from an AEA project.

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

        loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
        agent_configuration = loader.load(configuration_file.open())

        builder.set_from_configuration(
            agent_configuration, aea_project_path, skip_consistency_check
        )
        return builder

    def _load_and_add_components(
        self,
        component_type: ComponentType,
        resources: Resources,
        agent_name: str,
        **kwargs,
    ) -> None:
        """
        Load and add components added to the builder to a Resources instance.

        :param component_type: the component type for which
        :param resources: the resources object to populate.
        :param agent_name: the AEA name for logging purposes.
        :param kwargs: keyword argument to forward to the component loader.
        :return: None
        """
        for configuration in self._package_dependency_manager.get_components_by_type(
            component_type
        ).values():
            if configuration.is_abstract_component:
                load_aea_package(configuration)
                continue

            if configuration in self._component_instances[component_type].keys():
                component = self._component_instances[component_type][configuration]
            else:
                configuration = deepcopy(configuration)
                component = load_component_from_config(configuration, **kwargs)

            _set_logger_to_component(component, configuration, agent_name)
            resources.add_component(component)

    def _populate_contract_registry(self):
        """Populate contract registry."""
        for configuration in self._package_dependency_manager.get_components_by_type(
            ComponentType.CONTRACT
        ).values():
            configuration = cast(ContractConfig, configuration)
            if str(configuration.public_id) in contract_registry.specs:
                logger.warning(
                    f"Skipping registration of contract {configuration.public_id} since already registered."
                )
                continue
            logger.debug(f"Registering contract {configuration.public_id}")

            path = Path(
                configuration.directory, configuration.path_to_contract_interface
            )
            with open(path, "r") as interface_file:
                contract_interface = json.load(interface_file)

            try:
                contract_registry.register(
                    id_=str(configuration.public_id),
                    entry_point=f"{configuration.prefix_import_path}.contract:{configuration.class_name}",
                    class_kwargs={"contract_interface": contract_interface},
                    contract_config=configuration,  # TODO: resolve configuration being applied globally
                )
            except AEAException as e:  # pragma: nocover
                if "Cannot re-register id:" in str(e):
                    logger.warning(
                        "Already registered: {}".format(configuration.class_name)
                    )
                else:
                    raise e

    def _check_we_can_build(self):
        if self._build_called and self._to_reset:
            raise ValueError(
                "Cannot build the agent; You have done one of the following:\n"
                "- added a component instance;\n"
                "- added a private key manually.\n"
                "Please call 'reset() if you want to build another agent."
            )


def _set_logger_to_component(
    component: Component, configuration: ComponentConfiguration, agent_name: str,
) -> None:
    """
    Set the logger to the component.

    :param component: the component instance.
    :param configuration: the component configuration
    :param agent_name: the agent name
    :return: None
    """
    if configuration.component_type == ComponentType.SKILL:
        # skip because skill object already have their own logger from the skill context.
        return
    logger_name = f"aea.packages.{configuration.author}.{configuration.component_type.to_plural()}.{configuration.name}"
    logger = AgentLoggerAdapter(logging.getLogger(logger_name), agent_name)
    component.logger = logger


# TODO this function is repeated in 'aea.cli.utils.package_utils.py'
def _verify_or_create_private_keys(aea_project_path: Path) -> None:
    """Verify or create private keys."""
    path_to_configuration = aea_project_path / DEFAULT_AEA_CONFIG_FILE
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp_read = path_to_configuration.open(mode="r", encoding="utf-8")
    agent_configuration = agent_loader.load(fp_read)

    for identifier, _value in agent_configuration.private_key_paths.read_all():
        if identifier not in crypto_registry.supported_ids:
            raise ValueError(f"Item not registered with id '{identifier}'.")

    for identifier, private_key_path in IDENTIFIER_TO_KEY_FILES.items():
        config_private_key_path = agent_configuration.private_key_paths.read(identifier)
        if config_private_key_path is None:
            create_private_key(
                identifier, private_key_file=str(aea_project_path / private_key_path)
            )
            agent_configuration.private_key_paths.update(identifier, private_key_path)
        else:
            try:
                try_validate_private_key_path(
                    identifier,
                    str(aea_project_path / private_key_path),
                    exit_on_error=False,
                )
            except FileNotFoundError:  # pragma: no cover
                logger.error(
                    "File {} for private key {} not found.".format(
                        repr(private_key_path), identifier,
                    )
                )
                raise

    fp_write = path_to_configuration.open(mode="w", encoding="utf-8")
    agent_loader.dump(agent_configuration, fp_write)
