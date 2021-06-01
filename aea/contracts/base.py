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
from pathlib import Path
from typing import Any, Dict, Optional, cast

from aea.common import JSONLike
from aea.components.base import Component, load_aea_package
from aea.configurations.base import ComponentType, ContractConfig, PublicId
from aea.configurations.constants import CONTRACTS
from aea.configurations.loader import load_component_configuration
from aea.crypto.base import LedgerApi
from aea.crypto.registries import Registry, ledger_apis_registry, make_ledger_api_cls
from aea.exceptions import AEAComponentLoadException, AEAException
from aea.helpers.base import load_module


contract_registry: Registry["Contract"] = Registry["Contract"]()
_default_logger = logging.getLogger(__name__)


class Contract(Component):
    """Abstract definition of a contract."""

    contract_id = None  # type: PublicId
    contract_interface: Any = None

    def __init__(self, contract_config: ContractConfig, **kwargs: Any) -> None:
        """
        Initialize the contract.

        :param contract_config: the contract configurations.
        :param kwargs: the keyword arguments.
        """
        super().__init__(contract_config, **kwargs)

    @property
    def id(self) -> PublicId:
        """Get the name."""
        return self.public_id

    @property
    def configuration(self) -> ContractConfig:
        """Get the configuration."""
        if self._configuration is None:  # pragma: nocover
            raise ValueError("Configuration not set.")
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
    def from_dir(cls, directory: str, **kwargs: Any) -> "Contract":
        """
        Load the protocol from a directory.

        :param directory: the directory to the skill package.
        :param kwargs: the keyword arguments.
        :return: the contract object.
        """
        configuration = cast(
            ContractConfig,
            load_component_configuration(ComponentType.CONTRACT, Path(directory)),
        )
        configuration.directory = Path(directory)
        return Contract.from_config(configuration, **kwargs)

    @classmethod
    def from_config(cls, configuration: ContractConfig, **kwargs: Any) -> "Contract":
        """
        Load contract from configuration.

        :param configuration: the contract configuration.
        :param kwargs: the keyword arguments.
        :return: the contract object.
        """
        if configuration.directory is None:  # pragma: nocover
            raise ValueError("Configuration must be associated with a directory.")
        directory = configuration.directory
        load_aea_package(configuration)
        contract_module = load_module(CONTRACTS, directory / "contract.py")
        classes = inspect.getmembers(contract_module, inspect.isclass)
        contract_class_name = cast(str, configuration.class_name)
        contract_classes = list(
            filter(lambda x: re.match(contract_class_name, x[0]), classes)
        )
        name_to_class = dict(contract_classes)
        _default_logger.debug(f"Processing contract {contract_class_name}")
        contract_class = name_to_class.get(contract_class_name, None)
        if contract_class is None:
            raise AEAComponentLoadException(
                f"Contract class '{contract_class_name}' not found."
            )

        _try_to_register_contract(configuration)
        contract = contract_registry.make(str(configuration.public_id), **kwargs)
        return contract

    @classmethod
    def get_deploy_transaction(
        cls, ledger_api: LedgerApi, deployer_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
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
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Handler method for the 'GET_RAW_TRANSACTION' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """
        Handler method for the 'GET_RAW_MESSAGE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Handler method for the 'GET_STATE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError


def _try_to_register_contract(configuration: ContractConfig) -> None:
    """Register a contract to the registry."""
    if str(configuration.public_id) in contract_registry.specs:  # pragma: nocover
        _default_logger.warning(
            f"Skipping registration of contract {configuration.public_id} since already registered."
        )
        return
    _default_logger.debug(
        f"Registering contract {configuration.public_id}"
    )  # pragma: nocover
    contract_interfaces = _load_contract_interfaces(configuration)
    try:  # pragma: nocover
        contract_registry.register(
            id_=str(configuration.public_id),
            entry_point=f"{configuration.prefix_import_path}.contract:{configuration.class_name}",
            class_kwargs={"contract_interface": contract_interfaces},
            contract_config=configuration,
        )
    except AEAException as e:  # pragma: nocover
        if "Cannot re-register id:" in str(e):
            _default_logger.warning(
                "Already registered: {}".format(configuration.class_name)
            )
        else:
            raise e


def _load_contract_interfaces(
    configuration: ContractConfig,
) -> Dict[str, Dict[str, str]]:
    """Get the contract interfaces."""
    if configuration.directory is None:  # pragma: nocover
        raise ValueError("Set contract configuration directory before calling.")
    contract_interfaces = {}  # type: Dict[str, Dict[str, str]]
    for identifier, path in configuration.contract_interface_paths.items():
        full_path = Path(configuration.directory, path)
        if identifier not in ledger_apis_registry.supported_ids:
            raise ValueError(  # pragma: nocover
                "No ledger api registered for identifier {}."
            )
        ledger_api = make_ledger_api_cls(identifier)
        contract_interface = ledger_api.load_contract_interface(full_path)
        contract_interfaces[identifier] = contract_interface
    return contract_interfaces
