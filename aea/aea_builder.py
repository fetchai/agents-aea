# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import ast
import logging
import logging.config
import os
import pprint
import subprocess  # nosec
import sys
from collections import defaultdict
from copy import deepcopy
from importlib import import_module
from pathlib import Path
from typing import Any, Collection, Dict, List, Optional, Set, Tuple, Type, Union, cast

import jsonschema
from packaging.specifiers import SpecifierSet

from aea.aea import AEA
from aea.common import PathLike
from aea.components.base import Component, load_aea_package
from aea.components.loader import load_component_from_config
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    Dependencies,
    PackageType,
    ProtocolConfig,
    PublicId,
    SkillConfig,
)
from aea.configurations.constants import (
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_ENV_DOTFILE,
    DEFAULT_LEDGER,
    DEFAULT_LOGGING_CONFIG,
    DEFAULT_REGISTRY_NAME,
)
from aea.configurations.constants import (
    DEFAULT_SEARCH_SERVICE_ADDRESS as _DEFAULT_SEARCH_SERVICE_ADDRESS,
)
from aea.configurations.constants import (
    DOTTED_PATH_MODULE_ELEMENT_SEPARATOR,
    PROTOCOLS,
    SIGNING_PROTOCOL,
    SKILLS,
)
from aea.configurations.data_types import PackageIdPrefix
from aea.configurations.loader import ConfigLoader, load_component_configuration
from aea.configurations.manager import (
    AgentConfigManager,
    find_component_directory_from_component_id,
)
from aea.configurations.pypi import (
    is_satisfiable,
    merge_dependencies,
    merge_dependencies_list,
)
from aea.configurations.validation import ExtraPropertiesError
from aea.crypto.helpers import private_key_verify
from aea.crypto.ledger_apis import DEFAULT_CURRENCY_DENOMINATIONS
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMakerHandler
from aea.error_handler.base import AbstractErrorHandler
from aea.exceptions import (
    AEAException,
    AEAValidationError,
    AEAWalletNoAddressException,
    enforce,
)
from aea.helpers.base import (
    SimpleId,
    find_topological_order,
    load_env_file,
    load_module,
)
from aea.helpers.dependency_tree import DependencyTree
from aea.helpers.env_vars import apply_env_variables
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.helpers.install_dependency import install_dependency
from aea.helpers.io import open_file
from aea.helpers.logging import AgentLoggerAdapter, WithLogger, get_logger
from aea.identity.base import Identity
from aea.registries.resources import Resources


_default_logger = logging.getLogger(__name__)


class _DependenciesManager:
    """Class to manage dependencies of agent packages."""

    def __init__(self) -> None:
        """Initialize the dependency graph."""
        # adjacency list of the dependency DAG
        # an arc means "depends on"
        self._dependencies = {}  # type: Dict[ComponentId, ComponentConfiguration]
        self._all_dependencies_by_type = (
            {}
        )  # type: Dict[ComponentType, Dict[ComponentId, ComponentConfiguration]]
        self._prefix_to_components = {}  # type: Dict[PackageIdPrefix, Set[ComponentId]]
        self._inverse_dependency_graph = {}  # type: Dict[ComponentId, Set[ComponentId]]

        self.agent_pypi_dependencies: Dependencies = {}

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
        Add a component to the dependency manager.

        :param configuration: the component configuration to add.
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

    def remove_component(self, component_id: ComponentId) -> None:
        """
        Remove a component.

        :param component_id: the component id
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
        all_pypi_dependencies = merge_dependencies_list(
            self.agent_pypi_dependencies,
            *[
                configuration.pypi_dependencies
                for configuration in self._dependencies.values()
            ],
        )
        return all_pypi_dependencies

    def install_dependencies(self) -> None:
        """Install extra dependencies for components."""
        for name, d in self.pypi_dependencies.items():
            install_dependency(name, d, _default_logger)


class AEABuilder(WithLogger):  # pylint: disable=too-many-public-methods
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

    DEFAULT_LEDGER = DEFAULT_LEDGER
    DEFAULT_CURRENCY_DENOMINATIONS = DEFAULT_CURRENCY_DENOMINATIONS
    DEFAULT_AGENT_ACT_PERIOD = 0.05  # seconds
    DEFAULT_EXECUTION_TIMEOUT = 0
    DEFAULT_MAX_REACTIONS = 20
    DEFAULT_SKILL_EXCEPTION_POLICY = ExceptionPolicyEnum.propagate
    DEFAULT_CONNECTION_EXCEPTION_POLICY = ExceptionPolicyEnum.propagate
    DEFAULT_LOOP_MODE = "async"
    DEFAULT_RUNTIME_MODE = "threaded"
    DEFAULT_TASKMANAGER_MODE = "threaded"
    DEFAULT_SEARCH_SERVICE_ADDRESS = _DEFAULT_SEARCH_SERVICE_ADDRESS
    AEA_CLASS = AEA
    BUILD_TIMEOUT = 120
    loader = ConfigLoader.from_configuration_type(PackageType.AGENT)

    # pylint: disable=attribute-defined-outside-init

    def __init__(
        self,
        with_default_packages: bool = True,
        registry_dir: str = DEFAULT_REGISTRY_NAME,
        build_dir_root: Optional[str] = None,
    ) -> None:
        """
        Initialize the builder.

        :param with_default_packages: add the default packages.
        :param registry_dir: the registry directory.
        :param build_dir_root: the root of the build directory.
        """
        WithLogger.__init__(self, logger=_default_logger)
        self.registry_dir = os.path.join(os.getcwd(), registry_dir)
        self._with_default_packages = with_default_packages
        self.build_dir_root = build_dir_root
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
        """
        self._reset(is_full_reset)

    def _reset(self, is_full_reset: bool = False) -> None:
        """
        Reset the builder (private usage).

        :param is_full_reset: whether it is a full reset or not.
        """
        self._name: Optional[str] = None
        self._private_key_paths: Dict[str, Optional[str]] = {}
        self._connection_private_key_paths: Dict[str, Optional[str]] = {}
        if not is_full_reset:
            self._remove_components_from_dependency_manager()
        self._component_instances: Dict[
            ComponentType, Dict[ComponentConfiguration, Component]
        ] = {
            ComponentType.CONNECTION: {},
            ComponentType.CONTRACT: {},
            ComponentType.PROTOCOL: {},
            ComponentType.SKILL: {},
        }
        self._custom_component_configurations: Dict[ComponentId, Dict] = {}
        self._to_reset: bool = False
        self._build_called: bool = False
        if not is_full_reset:
            return
        self._default_ledger: Optional[str] = None
        self._required_ledgers: Optional[List[str]] = None
        self._build_entrypoint: Optional[str] = None
        self._currency_denominations: Dict[str, str] = {}
        self._default_connection: Optional[PublicId] = None
        self._context_namespace: Dict[str, Any] = {}
        self._period: Optional[float] = None
        self._execution_timeout: Optional[float] = None
        self._max_reactions: Optional[int] = None
        self._decision_maker_handler_class: Optional[Type[DecisionMakerHandler]] = None
        self._decision_maker_handler_dotted_path: Optional[str] = None
        self._decision_maker_handler_file_path: Optional[str] = None
        self._decision_maker_handler_config: Optional[Dict[str, Any]] = None
        self._error_handler_class: Optional[Type[AbstractErrorHandler]] = None
        self._error_handler_dotted_path: Optional[str] = None
        self._error_handler_file_path: Optional[str] = None
        self._error_handler_config: Optional[Dict[str, Any]] = None
        self._skill_exception_policy: Optional[ExceptionPolicyEnum] = None
        self._connection_exception_policy: Optional[ExceptionPolicyEnum] = None
        self._default_routing: Dict[PublicId, PublicId] = {}
        self._loop_mode: Optional[str] = None
        self._runtime_mode: Optional[str] = None
        self._task_manager_mode: Optional[str] = None
        self._search_service_address: Optional[str] = None
        self._storage_uri: Optional[str] = None
        self._data_dir: Optional[str] = None
        self._logging_config: Dict = DEFAULT_LOGGING_CONFIG

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

    def set_period(self, period: Optional[float]) -> "AEABuilder":
        """
        Set agent act period.

        :param period: period in seconds

        :return: self
        """
        self._period = period
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

    def set_decision_maker_handler_details(
        self,
        decision_maker_handler_dotted_path: str,
        file_path: str,
        config: Dict[str, Any],
    ) -> "AEABuilder":
        """
        Set error handler details.

        :param decision_maker_handler_dotted_path: the dotted path to the decision maker handler
        :param file_path: the file path to the file which contains the decision maker handler
        :param config: the configuration passed to the decision maker handler on instantiation

        :return: self
        """
        self._decision_maker_handler_dotted_path = decision_maker_handler_dotted_path
        self._decision_maker_handler_file_path = file_path
        self._decision_maker_handler_config = config
        return self

    def _load_decision_maker_handler_class(
        self,
    ) -> Optional[Type[DecisionMakerHandler]]:
        """
        Load decision maker handler class.

        :return: decision maker handler class
        """
        _class = self._get_decision_maker_handler_class()
        if _class is not None and self._decision_maker_handler_dotted_path is not None:
            raise ValueError(  # pragma: nocover
                "DecisionMakerHandler class and dotted path set: can only set one!"
            )
        if _class is not None:
            return _class  # pragma: nocover
        if self._decision_maker_handler_dotted_path is None:
            return None
        dotted_path, class_name = self._decision_maker_handler_dotted_path.split(
            DOTTED_PATH_MODULE_ELEMENT_SEPARATOR
        )
        try:
            if self._decision_maker_handler_file_path is None:
                module = import_module(dotted_path)
            else:
                module = load_module(
                    dotted_path, Path(self._decision_maker_handler_file_path)
                )
        except Exception as e:  # pragma: nocover
            self.logger.error(
                "Could not locate decision maker handler for dotted path '{}' and file path '{}'. Error message: {}".format(
                    dotted_path, self._decision_maker_handler_file_path, e
                )
            )
            raise  # log and re-raise because we should not build an agent from an invalid configuration

        try:
            _class = getattr(module, class_name)
        except Exception as e:  # pragma: nocover
            self.logger.error(
                "Could not locate decision maker handler for dotted path '{}', class name '{}' and file path '{}'. Error message: {}".format(
                    dotted_path, class_name, self._decision_maker_handler_file_path, e
                )
            )
            raise  # log and re-raise because we should not build an agent from an invalid configuration

        return _class

    def _load_error_handler_class(
        self,
    ) -> Optional[Type[AbstractErrorHandler]]:
        """
        Load error handler class.

        :return: error handler class
        """
        _class = self._get_error_handler_class()
        if _class is not None and self._error_handler_dotted_path is not None:
            raise ValueError(  # pragma: nocover
                "ErrorHandler class and dotted path set: can only set one!"
            )
        if _class is not None:
            return _class  # pragma: nocover
        if self._error_handler_dotted_path is None:
            return None
        dotted_path, class_name = self._error_handler_dotted_path.split(
            DOTTED_PATH_MODULE_ELEMENT_SEPARATOR
        )
        try:
            if self._error_handler_file_path is None:
                module = import_module(dotted_path)
            else:
                module = load_module(dotted_path, Path(self._error_handler_file_path))
        except Exception as e:  # pragma: nocover
            self.logger.error(
                "Could not locate error handler for dotted path '{}' and file path '{}'. Error message: {}".format(
                    dotted_path, self._error_handler_file_path, e
                )
            )
            raise  # log and re-raise because we should not build an agent from an invalid configuration

        try:
            _class = getattr(module, class_name)
        except Exception as e:  # pragma: nocover
            self.logger.error(
                "Could not locate error handler for dotted path '{}', class name '{}' and file path '{}'. Error message: {}".format(
                    dotted_path, class_name, self._error_handler_file_path, e
                )
            )
            raise  # log and re-raise because we should not build an agent from an invalid configuration

        return _class

    def set_error_handler_details(
        self, error_handler_dotted_path: str, file_path: str, config: Dict[str, Any]
    ) -> "AEABuilder":
        """
        Set error handler details.

        :param error_handler_dotted_path: the dotted path to the error handler
        :param file_path: the file path to the file which contains the error handler
        :param config: the configuration passed to the error handler on instantiation

        :return: self
        """
        self._error_handler_dotted_path = error_handler_dotted_path
        self._error_handler_file_path = file_path
        self._error_handler_config = config
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

    def set_connection_exception_policy(
        self, connection_exception_policy: Optional[ExceptionPolicyEnum]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set connection exception policy.

        :param connection_exception_policy: the policy

        :return: self
        """
        self._connection_exception_policy = connection_exception_policy
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
        for protocol_id, connection_id in default_routing.items():
            if (
                ComponentId("protocol", protocol_id)
                not in self._package_dependency_manager.protocols
            ):
                raise ValueError(
                    f"Protocol {protocol_id} specified in `default_routing` is not a project dependency!"
                )
            if (
                ComponentId("connection", connection_id)
                not in self._package_dependency_manager.connections
            ):
                raise ValueError(
                    f"Connection {connection_id} specified in `default_routing` is not a project dependency!"
                )

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

    def set_task_manager_mode(
        self, task_manager_mode: Optional[str]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the task_manager_mode.

        :param task_manager_mode: the agent task_manager_mode
        :return: self
        """
        self._task_manager_mode = task_manager_mode
        return self

    def set_storage_uri(
        self, storage_uri: Optional[str]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the storage uri.

        :param storage_uri: storage uri
        :return: self
        """
        self._storage_uri = storage_uri
        return self

    def set_data_dir(self, data_dir: Optional[str]) -> "AEABuilder":  # pragma: nocover
        """
        Set the data directory.

        :param data_dir: path to directory where to store data.
        :return: self
        """
        self._data_dir = data_dir
        return self

    def set_logging_config(
        self, logging_config: Dict
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the logging configurations.

        The dictionary must satisfy the following schema:

          https://docs.python.org/3/library/logging.config.html#logging-config-dictschema

        :param logging_config: the logging configurations.
        :return: self
        """
        self._logging_config = logging_config
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
        # add signing protocol
        signing_protocol = PublicId.from_str(SIGNING_PROTOCOL)
        self.add_protocol(
            Path(
                self.registry_dir,
                signing_protocol.author,
                PROTOCOLS,
                signing_protocol.name,
            )
        )

    def _check_can_remove(self, component_id: ComponentId) -> None:
        """
        Check if a component can be removed.

        :param component_id: the component id.
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
        self, public_id: Optional[PublicId] = None
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the default connection.

        :param public_id: the public id of the default connection package.
        :return: the AEABuilder
        """
        if (
            public_id
            and ComponentId("connection", public_id)
            not in self._package_dependency_manager.connections
        ):
            raise ValueError(
                f"Connection {public_id} specified as `default_connection` is not a project dependency!"
            )
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

    def set_default_ledger(
        self, identifier: Optional[str]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set a default ledger API to use.

        :param identifier: the identifier of the ledger api
        :return: the AEABuilder
        """
        self._default_ledger = (
            str(SimpleId(identifier)) if identifier is not None else None
        )
        return self

    def set_required_ledgers(
        self, required_ledgers: Optional[List[str]]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the required ledger identifiers.

        These are the ledgers for which the AEA requires a key pair.

        :param required_ledgers: the required ledgers.
        :return: the AEABuilder.
        """
        self._required_ledgers = (
            [str(SimpleId(ledger)) for ledger in required_ledgers]
            if required_ledgers is not None
            else None
        )
        return self

    def set_build_entrypoint(
        self, build_entrypoint: Optional[str]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set build entrypoint.

        :param build_entrypoint: path to the builder script.
        :return: the AEABuilder
        """
        self._build_entrypoint = build_entrypoint
        return self

    def set_currency_denominations(
        self, currency_denominations: Dict[str, str]
    ) -> "AEABuilder":  # pragma: nocover
        """
        Set the mapping from ledger ids to currency denominations.

        :param currency_denominations: the mapping
        :return: the AEABuilder
        """
        self._currency_denominations = currency_denominations
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
        :raises AEAException: if a component is already registered with the same component id.   # noqa: DAR402
                            | or if there's a missing dependency.  # noqa: DAR402
        :return: the AEABuilder
        """
        directory = Path(directory)
        configuration = load_component_configuration(
            component_type, directory, skip_consistency_check
        )
        self._set_component_build_directory(configuration)
        self._check_can_add(configuration)
        # update dependency graph
        self._package_dependency_manager.add_component(configuration)
        configuration.directory = directory

        return self

    def _set_component_build_directory(
        self, configuration: ComponentConfiguration
    ) -> None:
        """
        Set component build directory, create if not presents.

        :param configuration: component configuration
        """
        configuration.build_directory = os.path.join(
            self.get_build_root_directory(),
            configuration.component_type.value,
            configuration.author,
            configuration.name,
        )

    def add_component_instance(self, component: Component) -> "AEABuilder":
        """
        Add already initialized component object to resources or connections.

        Please, pay attention, all dependencies have to be already loaded.

        Notice also that this will make the call to 'build()' non re-entrant.
        You will have to `reset()` the builder before calling `build()` again.

        :param component: Component instance already initialized.
        :return: self
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

    def set_agent_pypi_dependencies(self, dependencies: Dependencies) -> "AEABuilder":
        """
        Set agent PyPI dependencies.

        :param dependencies: PyPI dependencies for the agent.
        :return: the AEABuilder.
        """
        self._package_dependency_manager.agent_pypi_dependencies = dependencies
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

    def _remove(self, component_id: ComponentId) -> None:
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

    def call_all_build_entrypoints(self) -> None:
        """Call all the build entrypoints."""
        for config in self._package_dependency_manager._dependencies.values():  # type: ignore # pylint: disable=protected-access
            self.run_build_for_component_configuration(config, logger=self.logger)

        target_directory = self.get_build_root_directory()

        if self._build_entrypoint:
            self.logger.info("Building AEA package...")
            source_directory = "."
            build_entrypoint = cast(str, self._build_entrypoint)
            self._run_build_entrypoint(
                build_entrypoint, source_directory, target_directory, logger=self.logger
            )

    def get_build_root_directory(self) -> str:
        """Get build directory root."""
        return os.path.join(self.build_dir_root or ".", self.AEA_CLASS.get_build_dir())

    @classmethod
    def run_build_for_component_configuration(
        cls,
        config: ComponentConfiguration,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Run a build entrypoint script for component configuration."""
        if not config.build_entrypoint:
            return

        enforce(bool(config.build_directory), f"{config}.build_directory is not set!")

        if not config.build_directory:  # pragma: nocover
            return

        if logger:
            logger.info(f"Building package {config.component_id}...")

        source_directory = cast(str, config.directory)
        target_directory = os.path.abspath(config.build_directory)
        build_entrypoint = cast(str, config.build_entrypoint)
        cls._run_build_entrypoint(
            build_entrypoint, source_directory, target_directory, logger=logger
        )

    @classmethod
    def _run_build_entrypoint(
        cls,
        build_entrypoint: str,
        source_directory: str,
        target_directory: str,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Run a build entrypoint script.

        :param build_entrypoint: the path to the build script relative to directory.
        :param source_directory: the source directory.
        :param target_directory: the target directory.
        :param logger: logger
        """
        cls._check_valid_entrypoint(build_entrypoint, source_directory)

        command = [sys.executable, build_entrypoint, target_directory]
        command_str = " ".join(command)
        if logger:
            logger.info(f"Running command '{command_str}'...")
        stdout, stderr, code = cls._run_in_subprocess(command, source_directory)
        if code == 0:
            if logger:
                logger.info(f"Command '{command_str}' succeded with output:\n{stdout}")
        else:
            raise AEAException(
                f"An error occurred while running command '{command_str}':\n{stderr}"
            )

    @classmethod
    def _run_in_subprocess(
        cls, command: List[str], source_directory: str
    ) -> Tuple[str, str, int]:
        """
        Run in subprocess.

        :param command: command to run
        :param source_directory: source directory
        :return: stdout, stderr, code
        """
        res = subprocess.run(  # nosec
            command,
            cwd=source_directory,
            check=False,
            timeout=cls.BUILD_TIMEOUT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        code = res.returncode
        stdout = res.stdout.decode("utf-8")
        stderr = res.stderr.decode("utf-8")
        return stdout, stderr, code

    def _build_wallet(
        self, data_directory: str, password: Optional[str] = None
    ) -> Wallet:
        """
        Build the wallet.

        We need to prepend the path to the data directory
        to each private key path, but only if
        the path is not an absolute path.

        :param data_directory: the path prefix to be prepended to each private key path.
        :param password: the password to encrypt/decrypt the private key.
        :return: the wallet instance.
        """

        def _prepend_if_not_none(
            obj: Dict[str, Optional[str]]
        ) -> Dict[str, Optional[str]]:
            return {
                key: os.path.join(data_directory, value)
                if value is not None and not os.path.isabs(value)
                else value
                for key, value in obj.items()
            }

        private_key_paths = _prepend_if_not_none(self.private_key_paths)
        connection_private_key_paths = _prepend_if_not_none(
            self.connection_private_key_paths
        )
        wallet = Wallet(
            private_key_paths, connection_private_key_paths, password=password
        )
        return wallet

    def _build_identity_from_wallet(self, wallet: Wallet) -> Identity:
        """
        Get the identity associated to a wallet.

        :param wallet: the wallet
        :return: the identity
        """
        if self._name is None:  # pragma: nocover
            raise ValueError("You must set the name of the agent.")

        default_ledger = self.get_default_ledger()
        if not wallet.addresses:
            raise AEAWalletNoAddressException("Wallet has no addresses.")

        if default_ledger not in wallet.addresses:
            raise ValueError(  # pragma: nocover
                f"Specified default ledger '{default_ledger}' not found in available addresses of types: {'[' + ','.join(wallet.addresses.keys()) + ']'}"
            )

        if len(wallet.addresses) > 1:
            identity = Identity(
                self._name,
                addresses=wallet.addresses,
                public_keys=wallet.public_keys,
                default_address_key=default_ledger,
            )
        else:
            identity = Identity(
                self._name,
                address=wallet.addresses[default_ledger],
                public_key=wallet.public_keys[default_ledger],
                default_address_key=default_ledger,
            )
        return identity

    def _process_connection_ids(  # pylint: disable=unsubscriptable-object
        self,
        connection_ids: Optional[Collection[PublicId]] = None,
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

        if len(selected_connections_ids) == 0:
            return selected_connections_ids
        # sort default id to be first
        default_connection = self._get_default_connection()
        if default_connection is None:
            return []
        full_default_connection_id = [
            connection_id
            for connection_id in selected_connections_ids
            if connection_id.same_prefix(default_connection)
        ]
        if len(full_default_connection_id) == 1:
            selected_connections_ids.remove(full_default_connection_id[0])
            sorted_selected_connections_ids = (
                full_default_connection_id + selected_connections_ids
            )
        else:
            raise ValueError(
                "Default connection not a dependency. Please add it and retry."
            )

        return sorted_selected_connections_ids

    def install_pypi_dependencies(self) -> None:
        """Install components extra dependencies."""
        self._package_dependency_manager.install_dependencies()

    def build(  # pylint: disable=unsubscriptable-object
        self,
        connection_ids: Optional[Collection[PublicId]] = None,
        password: Optional[str] = None,
    ) -> AEA:
        """
        Build the AEA.

        This method is re-entrant only if the components have been
        added through the method 'add_component'. If some of them
        have been loaded with 'add_component_instance', it
        can be called only once, and further calls are only possible
        after a call to 'reset' and re-loading of the components added
        via 'add_component_instance' and the private keys.

        :param connection_ids: select only these connections to run the AEA.
        :param password: the password to encrypt/decrypt the private key.
        :return: the AEA object.
        """
        datadir = self._get_data_dir()
        self._check_we_can_build()
        self._preliminary_checks_before_build()
        logging.config.dictConfig(self._logging_config)
        wallet = self._build_wallet(datadir, password=password)
        identity = self._build_identity_from_wallet(wallet)
        resources = Resources(identity.name)
        self._load_and_add_components(ComponentType.PROTOCOL, resources, identity.name)
        self._load_and_add_components(ComponentType.CONTRACT, resources, identity.name)
        self._load_and_add_components(
            ComponentType.CONNECTION,
            resources,
            identity.name,
            identity=identity,
            crypto_store=wallet.connection_cryptos,
            data_dir=datadir,
        )
        connection_ids = self._process_connection_ids(connection_ids)
        aea = self.AEA_CLASS(
            identity,
            wallet,
            resources,
            datadir,
            loop=None,
            period=self._get_agent_act_period(),
            execution_timeout=self._get_execution_timeout(),
            max_reactions=self._get_max_reactions(),
            error_handler_class=self._load_error_handler_class(),
            error_handler_config=self._get_error_handler_config(),
            decision_maker_handler_class=self._load_decision_maker_handler_class(),
            decision_maker_handler_config=self._get_decision_maker_handler_config(),
            skill_exception_policy=self._get_skill_exception_policy(),
            connection_exception_policy=self._get_connection_exception_policy(),
            currency_denominations=self._get_currency_denominations(),
            default_routing=self._get_default_routing(),
            default_connection=self._get_default_connection(),
            loop_mode=self._get_loop_mode(),
            runtime_mode=self._get_runtime_mode(),
            task_manager_mode=self._get_task_manager_mode(),
            connection_ids=connection_ids,
            search_service_address=self._get_search_service_address(),
            storage_uri=self._get_storage_uri(),
            **deepcopy(self._context_namespace),
        )
        self._load_and_add_components(
            ComponentType.SKILL, resources, identity.name, agent_context=aea.context
        )
        self._build_called = True
        return aea

    def get_default_ledger(self) -> str:
        """
        Return default ledger.

        :return: the default ledger identifier.
        """
        return self._default_ledger or self.DEFAULT_LEDGER

    def get_required_ledgers(self) -> List[str]:
        """
        Get the required ledger identifiers.

        These are the ledgers for which the AEA requires a key pair.

        :return: the list of required ledgers.
        """
        return self._required_ledgers or [self.DEFAULT_LEDGER]

    def _get_agent_act_period(self) -> float:
        """
        Return agent act period.

        :return: period in seconds if set else default value.
        """
        return self._period or self.DEFAULT_AGENT_ACT_PERIOD

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

    def _get_error_handler_class(
        self,
    ) -> Optional[Type]:
        """
        Return the error handler class.

        :return: error handler class
        """
        return self._error_handler_class

    def _get_error_handler_config(
        self,
    ) -> Optional[Dict[str, Any]]:
        """
        Return the error handler config.

        :return: error handler config
        """
        return self._error_handler_config

    def _get_decision_maker_handler_class(
        self,
    ) -> Optional[Type[DecisionMakerHandler]]:
        """
        Return the decision maker handler class.

        :return: decision maker handler class
        """
        return self._decision_maker_handler_class

    def _get_decision_maker_handler_config(
        self,
    ) -> Optional[Dict[str, Any]]:
        """
        Return the decision maker handler config.

        :return: decision maker handler config
        """
        return self._decision_maker_handler_config

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

    def _get_connection_exception_policy(self) -> ExceptionPolicyEnum:
        """
        Return the skill exception policy.

        :return: the skill exception policy.
        """
        return (
            self._connection_exception_policy
            if self._connection_exception_policy is not None
            else self.DEFAULT_CONNECTION_EXCEPTION_POLICY
        )

    def _get_currency_denominations(self) -> Dict[str, str]:
        """
        Return the mapping from ledger id to currency denominations.

        :return: the mapping
        """
        return (
            self._currency_denominations
            if self._currency_denominations != {}
            else self.DEFAULT_CURRENCY_DENOMINATIONS
        )

    def _get_default_routing(self) -> Dict[PublicId, PublicId]:
        """
        Return the default routing.

        :return: the default routing
        """
        return self._default_routing

    def _get_default_connection(self) -> Optional[PublicId]:
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

    def _get_task_manager_mode(self) -> str:
        """
        Return the askmanager mode name.

        :return: the taskmanager mode name
        """
        return (
            self._task_manager_mode
            if self._task_manager_mode is not None
            else self.DEFAULT_TASKMANAGER_MODE
        )

    def _get_storage_uri(self) -> Optional[str]:
        """
        Return the storage uri.

        :return: the storage uri
        """
        return self._storage_uri

    def _get_data_dir(self) -> str:
        """
        Return the data directory.

        :return: the data directory.
        """
        return self._data_dir if self._data_dir is not None else os.getcwd()

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

        :param configuration: the component configuration being added
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

        :param configuration: the component configuration
        :raises AEAException: if there's a missing dependency.
        """

        not_supported_packages = {
            dep.without_hash() for dep in configuration.package_dependencies
        }.difference(
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

    def _check_pypi_dependencies(self, configuration: ComponentConfiguration) -> None:
        """
        Check that PyPI dependencies of a package don't conflict with the existing ones.

        :param configuration: the component configuration.
        :raises AEAException: if some PyPI dependency is conflicting.
        """
        all_pypi_dependencies = self._package_dependency_manager.pypi_dependencies
        all_pypi_dependencies = merge_dependencies(
            all_pypi_dependencies, configuration.pypi_dependencies
        )
        for pkg_name, dep_info in all_pypi_dependencies.items():
            set_specifier = SpecifierSet(dep_info.version)
            if not is_satisfiable(set_specifier):
                raise AEAException(
                    f"Conflict on package {pkg_name}: specifier set '{dep_info.version}' not satisfiable."
                )

    @staticmethod
    def check_project_dependencies(
        agent_configuration: AgentConfig, project_path: Path
    ) -> None:
        """Check project config for missing dependencies."""

        dep_tree: Set[ComponentId] = set()
        for level in DependencyTree.generate(project_path, from_project=True):
            dep_tree.update(
                {
                    ComponentId(package.package_type.value, package.public_id)
                    for package in level
                    if package.package_type != PackageType.AGENT
                }
            )

        available_components = {
            component.without_hash()
            for component in agent_configuration.all_components_id
        }

        missing_dependencies_from_config = dep_tree - available_components
        enforce(
            len(missing_dependencies_from_config) == 0,
            f"Following dependencies are present in the project but missing from the aea-config.yaml; {missing_dependencies_from_config}",
        )

    @classmethod
    def try_to_load_agent_configuration_file(
        cls,
        aea_project_path: Union[str, Path],
        apply_environment_variables: bool = True,
    ) -> AgentConfig:
        """Try to load the agent configuration file.."""
        try:
            aea_project_path = Path(aea_project_path)
            configuration_file_path = cls.get_configuration_file_path(aea_project_path)
            with open_file(configuration_file_path, mode="r", encoding="utf-8") as fp:
                loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
                agent_configuration = loader.load(fp)
                if apply_environment_variables:
                    agent_configuration = apply_env_variables(
                        agent_configuration, os.environ
                    )
                cls.check_project_dependencies(agent_configuration, aea_project_path)
                return agent_configuration
        except FileNotFoundError:  # pragma: nocover
            raise ValueError(
                "Agent configuration file '{}' not found in the current directory.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
        except (
            AEAValidationError,
            jsonschema.exceptions.ValidationError,
            ExtraPropertiesError,
        ) as e:  # pragma: nocover
            raise AEAValidationError(
                "Agent configuration file '{}' is invalid: `{}`. Please check the documentation.".format(
                    DEFAULT_AEA_CONFIG_FILE, str(e)
                )
            )

    @staticmethod
    def _check_valid_entrypoint(build_entrypoint: str, directory: str) -> None:
        """
        Check a configuration has a valid entrypoint.

        :param build_entrypoint: the build entrypoint.
        :param directory: the directory from where to start reading the script.
        """
        enforce(
            build_entrypoint is not None,
            "Package has not a build entrypoint specified.",
        )
        build_entrypoint = cast(str, build_entrypoint)
        script_path = Path(directory) / build_entrypoint
        enforce(
            script_path.exists(),
            f"File '{build_entrypoint}' does not exists.",
        )
        enforce(
            script_path.is_file(),
            f"'{build_entrypoint}' is not a file.",
        )
        try:
            ast.parse(script_path.read_text())
        except SyntaxError as e:
            message = f"{str(e)}: {e.text}"
            raise AEAException(
                f"The Python script at '{build_entrypoint}' has a syntax error: {message}"
            ) from e

    def set_from_configuration(
        self,
        agent_configuration: AgentConfig,
        aea_project_path: Path,
        skip_consistency_check: bool = False,
    ) -> None:
        """
        Set builder variables from AgentConfig.

        :param agent_configuration: AgentConfig to get values from.
        :param aea_project_path: PathLike root directory of the agent project.
        :param skip_consistency_check: if True, the consistency check are skipped.
        """
        # set name and other configurations
        self.set_name(agent_configuration.name)
        self.set_default_ledger(agent_configuration.default_ledger)
        self.set_required_ledgers(agent_configuration.required_ledgers)
        self.set_build_entrypoint(agent_configuration.build_entrypoint)
        self.set_currency_denominations(agent_configuration.currency_denominations)

        self.set_period(agent_configuration.period)
        self.set_execution_timeout(agent_configuration.execution_timeout)
        self.set_max_reactions(agent_configuration.max_reactions)

        if agent_configuration.decision_maker_handler != {}:
            dotted_path = agent_configuration.decision_maker_handler["dotted_path"]
            file_path = agent_configuration.decision_maker_handler["file_path"]
            config = agent_configuration.decision_maker_handler["config"]
            self.set_decision_maker_handler_details(dotted_path, file_path, config)
        if agent_configuration.error_handler != {}:
            dotted_path = agent_configuration.error_handler["dotted_path"]
            file_path = agent_configuration.error_handler["file_path"]
            config = agent_configuration.error_handler["config"]
            self.set_error_handler_details(dotted_path, file_path, config)
        if agent_configuration.skill_exception_policy is not None:
            self.set_skill_exception_policy(
                ExceptionPolicyEnum(agent_configuration.skill_exception_policy)
            )
        if agent_configuration.connection_exception_policy is not None:
            self.set_connection_exception_policy(
                ExceptionPolicyEnum(agent_configuration.connection_exception_policy)
            )

        self.set_loop_mode(agent_configuration.loop_mode)
        self.set_runtime_mode(agent_configuration.runtime_mode)
        self.set_task_manager_mode(agent_configuration.task_manager_mode)
        self.set_storage_uri(agent_configuration.storage_uri)
        self.set_data_dir(agent_configuration.data_dir)
        self.set_logging_config(agent_configuration.logging_config)

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

        for component_type in [
            ComponentType.PROTOCOL,
            ComponentType.CONTRACT,
            ComponentType.CONNECTION,
            ComponentType.SKILL,
        ]:
            self._add_components_of_type(
                component_type,
                agent_configuration,
                aea_project_path,
                skip_consistency_check,
            )

        self._custom_component_configurations = (
            agent_configuration.component_configurations
        )

        self.set_default_connection(agent_configuration.default_connection)
        self.set_default_routing(agent_configuration.default_routing)
        self.set_agent_pypi_dependencies(agent_configuration.dependencies)

    @staticmethod
    def _find_import_order(
        component_ids: List[ComponentId],
        aea_project_path: Path,
        skip_consistency_check: bool,
    ) -> List[ComponentId]:
        """
        Find import order for skills/connections.

        We need to handle skills and connections separately, since skills/connections can depend on each other.

        That is, we need to:
        - load the skill/connection configurations to find the import order
        - detect if there are cycles
        - import skills/connections from the leaves of the dependency graph, by finding a topological ordering.

        :param component_ids: component ids to check
        :param aea_project_path: project path to AEA
        :param skip_consistency_check: consistency check of AEA
        :return: list of component ids ordered for import
        """
        # the adjacency list for the inverse dependency graph
        dependency_to_supported_dependencies: Dict[
            ComponentId, Set[ComponentId]
        ] = defaultdict(set)
        for component_id in component_ids:
            component_id = component_id.without_hash()
            component_path = find_component_directory_from_component_id(
                aea_project_path, component_id
            )
            configuration = load_component_configuration(
                component_id.component_type, component_path, skip_consistency_check
            )

            if component_id not in dependency_to_supported_dependencies:
                dependency_to_supported_dependencies[component_id] = set()
            if isinstance(configuration, SkillConfig):
                dependencies, component_type = configuration.skills, SKILLS
            elif isinstance(configuration, ConnectionConfig):
                dependencies, component_type = configuration.connections, CONNECTIONS
            elif isinstance(configuration, ContractConfig):
                dependencies, component_type = configuration.contracts, CONTRACTS
            else:
                raise AEAException("Not a valid configuration type.")  # pragma: nocover

            for dependency in dependencies:
                dependency_to_supported_dependencies[
                    ComponentId(component_type[:-1], dependency).without_hash()
                ].add(component_id)

        try:
            order = find_topological_order(dependency_to_supported_dependencies)
        except ValueError:
            raise AEAException(
                f"Cannot load {component_type}, there is a cyclic dependency."
            )

        return order

    @classmethod
    def from_aea_project(
        cls,
        aea_project_path: PathLike,
        skip_consistency_check: bool = False,
        apply_environment_variables: bool = False,
        password: Optional[str] = None,
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
        :param apply_environment_variables: if True, environment variables are loaded.
        :param password: the password to encrypt/decrypt private keys.
        :return: an AEABuilder.
        """
        aea_project_path = Path(aea_project_path)
        cls.try_to_load_agent_configuration_file(
            aea_project_path, apply_environment_variables
        )
        load_env_file(str(aea_project_path / DEFAULT_ENV_DOTFILE))

        if not apply_environment_variables:
            # check and create missing, do not replace env variables. updates config
            AgentConfigManager.verify_private_keys(
                aea_project_path,
                substitude_env_vars=False,
                private_key_helper=private_key_verify,
                password=password,
            ).dump_config()

        # just validate
        agent_configuration = AgentConfigManager.verify_private_keys(
            aea_project_path,
            substitude_env_vars=True,
            private_key_helper=private_key_verify,
            password=password,
        ).agent_config

        builder = AEABuilder(with_default_packages=False)
        builder.set_from_configuration(
            agent_configuration, aea_project_path, skip_consistency_check
        )
        return builder

    @staticmethod
    def get_configuration_file_path(aea_project_path: Union[Path, str]) -> Path:
        """Return path to aea-config file for the given AEA project path."""
        return Path(aea_project_path) / DEFAULT_AEA_CONFIG_FILE

    def _load_and_add_components(
        self,
        component_type: ComponentType,
        resources: Resources,
        agent_name: str,
        **kwargs: Any,
    ) -> None:
        """
        Load and add components added to the builder to a Resources instance.

        :param component_type: the component type for which
        :param resources: the resources object to populate.
        :param agent_name: the AEA name for logging purposes.
        :param kwargs: keyword argument to forward to the component loader.
        """
        for configuration in self._package_dependency_manager.get_components_by_type(
            component_type
        ).values():
            if configuration in self._component_instances[component_type].keys():
                component = self._component_instances[component_type][configuration]
                if configuration.component_type != ComponentType.SKILL:
                    component.logger = cast(
                        logging.Logger, make_component_logger(configuration, agent_name)
                    )
            else:
                new_configuration = self._overwrite_custom_configuration(configuration)
                if new_configuration.is_abstract_component:
                    load_aea_package(configuration)
                    self.logger.debug(
                        f"Package {configuration.public_id} of type {configuration.component_type} is abstract, "
                        f"therefore only the Python modules have been loaded."
                    )
                    continue
                _logger = make_component_logger(new_configuration, agent_name)
                component = load_component_from_config(
                    new_configuration, logger=_logger, **kwargs
                )

            resources.add_component(component)

    def _check_we_can_build(self) -> None:
        if self._build_called and self._to_reset:
            raise ValueError(
                "Cannot build the agent; You have done one of the following:\n"
                "- added a component instance;\n"
                "- added a private key manually.\n"
                "Please call 'reset() if you want to build another agent."
            )

    def _overwrite_custom_configuration(
        self, configuration: ComponentConfiguration
    ) -> ComponentConfiguration:
        """
        Overwrite custom configurations.

        It deep-copies the configuration, to avoid undesired side-effects.

        :param configuration: the configuration object.
        :return: the new configuration instance.
        """
        new_configuration = deepcopy(configuration)
        custom_config = self._custom_component_configurations.get(
            new_configuration.component_id, {}
        )
        new_configuration.update(custom_config)

        return new_configuration

    def _add_components_of_type(
        self,
        component_type: ComponentType,
        agent_configuration: AgentConfig,
        aea_project_path: Path,
        skip_consistency_check: bool,
    ) -> None:
        """
        Add components of a given type.

        :param component_type: the type of components to add.
        :param agent_configuration: the agent configuration from where to retrieve the components.
        :param aea_project_path: path to the AEA project.
        :param skip_consistency_check: if true, skip consistency checks.
        """
        public_ids = getattr(agent_configuration, component_type.to_plural())
        component_ids = [
            ComponentId(component_type, public_id) for public_id in public_ids
        ]
        if component_type in {ComponentType.PROTOCOL}:
            # if protocols or contracts, import order doesn't matter.
            import_order = component_ids
        else:
            import_order = self._find_import_order(
                component_ids, aea_project_path, skip_consistency_check
            )

        for component_id in import_order:
            component_path = find_component_directory_from_component_id(
                aea_project_path, component_id
            )
            self.add_component(
                component_id.component_type,
                component_path,
                skip_consistency_check=skip_consistency_check,
            )

    def _preliminary_checks_before_build(self) -> None:
        """
        Do consistency check on build parameters.

        - Check that the specified default ledger is in the list of specified required ledgers.
        """
        default_ledger = self.get_default_ledger()
        required_ledgers = self.get_required_ledgers()
        enforce(
            default_ledger in required_ledgers,
            exception_text=f"Default ledger '{default_ledger}' not declared in the list of required ledgers: {required_ledgers}.",
            exception_class=AEAValidationError,
        )


def make_component_logger(
    configuration: ComponentConfiguration,
    agent_name: str,
) -> Optional[logging.Logger]:
    """
    Make the logger for a component.

    :param configuration: the component configuration
    :param agent_name: the agent name
    :return: the logger.
    """
    if configuration.component_type == ComponentType.SKILL:
        # skip because skill object already have their own logger from the skill context.
        return None
    logger_name = f"aea.packages.{configuration.author}.{configuration.component_type.to_plural()}.{configuration.name}"
    _logger = AgentLoggerAdapter(get_logger(logger_name, agent_name), agent_name)
    return cast(logging.Logger, _logger)
