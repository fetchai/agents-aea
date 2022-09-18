# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Implementation of the AgentConfigManager."""
import json
import os
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from typing import Callable, Dict, List, NewType, Optional, Set, Tuple, Union, cast

from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    DEFAULT_AEA_CONFIG_FILE,
    PackageType,
)
from aea.configurations.constants import (
    AGENT,
    AGENTS,
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PROTOCOLS,
    SKILLS,
    VENDOR,
)
from aea.configurations.data_types import ComponentType, PackageIdPrefix, PublicId
from aea.configurations.loader import ConfigLoader, load_component_configuration
from aea.configurations.validation import SAME_MARK, filter_data
from aea.exceptions import AEAException, enforce
from aea.helpers.env_vars import apply_env_variables
from aea.helpers.io import open_file
from aea.helpers.storage.backends.base import JSON_TYPES
from aea.helpers.yaml_utils import yaml_load_all


ALLOWED_PATH_ROOTS = [
    AGENT,
    CONNECTIONS,
    CONTRACTS,
    PROTOCOLS,
    SKILLS,
    VENDOR,
]


RESOURCE_TYPE_TO_CONFIG_FILE = {
    SKILLS: DEFAULT_SKILL_CONFIG_FILE,
    PROTOCOLS: DEFAULT_PROTOCOL_CONFIG_FILE,
    CONNECTIONS: DEFAULT_CONNECTION_CONFIG_FILE,
    CONTRACTS: DEFAULT_CONTRACT_CONFIG_FILE,
}  # type: Dict[str, str]


JsonPath = List[str]
VariablePath = Union[str, JsonPath]


class VariableDoesNotExist(ValueError):
    """Variable does not exist in a config exception."""


NotExistsType = NewType("NotExistsType", object)
NotExists = NotExistsType(None)


def _try_get_configuration_object_from_aea_config(
    agent_config: AgentConfig, component_id: ComponentId
) -> Optional[Dict]:
    """
    Try to get the configuration object in the AEA config.

    The result is not guaranteed because there might not be any

    :param agent_config: the agent configuration.
    :param component_id: the component id whose prefix points to the relevant custom configuration in the AEA configuration file.
    :return: the configuration object to get/set an attribute.
    """
    if component_id is None:
        # this is the case when the prefix of the json path is 'agent'.
        return None  # pragma: nocover
    type_, author, name = (
        component_id.component_type,
        component_id.author,
        component_id.name,
    )
    component_ids = set(agent_config.component_configurations.keys())
    true_component_id = _try_get_component_id_from_prefix(
        component_ids, (type_, author, name)
    )
    if true_component_id is not None:
        return agent_config.component_configurations.get(true_component_id)
    return None


def _try_get_component_id_from_prefix(
    component_ids: Set[ComponentId], component_prefix: PackageIdPrefix
) -> Optional[ComponentId]:
    """
    Find the component id matching a component prefix.

    :param component_ids: the set of component id.
    :param component_prefix: the component prefix.
    :return: the component id that matches the prefix.
    :raises AEAEnforceError: if there are more than two components as candidate results.  # noqa: DAR402
    """
    type_, author, name = component_prefix
    results = list(
        filter(
            lambda x: x.component_type == type_
            and x.author == author
            and x.name == name,
            component_ids,
        )
    )
    if len(results) == 0:
        return None
    enforce(len(results) == 1, f"Expected only one component, found {len(results)}.")
    return results[0]


def handle_dotted_path(
    value: str,
    author: str,
    aea_project_path: Union[str, Path] = ".",
) -> Tuple[List[str], Path, ConfigLoader, Optional[ComponentId]]:
    """Separate the path between path to resource and json path to attribute.

    Allowed values:
        'agent.an_attribute_name'
        'protocols.my_protocol.an_attribute_name'
        'connections.my_connection.an_attribute_name'
        'contracts.my_contract.an_attribute_name'
        'skills.my_skill.an_attribute_name'
        'vendor.author.[protocols|contracts|connections|skills].package_name.attribute_name

    We also return the component id to retrieve the configuration of a specific
    component. Notice that at this point we don't know the version,
    so we put 'latest' as version, but later we will ignore it because
    we will filter with only the component prefix (i.e. the triple type, author and name).

    :param value: dotted path.
    :param author: the author string.
    :param aea_project_path: project path

    :return: Tuple[list of settings dict keys, filepath, config loader, component id].
    """
    parts = value.split(".")
    aea_project_path = Path(aea_project_path)

    root = parts[0]
    if root not in ALLOWED_PATH_ROOTS:
        raise AEAException(
            "The root of the dotted path must be one of: {}".format(ALLOWED_PATH_ROOTS)
        )

    if (
        len(parts) < 2
        or parts[0] == AGENT
        and len(parts) < 2
        or parts[0] == VENDOR
        and len(parts) < 5
        or parts[0] != AGENT
        and len(parts) < 3
    ):
        raise AEAException(
            "The path is too short. Please specify a path up to an attribute name."
        )

    # if the root is 'agent', stop.
    if root == AGENT:
        resource_type_plural = AGENTS
        path_to_resource_configuration = Path(DEFAULT_AEA_CONFIG_FILE)
        json_path = parts[1:]
        component_id = None
    elif root == VENDOR:
        # parse json path
        resource_author = parts[1]
        resource_type_plural = parts[2]
        resource_name = parts[3]

        # extract component id
        resource_type_singular = resource_type_plural[:-1]
        try:
            component_type = ComponentType(resource_type_singular)
        except ValueError as e:
            raise AEAException(
                f"'{resource_type_plural}' is not a valid component type. Please use one of {ComponentType.plurals()}."
            ) from e
        component_id = ComponentId(
            component_type, PublicId(resource_author, resource_name)
        )

        # find path to the resource directory
        path_to_resource_directory = (
            aea_project_path
            / VENDOR
            / resource_author
            / resource_type_plural
            / resource_name
        )
        path_to_resource_configuration = (
            path_to_resource_directory
            / RESOURCE_TYPE_TO_CONFIG_FILE[resource_type_plural]
        )
        json_path = parts[4:]
        if not path_to_resource_directory.exists():
            raise AEAException(  # pragma: nocover
                "Resource vendor/{}/{}/{} does not exist.".format(
                    resource_author, resource_type_plural, resource_name
                )
            )
    else:
        # navigate the resources of the agent to reach the target configuration file.
        resource_type_plural = root
        resource_name = parts[1]

        # extract component id
        resource_type_singular = resource_type_plural[:-1]
        component_type = ComponentType(resource_type_singular)
        resource_author = author
        component_id = ComponentId(
            component_type, PublicId(resource_author, resource_name)
        )

        # find path to the resource directory
        path_to_resource_directory = (
            aea_project_path / resource_type_plural / resource_name
        )
        path_to_resource_configuration = (
            path_to_resource_directory
            / RESOURCE_TYPE_TO_CONFIG_FILE[resource_type_plural]
        )
        json_path = parts[2:]
        if not path_to_resource_directory.exists():
            raise AEAException(
                "Resource {}/{} does not exist.".format(
                    resource_type_plural, resource_name
                )
            )

    config_loader = ConfigLoader.from_configuration_type(resource_type_plural[:-1])
    return json_path, path_to_resource_configuration, config_loader, component_id


def find_component_directory_from_component_id(
    aea_project_directory: Path, component_id: ComponentId
) -> Path:
    """Find a component directory from component id."""
    # search in vendor first
    vendor_package_path = (
        aea_project_directory
        / VENDOR
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


class AgentConfigManager:
    """AeaConfig manager."""

    component_configurations = "component_configurations"
    _loader = ConfigLoader.from_configuration_type(PackageType.AGENT)

    def __init__(
        self,
        agent_config: AgentConfig,
        aea_project_directory: Union[str, Path],
        env_vars_friendly: bool = False,
    ) -> None:
        """
        Init manager.

        :param agent_config: AgentConfig to manage.
        :param aea_project_directory: directory where project for agent_config placed.
        :param env_vars_friendly: whether or not it is env vars friendly
        """
        self.agent_config = agent_config
        self.aea_project_directory = aea_project_directory
        self.env_vars_friendly = env_vars_friendly

    def load_component_configuration(
        self,
        component_id: ComponentId,
        skip_consistency_check: bool = True,
    ) -> ComponentConfiguration:
        """
        Load component configuration from the project directory.

        :param component_id: Id of the component to load config for.
        :param skip_consistency_check: bool.

        :return: ComponentConfiguration
        """
        path = find_component_directory_from_component_id(
            aea_project_directory=Path(self.aea_project_directory),
            component_id=component_id,
        )
        return load_component_configuration(
            component_type=component_id.component_type,
            directory=path,
            skip_consistency_check=skip_consistency_check,
        )

    @property
    def agent_config_file_path(self) -> Path:
        """Return agent config file path."""
        return self._get_agent_config_file_path(self.aea_project_directory)

    @classmethod
    def _get_agent_config_file_path(cls, aea_project_path: Union[str, Path]) -> Path:
        """Get agent config file path for AEA project path."""
        return Path(aea_project_path) / DEFAULT_AEA_CONFIG_FILE

    @classmethod
    def load(
        cls, aea_project_path: Union[Path, str], substitude_env_vars: bool = False
    ) -> "AgentConfigManager":
        """Create AgentConfigManager instance from agent project path."""
        data = cls._load_config_data(Path(aea_project_path))
        if substitude_env_vars:
            data = cast(List[Dict], apply_env_variables(data, os.environ))
        agent_config = cls._loader.load_agent_config_from_json(data, validate=False)
        instance = cls(
            agent_config, aea_project_path, env_vars_friendly=not substitude_env_vars
        )
        instance.validate_current_config()
        return instance

    @classmethod
    def _load_config_data(cls, aea_project_path: Path) -> List[Dict]:
        with open_file(cls._get_agent_config_file_path(aea_project_path)) as fp:
            data = yaml_load_all(fp)
        return data

    def set_variable(self, path: VariablePath, value: JSON_TYPES) -> None:
        """
        Set config variable.

        :param path: str dotted path  or List[Union[ComponentId, str]]
        :param value: one of the json friendly objects.
        """
        component_id, json_path = self._parse_path(path)
        data = self._make_dict_for_path_and_value(json_path, value)
        overrides = {}
        if component_id:
            overrides[self.component_configurations] = {component_id: data}
        else:
            # agent
            overrides.update(data)

        dict_overrides: Optional[Dict] = None
        if isinstance(value, (dict, OrderedDict)):
            dict_overrides = {
                component_id: [
                    json_path,
                ]
            }

        self.update_config(overrides, dict_overrides=dict_overrides)

    @staticmethod
    def _make_dict_for_path_and_value(json_path: JsonPath, value: JSON_TYPES) -> Dict:
        """
        Turn json_path and value into overrides dict.

        :param json_path: List[str] represents config variable path:
        :param value: json friendly value

        :return: dict of overrides
        """
        data: Dict = {}
        nested = data
        for key in json_path[:-1]:
            nested[key] = {}
            nested = nested[key]
        nested[json_path[-1]] = value
        return data

    def get_variable(self, path: VariablePath) -> JSON_TYPES:
        """
        Set config variable.

        :param path: str dotted path or List[Union[ComponentId, str]]

        :return: json friendly value.
        """
        component_id, json_path = self._parse_path(path)

        if component_id:
            configrations_data = [
                _try_get_configuration_object_from_aea_config(
                    self.agent_config, component_id
                )
                or {},
                self.load_component_configuration(component_id).json,
            ]
        else:
            configrations_data = [self.agent_config.json]

        for data in configrations_data:
            value = self._get_value_for_json_path(data, json_path)
            if value is not NotExists:
                return cast(JSON_TYPES, value)

        raise VariableDoesNotExist(
            f"Attribute `{'.'.join(json_path)}` for {'{}({}) config'.format(component_id.component_type,component_id.public_id) if component_id else 'AgentConfig'} does not exist"
        )

    @staticmethod
    def _get_value_for_json_path(
        data: Dict, json_path: JsonPath
    ) -> Union[NotExistsType, JSON_TYPES]:
        """
        Get value by json path from the dict object.

        :param data: dict to get value from
        :param json_path: List[str]

        :return: one of the json values of NotExists if value not presents in data dict.
        """
        value = json.loads(json.dumps(data))  # in case of ordered dict doing copy
        prev_key = ""
        for key in json_path:
            if not isinstance(value, dict):
                raise ValueError(
                    f"Attribute '{prev_key}' is not a dictionary."
                )  # pragma: nocover

            if key not in value:
                return NotExists
            value = value[key]
            prev_key = key
        return value

    def _parse_path(self, path: VariablePath) -> Tuple[Optional[ComponentId], JsonPath]:
        """
        Get component_id and json path from dotted path or list of str with first optional component id.

        :param path: dotted path str, list of str with first optional component id

        :return: Tuple of optional component id if path related to component and List[str]
        """
        if isinstance(path, str):
            json_path, *_, component_id = handle_dotted_path(
                path,
                self.agent_config.author,
                aea_project_path=self.aea_project_directory,
            )
        else:  # pragma: nocover
            if isinstance(path[0], ComponentId):
                json_path = path[1:]
                component_id = path[0]
            else:
                component_id = None
                json_path = path
        if component_id:
            component_id = _try_get_component_id_from_prefix(
                set(self.agent_config.all_components_id), component_id.component_prefix
            )
        return component_id, json_path

    def update_config(
        self,
        overrides: Dict,
        dict_overrides: Optional[Dict] = None,
    ) -> None:
        """
        Apply overrides for agent config.

        Validates and applies agent config and component overrides.
        Does not save it on the disc!

        :param overrides: overridden values dictionary
        :param dict_overrides: A dictionary containing mapping for Component ID -> List of paths

        :return: None
        """
        if not overrides:
            # nothing to update
            return  # pragma: nocover

        overrides = self._filter_overrides(overrides)
        if overrides is SAME_MARK:
            # nothing to update
            return

        for component_id, obj in overrides.get("component_configurations", {}).items():
            component_configuration = self.load_component_configuration(component_id)
            component_configuration.check_overrides_valid(
                obj, env_vars_friendly=self.env_vars_friendly
            )

        self.agent_config.update(
            overrides,
            env_vars_friendly=self.env_vars_friendly,
            dict_overrides=dict_overrides,
        )

    def _filter_overrides(self, overrides: Dict) -> Dict:
        """Stay only updated values for agent config."""
        agent_overridable, components_overridables = self.get_overridables()

        agent_overridable["component_configurations"] = components_overridables

        filtered_overrides = filter_data(agent_overridable, overrides)
        return filtered_overrides

    def validate_current_config(self) -> None:
        """Check is current config valid."""
        for component_id, obj in self.agent_config.component_configurations.items():
            component_configuration = self.load_component_configuration(component_id)
            component_configuration.check_overrides_valid(
                obj, env_vars_friendly=self.env_vars_friendly
            )
        self.agent_config.validate_config_data(
            self.agent_config.json, env_vars_friendly=self.env_vars_friendly
        )

    @property
    def json(self) -> Dict:
        """Return current agent config json representation."""
        return self.agent_config.json

    def dump_config(self) -> None:
        """Save agent config on the disc."""
        config_data = self.json
        self.agent_config.validate_config_data(
            config_data, env_vars_friendly=self.env_vars_friendly
        )
        with open_file(self.agent_config_file_path, "w") as file_pointer:
            ConfigLoader.from_configuration_type(PackageType.AGENT).dump(
                self.agent_config, file_pointer
            )

    @classmethod
    def verify_private_keys(
        cls,
        aea_project_path: Union[Path, str],
        private_key_helper: Callable[[AgentConfig, Path, Optional[str]], None],
        substitude_env_vars: bool = False,
        password: Optional[str] = None,
    ) -> "AgentConfigManager":
        """
        Verify private keys.

        Does not saves the config! Use AgentConfigManager.dump_config()

        :param aea_project_path: path to an AEA project.
        :param private_key_helper: private_key_helper is a function that use agent config to check the keys
        :param substitude_env_vars: replace env vars with values, does not dump config
        :param password: the password to encrypt/decrypt the private key.

        :return: the agent configuration manager.
        """
        aea_project_path = Path(aea_project_path)
        agent_config_manager = cls.load(
            aea_project_path, substitude_env_vars=substitude_env_vars
        )
        aea_conf = agent_config_manager.agent_config
        private_key_helper(aea_conf, Path(aea_project_path), password)
        return agent_config_manager

    def get_overridables(self) -> Tuple[Dict, Dict[ComponentId, Dict]]:
        """Get config overridables."""
        agent_overridable = self.agent_config.get_overridable()

        components_overridables: Dict[ComponentId, Dict] = {}
        for component_id in self.agent_config.all_components_id:
            obj = {}
            component_config = self.load_component_configuration(
                component_id, skip_consistency_check=True
            )
            obj.update(component_config.get_overridable())
            obj.update(
                deepcopy(
                    self.agent_config.component_configurations.get(component_id, {})
                )
            )
            if obj:
                components_overridables[component_id] = obj
        return agent_overridable, components_overridables
