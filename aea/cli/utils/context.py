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
"""A module with context tools of the aea cli."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from aea.cli.utils.loggers import logger
from aea.configurations.base import (
    AgentConfig,
    Dependencies,
    PackageType,
    PublicId,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import (
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_REGISTRY_NAME,
    PROTOCOL,
    SKILL,
    VENDOR,
)
from aea.configurations.loader import ConfigLoader
from aea.configurations.pypi import merge_dependencies_list
from aea.helpers.io import open_file


class Context:
    """A class to keep configuration of the cli tool."""

    agent_config: AgentConfig

    def __init__(self, cwd: str, verbosity: str, registry_path: Optional[str]) -> None:
        """Init the context."""
        self.config = dict()  # type: Dict
        self.cwd = cwd
        self.verbosity = verbosity
        self.clean_paths: List = []
        self._registry_path = registry_path

    @property
    def registry_path(self) -> str:
        """Get registry path specified or from config or default one with check is it present."""
        # registry path is provided or in config or default
        if self._registry_path:
            registry_path = Path(self._registry_path)
            if not (registry_path.exists() and registry_path.is_dir()):
                raise ValueError(
                    f"Registry path directory provided ({self._registry_path}) can not be found. Current work dir is {self.cwd}"
                )
            return str(registry_path)

        registry_path = (Path(self.cwd) / DEFAULT_REGISTRY_NAME).absolute()
        if registry_path.is_dir():
            return str(registry_path)
        registry_path = (Path(self.cwd) / ".." / DEFAULT_REGISTRY_NAME).absolute()
        if registry_path.is_dir():
            return str(registry_path)
        raise ValueError(
            f"Registry path not provided and local registry `{DEFAULT_REGISTRY_NAME}` not found in current ({self.cwd}) and parent directory."
        )

    @property
    def skip_aea_validation(self) -> bool:
        """
        Get the 'skip_aea_validation' flag.

        If true, validation of the AEA version for loaded configuration
        file is skipped.

        :return: the 'skip_aea_validation'
        """
        return self.config.get("skip_aea_validation", True)

    @property
    def agent_loader(self) -> ConfigLoader:
        """Get the agent loader."""
        return ConfigLoader.from_configuration_type(
            PackageType.AGENT, skip_aea_validation=self.skip_aea_validation
        )

    @property
    def protocol_loader(self) -> ConfigLoader:
        """Get the protocol loader."""
        return ConfigLoader.from_configuration_type(
            PackageType.PROTOCOL, skip_aea_validation=self.skip_aea_validation
        )

    @property
    def connection_loader(self) -> ConfigLoader:
        """Get the connection loader."""
        return ConfigLoader.from_configuration_type(
            PackageType.CONNECTION, skip_aea_validation=self.skip_aea_validation
        )

    @property
    def skill_loader(self) -> ConfigLoader:
        """Get the skill loader."""
        return ConfigLoader.from_configuration_type(
            PackageType.SKILL, skip_aea_validation=self.skip_aea_validation
        )

    @property
    def contract_loader(self) -> ConfigLoader:
        """Get the contract loader."""
        return ConfigLoader.from_configuration_type(
            PackageType.CONTRACT, skip_aea_validation=self.skip_aea_validation
        )

    def set_config(self, key: str, value: Any) -> None:
        """
        Set a config.

        :param key: the key for the configuration.
        :param value: the value associated with the key.
        """
        self.config[key] = value
        logger.debug("  config[{}] = {}".format(key, value))

    @staticmethod
    def _get_item_dependencies(item_type: str, public_id: PublicId) -> Dependencies:
        """Get the dependencies from item type and public id."""
        item_type_plural = item_type + "s"
        default_config_file_name = _get_default_configuration_file_name_from_type(
            item_type
        )
        path = Path(
            VENDOR,
            public_id.author,
            item_type_plural,
            public_id.name,
            default_config_file_name,
        )
        if not path.exists():
            path = Path(item_type_plural, public_id.name, default_config_file_name)
        config_loader = ConfigLoader.from_configuration_type(item_type)
        with open_file(path) as fp:
            config = config_loader.load(fp)
        deps = cast(Dependencies, config.dependencies)
        return deps

    def get_dependencies(self) -> Dependencies:
        """
        Aggregate the dependencies from every component.

        :return: a list of dependency version specification. e.g. ["gym >= 1.0.0"]
        """
        protocol_dependencies = [
            self._get_item_dependencies(PROTOCOL, protocol_id)
            for protocol_id in self.agent_config.protocols
        ]
        connection_dependencies = [
            self._get_item_dependencies(CONNECTION, connection_id)
            for connection_id in self.agent_config.connections
        ]
        skill_dependencies = [
            self._get_item_dependencies(SKILL, skill_id)
            for skill_id in self.agent_config.skills
        ]
        contract_dependencies = [
            self._get_item_dependencies(CONTRACT, contract_id)
            for contract_id in self.agent_config.contracts
        ]

        all_dependencies = [
            self.agent_config.dependencies,
            *protocol_dependencies,
            *connection_dependencies,
            *skill_dependencies,
            *contract_dependencies,
        ]

        result = merge_dependencies_list(*all_dependencies)
        return result

    def dump_agent_config(self) -> None:
        """Dump the current agent configuration."""
        with open(os.path.join(self.cwd, DEFAULT_AEA_CONFIG_FILE), "w") as f:
            self.agent_loader.dump(self.agent_config, f)
