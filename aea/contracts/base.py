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

"""The base contract."""
import inspect
import json
import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, cast

from aea.configurations.base import (
    ComponentConfiguration,
    ComponentType,
    ContractConfig,
    ContractId,
)
from aea.components.base import Component
from aea.crypto.base import LedgerApi
from aea.helpers.base import add_modules_to_sys_modules, load_all_modules, load_module

logger = logging.getLogger(__name__)


class Contract(Component, ABC):
    """Abstract definition of a contract."""

    def __init__(
        self, config: ContractConfig, contract_interface: Dict[str, Any],
    ):
        """
        Initialize the contract.

        :param config: the contract configurations.
        :param contract_interface: the contract interface
        """
        super().__init__(config)
        self._contract_interface = contract_interface  # type: Dict[str, Any]

    @property
    def id(self) -> ContractId:
        """Get the name."""
        return self.public_id

    @property
    def config(self) -> ContractConfig:
        """Get the configuration."""
        # return self._config
        return self._configuration  # type: ignore

    @property
    def contract_interface(self) -> Dict[str, Any]:
        """Get the contract interface."""
        return self._contract_interface

    @abstractmethod
    def set_instance(self, ledger_api: LedgerApi) -> None:
        """
        Set the instance.

        :param ledger_api: the ledger api we are using.
        :return: None
        """

    @abstractmethod
    def set_address(self, ledger_api: LedgerApi, contract_address: str) -> None:
        """
        Set the contract address.

        :param ledger_api: the ledger_api we are using.
        :param contract_address: the contract address
        :return: None
        """

    @abstractmethod
    def set_deployed_instance(
        self, ledger_api: LedgerApi, contract_address: str
    ) -> None:
        """
        Set the contract address.

        :param ledger_api: the ledger_api we are using.
        :param contract_address: the contract address
        :return: None
        """

    @classmethod
    def from_dir(cls, directory: str) -> "Contract":
        """
        Load the protocol from a directory.

        :param directory: the directory to the skill package.
        :return: the contract object.
        """
        configuration = cast(
            ContractConfig,
            ComponentConfiguration.load(ComponentType.CONTRACT, Path(directory)),
        )
        configuration._directory = Path(directory)
        return Contract.from_config(configuration)

    @classmethod
    def from_config(cls, configuration: ContractConfig) -> "Contract":
        """
        Load contract from configuration

        :param configuration: the contract configuration.
        :return: the contract object.
        """
        assert (
            configuration.directory is not None
        ), "Configuration must be associated with a directory."
        directory = configuration.directory
        package_modules = load_all_modules(
            directory, glob="__init__.py", prefix=configuration.prefix_import_path
        )
        add_modules_to_sys_modules(package_modules)
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
