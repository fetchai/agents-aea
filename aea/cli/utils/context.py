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

from pathlib import Path
from typing import Dict, List, Optional, cast

from aea.cli.utils.loggers import logger
from aea.configurations.base import (
    AgentConfig,
    Dependencies,
    PackageType,
    PublicId,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL, VENDOR
from aea.configurations.loader import ConfigLoader


class Context:
    """A class to keep configuration of the cli tool."""

    agent_config: AgentConfig

    def __init__(
        self,
        cwd: str = ".",
        verbosity: str = "INFO",
        registry_path: Optional[str] = None,
    ):
        """Init the context."""
        self.config = dict()  # type: Dict
        self.cwd = cwd
        self.verbosity = verbosity
        self.clean_paths: List = []
        self.registry_path = registry_path

    @property
    def agent_loader(self) -> ConfigLoader:
        """Get the agent loader."""
        return ConfigLoader.from_configuration_type(PackageType.AGENT)

    @property
    def protocol_loader(self) -> ConfigLoader:
        """Get the protocol loader."""
        return ConfigLoader.from_configuration_type(PackageType.PROTOCOL)

    @property
    def connection_loader(self) -> ConfigLoader:
        """Get the connection loader."""
        return ConfigLoader.from_configuration_type(PackageType.CONNECTION)

    @property
    def skill_loader(self) -> ConfigLoader:
        """Get the skill loader."""
        return ConfigLoader.from_configuration_type(PackageType.SKILL)

    @property
    def contract_loader(self) -> ConfigLoader:
        """Get the contract loader."""
        return ConfigLoader.from_configuration_type(PackageType.CONTRACT)

    def set_config(self, key, value) -> None:
        """
        Set a config.

        :param key: the key for the configuration.
        :param value: the value associated with the key.
        :return: None
        """
        self.config[key] = value
        logger.debug("  config[{}] = {}".format(key, value))

    @staticmethod
    def _get_item_dependencies(item_type, public_id: PublicId) -> Dependencies:
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
        config = config_loader.load(path.open())
        deps = cast(Dependencies, config.dependencies)
        return deps

    def get_dependencies(self) -> Dependencies:
        """Aggregate the dependencies from every component.

        :return a list of dependency version specification. e.g. ["gym >= 1.0.0"]
        """
        dependencies = {}  # type: Dependencies
        for protocol_id in self.agent_config.protocols:
            dependencies.update(self._get_item_dependencies(PROTOCOL, protocol_id))

        for connection_id in self.agent_config.connections:
            dependencies.update(self._get_item_dependencies(CONNECTION, connection_id))

        for skill_id in self.agent_config.skills:
            dependencies.update(self._get_item_dependencies(SKILL, skill_id))

        for contract_id in self.agent_config.contracts:
            dependencies.update(self._get_item_dependencies(CONTRACT, contract_id))

        return dependencies
