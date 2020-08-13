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
import subprocess  # nosec
from pathlib import Path
from typing import Any, Dict, Optional, cast

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


class Contract(Component):
    """Abstract definition of a contract."""

    contract_interface: Any = None

    def __init__(self, contract_config: ContractConfig, **kwargs):
        """
        Initialize the contract.

        :param contract_config: the contract configurations.
        """
        super().__init__(contract_config, **kwargs)

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
    def get_instance(
        cls, ledger_api: LedgerApi, contract_address: Optional[str] = None
    ) -> Any:
        """
        Get the instance.

        :param ledger_api: the ledger api we are using.
        :param contract_address: the contract address.
        :return: the contract instance
        """
        contract_interface = cls.contract_interface.get(ledger_api.identifier, {})
        instance = ledger_api.get_contract_instance(
            contract_interface, contract_address
        )
        return instance

    @classmethod
    def from_dir(cls, directory: str, **kwargs) -> "Contract":
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
        return Contract.from_config(configuration, **kwargs)

    @classmethod
    def from_config(cls, configuration: ContractConfig, **kwargs) -> "Contract":
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

        # TODO: load interfaces here
        # contract_interface = configuration.contract_interfaces

        return contract_class(configuration, **kwargs)

    @classmethod
    def get_deploy_transaction(
        cls, ledger_api: LedgerApi, deployer_address: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Handler method for the 'GET_DEPLOY_TRANSACTION' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param deployer_address: The address that will deploy the contract.
        :param kwargs: keyword arguments.
        :return: the tx
        """
        contract_interface = cls.contract_interface.get(ledger_api.identifier, {})
        tx = ledger_api.get_deploy_transaction(
            contract_interface, deployer_address, **kwargs
        )
        return tx

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Handler method for the 'GET_RAW_TRANSACTION' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :return: the tx
        """
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Handler method for the 'GET_RAW_MESSAGE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :return: the tx
        """
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Handler method for the 'GET_STATE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :return: the tx
        """
        raise NotImplementedError

    @staticmethod
    def get_last_code_id():
        """
        Uses wasmcli to get ID of latest deployed .wasm bytecode

        :return: code id of last deployed .wasm bytecode
        """

        command = ["wasmcli", "query", "wasm", "list-code"]

        stdout, _ = subprocess.Popen(  # nosec
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ).communicate()

        json_out = json.loads(stdout.decode("ascii"))

        return json_out[-1]["id"]

    @staticmethod
    def get_contract_address(code_id: int):
        """
        Uses wasmcli to get contract address of latest initialised contract by its ID

        :param code_id: id of deployed CosmWasm bytecode
        :return: contract address of last initialised contract
        """

        command = ["wasmcli", "query", "wasm", "list-contract-by-code", str(code_id)]

        stdout, _ = subprocess.Popen(  # nosec
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ).communicate()

        json_out = json.loads(stdout.decode("ascii"))

        return json_out[-1]["address"]
