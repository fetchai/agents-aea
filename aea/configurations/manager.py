# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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
"""Implementation of the 'aea config' subcommand."""
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, NewType, Optional, Tuple, Union, cast

from aea.cli.utils.config import (
    _try_get_component_id_from_prefix,
    _try_get_configuration_object_from_aea_config,
    handle_dotted_path,
)
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    DEFAULT_AEA_CONFIG_FILE,
    PackageType,
)
from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA, VENDOR
from aea.configurations.loader import ConfigLoader, load_component_configuration
from aea.crypto.helpers import create_private_key, try_validate_private_key_path
from aea.crypto.registries import crypto_registry
from aea.helpers.env_vars import apply_env_variables, is_env_variable
from aea.helpers.storage.backends.base import JSON_TYPES
from aea.helpers.yaml_utils import yaml_load_all


JsonPath = List[str]
VariablePath = Union[str, JsonPath]


class VariableDoesNotExist(ValueError):
    """Variable does not exist in a config exception."""


NotExistsType = NewType("NotExistsType", object)
NotExists = NotExistsType(None)


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
        """
        self.agent_config = agent_config
        self.aea_project_directory = aea_project_directory
        self.env_vars_friendly = env_vars_friendly

    def load_component_configuration(
        self, component_id: ComponentId, skip_consistency_check: bool = True,
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
    def _get_agent_config_file_path(cls, aea_project_path) -> Path:
        """Get agent config file path for aea project path."""
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
        with cls._get_agent_config_file_path(aea_project_path).open() as fp:
            data = yaml_load_all(fp)
        return data

    def set_variable(self, path: VariablePath, value: JSON_TYPES) -> None:
        """
        Set config variable.

        :param path: str dotted path  or List[Union[ComponentId, str]]
        :param value: one of the json friendly objects.

        :return: None
        """
        component_id, json_path = self._parse_path(path)
        data = self._make_dict_for_path_and_value(json_path, value)
        overrides = {}
        if component_id:
            overrides[self.component_configurations] = {component_id: data}
        else:
            # agent
            overrides.update(data)

        self.update_config(overrides)

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
        value = json.loads(json.dumps(data))  # in case or ordered dict
        prev_key = ""
        for key in json_path:
            if not isinstance(value, dict):
                raise ValueError(f"Attribute '{prev_key}' is not a dictionary.")

            if key not in value:
                return NotExists
            value = value[key]
            prev_key = key
        return value

    def _parse_path(self, path: VariablePath) -> Tuple[Optional[ComponentId], JsonPath]:
        """
        Get component_id and json path from dotted path or list of str with first optional component id.

        :param path: dotted path str, list of str with first optional component id

        :return: Tuple of optonal component id if path related to component and List[str]
        """
        if isinstance(path, str):
            json_path, *_, component_id = handle_dotted_path(
                path, self.agent_config.author
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

    def update_config(self, overrides: Dict) -> None:
        """
        Apply overrides for agent config.

        Validates and applies agent config and component overrides.
        Does not save it on the disc!

        :param overrides: overrided values dictionary

        :return: None
        """
        for component_id, obj in overrides.get("component_configurations", {}).items():
            component_configuration = self.load_component_configuration(component_id)
            component_configuration.check_overrides_valid(
                obj, env_vars_friendly=self.env_vars_friendly
            )

        self.agent_config.update(overrides, env_vars_friendly=self.env_vars_friendly)

    def validate_current_config(self):
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
        with open(self.agent_config_file_path, "w") as file_pointer:
            ConfigLoader.from_configuration_type(PackageType.AGENT).dump(
                self.agent_config, file_pointer
            )

    @classmethod
    def verify_or_create_private_keys(
        cls,
        aea_project_path: Union[Path, str],
        exit_on_error: bool = True,
        substitude_env_vars: bool = False,
    ) -> "AgentConfigManager":
        """
        Verify or create private keys.

        Does not saves the config! Use AgentConfigManager.dump_config()

        :param aea_project_path: path to an AEA project.
        :param exit_on_error: whether we should exit the program on error.
        :param substitude_env_vars: replace env vars with values, does not dump config

        :return: the agent configuration manager.
        """
        aea_project_path = Path(aea_project_path)
        agent_config_manager = cls.load(
            aea_project_path, substitude_env_vars=substitude_env_vars
        )
        aea_conf = agent_config_manager.agent_config

        for identifier, _ in aea_conf.private_key_paths.read_all():
            if identifier not in crypto_registry.supported_ids:  # pragma: nocover
                raise ValueError(
                    "Unsupported identifier `{}` in private key paths. Supported identifiers: {}.".format(
                        identifier, sorted(crypto_registry.supported_ids)
                    )
                )

        for identifier in crypto_registry.supported_ids:
            config_private_key_path = aea_conf.private_key_paths.read(identifier)

            if is_env_variable(config_private_key_path):
                # skip env var definition
                continue

            if config_private_key_path is None:
                private_key_path = PRIVATE_KEY_PATH_SCHEMA.format(identifier)
                if identifier == aea_conf.default_ledger:  # pragma: nocover
                    if os.path.exists(private_key_path):
                        raise ValueError(
                            "File {} for private key {} already exists. Add to aea-config.yaml.".format(
                                repr(config_private_key_path), identifier
                            )
                        )
                    create_private_key(
                        identifier,
                        private_key_file=str(aea_project_path / private_key_path),
                    )
                    aea_conf.private_key_paths.update(identifier, private_key_path)
            else:
                try:
                    try_validate_private_key_path(
                        identifier,
                        str(aea_project_path / config_private_key_path),
                        exit_on_error=exit_on_error,
                    )
                except FileNotFoundError:  # pragma: no cover
                    raise ValueError(
                        "File {} for private key {} not found.".format(
                            repr(config_private_key_path), identifier,
                        )
                    )

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
