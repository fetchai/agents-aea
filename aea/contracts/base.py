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
import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, cast

from aea.components.base import Component
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentType,
    ContractConfig,
    ContractId,
)
from aea.crypto.base import LedgerApi
from aea.helpers.base import load_aea_package, load_module

logger = logging.getLogger(__name__)


class Contract(Component, ABC):
    """Abstract definition of a contract."""

    contract_interface: Any = None

    def __init__(self, contract_config: ContractConfig):
        """
        Initialize the contract.

        :param contract_config: the contract configurations.
        """
        super().__init__(contract_config)

    @property
    def id(self) -> ContractId:
        """Get the name."""
        return self.public_id

    @property
    def configuration(self) -> ContractConfig:
        """Get the configuration."""
        assert self._configuration is not None, "Configuration not set."
        return cast(ContractConfig, super().configuration)

    @classmethod
    @abstractmethod
    def get_instance(
        cls, ledger_api: LedgerApi, contract_address: Optional[str] = None
    ) -> Any:
        """
        Get the instance.

        :param ledger_api: the ledger api we are using.
        :param contract_address: the contract address.
        :return: the contract instance
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
        configuration.directory = Path(directory)
        return Contract.from_config(configuration)

    @classmethod
    def from_config(cls, configuration: ContractConfig) -> "Contract":
        """
        Load contract from configuration.

        :param configuration: the contract configuration.
        :return: the contract object.
        """
        assert (
            configuration.directory is not None
        ), "Configuration must be associated with a directory."
        directory = configuration.directory
        load_aea_package(configuration)
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

        # path = Path(directory, configuration.path_to_contract_interface)
        # with open(path, "r") as interface_file:
        #     contract_interface = json.load(interface_file)

        return contract_class(configuration)
