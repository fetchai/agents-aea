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

"""This module contains registries."""

import logging
import os
import queue
import re
from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue
from typing import Dict, Generic, List, Optional, Tuple, TypeVar, Union, cast

import importlib.util
import inspect
import json
import logging
import pprint
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Generic, List, Optional, Set, Tuple, TypeVar, cast

from aea.configurations.base import (
    ComponentType,
    ContractConfig,
    ContractId,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    ProtocolConfig,
    ProtocolId,
    PublicId,
    SkillId,
)
from aea.configurations.components import Component
from aea.decision_maker.messages.base import InternalMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.mail.base import EnvelopeContext
from aea.protocols.base import Message, Protocol
from aea.skills.base import Behaviour, Handler, Model, Skill

from aea.configurations.loader import ConfigLoader
from aea.contracts.base import Contract
from aea.protocols.base import Protocol
from aea.skills.base import Behaviour, Handler, Model

from aea.skills.tasks import Task

logger = logging.getLogger(__name__)

PACKAGE_NAME_REGEX = re.compile(
    "^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
)
INTERNAL_PROTOCOL_ID = PublicId.from_str("fetchai/internal:0.1.0")
DECISION_MAKER = "decision_maker"

Item = TypeVar("Item")
ItemId = TypeVar("ItemId")
ComponentId = Tuple[SkillId, str]
SkillComponentType = TypeVar("SkillComponentType", Handler, Behaviour, Task, Model)


class Registry(Generic[ItemId, Item], ABC):
    """This class implements an abstract registry."""

    @abstractmethod
    def register(self, item_id: ItemId, item: Item) -> None:
        """
        Register an item.

        :param item_id: the public id of the item.
        :param item: the item.
        :return: None
        :raises: ValueError if an item is already registered with that item id.
        """

    @abstractmethod
    def unregister(self, item_id: ItemId) -> None:
        """
        Unregister an item.

        :param item_id: the public id of the item.
        :return: None
        :raises: ValueError if no item registered with that item id.
        """

    @abstractmethod
    def fetch(self, item_id: ItemId) -> Optional[Item]:
        """
        Fetch an item.

        :param item_id: the public id of the item.
        :return: the Item
        """

    @abstractmethod
    def fetch_all(self) -> List[Item]:
        """
        Fetch all the items.

        :return: the list of items.
        """

    @abstractmethod
    def setup(self) -> None:
        """
        Set up registry.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """


class ContractRegistry(Registry[PublicId, Contract]):
    """This class implements the contracts registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._contracts = {}  # type: Dict[ContractId, Contract]

    def register(self, contract_id: ContractId, contract: Contract) -> None:
        """
        Register a contract.

        :param contract_id: the public id of the contract.
        :param contract: the contract object.
        """
        if contract_id in self._contracts.keys():
            raise ValueError(
                "Contract already registered with contract id '{}'".format(contract_id)
            )
        if contract.id != contract_id:
            raise ValueError(
                "Contract id '{}' is different to the id '{}' specified.".format(
                    contract.id, contract_id
                )
            )
        self._contracts[contract_id] = contract

    def unregister(self, contract_id: ContractId) -> None:
        """
        Unregister a contract.

        :param contract_id: the contract id
        """
        if contract_id not in self._contracts.keys():
            raise ValueError(
                "No contract registered with contract id '{}'".format(contract_id)
            )
        removed_contract = self._contracts.pop(contract_id)
        logger.debug("Contract '{}' has been removed.".format(removed_contract.id))

    def fetch(self, contract_id: ContractId) -> Optional[Contract]:
        """
        Fetch the contract by id.

        :param contract_id: the contract id
        :return: the contract or None if the contract is not registered
        """
        return self._contracts.get(contract_id, None)

    def fetch_all(self) -> List[Contract]:
        """Fetch all the contracts."""
        return list(self._contracts.values())

    def populate(
        self, directory: str, allowed_contracts: Optional[Set[PublicId]] = None
    ) -> None:
        """
        Load the contract from the directory

        :param directory: the filepath to the agent's resource directory.
        :param allowed_contracts: an optional set of allowed contracts (public ids).
                                  If None, every protocol is allowed.
        :return: None
        """
        contract_directory_paths = set()  # type: ignore

        # find all contract directories from vendor/*/contracts
        contract_directory_paths.update(
            Path(directory, "vendor").glob("./*/contracts/*/")
        )
        # find all contract directories from contracts/
        contract_directory_paths.update(Path(directory, "contracts").glob("./*/"))

        contract_packages_paths = list(
            filter(
                lambda x: PACKAGE_NAME_REGEX.match(str(x.name)) and x.is_dir(),
                contract_directory_paths,
            )
        )  # type: ignore
        logger.debug(
            "Found the following contract packages: {}".format(
                pprint.pformat(map(str, contract_directory_paths))
            )
        )
        for contract_package_path in contract_packages_paths:
            try:
                logger.debug(
                    "Processing the contract package '{}'".format(contract_package_path)
                )
                self._add_contract(
                    contract_package_path, allowed_contracts=allowed_contracts
                )
            except Exception:
                logger.exception(
                    "Not able to add contract '{}'.".format(contract_package_path.name)
                )

    def setup(self) -> None:
        """
        Set up the registry.

        :return: None
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        self._contracts = {}

    def _add_contract(
        self,
        contract_directory: Path,
        allowed_contracts: Optional[Set[PublicId]] = None,
    ):
        """
        Add a contract.

        :param contract_directory: the directory of the contract to be added.
        :param allowed_contracts: an optional set of allowed contracts (public ids).
                                  If None, every protocol is allowed.
        :return: None
        """
        config_loader = ConfigLoader("contract-config_schema.json", ContractConfig)
        contract_config = config_loader.load(
            open(contract_directory / DEFAULT_CONTRACT_CONFIG_FILE)
        )
        contract_public_id = PublicId(
            contract_config.author, contract_config.name, contract_config.version
        )
        if (
            allowed_contracts is not None
            and contract_public_id not in allowed_contracts
        ):
            logger.debug(
                "Ignoring contract {}, not declared in the configuration file.".format(
                    contract_public_id
                )
            )
            return

        contract_spec = importlib.util.spec_from_file_location(
            "contracts", contract_directory / "contract.py"
        )
        contract_module = importlib.util.module_from_spec(contract_spec)
        contract_spec.loader.exec_module(contract_module)  # type: ignore
        classes = inspect.getmembers(contract_module, inspect.isclass)
        contract_classes = list(
            filter(lambda x: re.match("\\w+Contract", x[0]), classes)
        )
        contract_class = contract_classes[0][1]
        path = Path(contract_directory, contract_config.path_to_contract_interface)
        with open(path, "r") as interface_file:
            contract_interface = json.load(interface_file)
        contract = contract_class(
            contract_id=contract_public_id,
            contract_config=contract_config,
            contract_interface=contract_interface,
        )

        self.register(contract_public_id, contract)


class ProtocolRegistry(Registry[PublicId, Protocol]):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._protocols = {}  # type: Dict[ProtocolId, Protocol]

    def register(self, item_id: PublicId, protocol: Protocol) -> None:
        """
        Register a protocol.

        :param item_id: the public id of the protocol.
        :param protocol: the protocol object.
        """
        if item_id in self._protocols.keys():
            raise ValueError(
                "Protocol already registered with protocol id '{}'".format(item_id)
            )
        if protocol.id != item_id:
            raise ValueError(
                "Protocol id '{}' is different to the id '{}' specified.".format(
                    protocol.id, item_id
                )
            )
        self._protocols[item_id] = protocol

    def unregister(self, protocol_id: ProtocolId) -> None:
        """Unregister a protocol."""
        if protocol_id not in self._protocols.keys():
            raise ValueError(
                "No protocol registered with protocol id '{}'".format(protocol_id)
            )
        removed_protocol = self._protocols.pop(protocol_id)
        logger.debug("Protocol '{}' has been removed.".format(removed_protocol.id))

    def fetch(self, protocol_id: ProtocolId) -> Optional[Protocol]:
        """
        Fetch the protocol for the envelope.

        :param protocol_id: the protocol id
        :return: the protocol id or None if the protocol is not registered
        """
        return self._protocols.get(protocol_id, None)

    def fetch_all(self) -> List[Protocol]:
        """Fetch all the protocols."""
        return list(self._protocols.values())

    def setup(self) -> None:
        """
        Set up the registry.

        :return: None
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        self._protocols = {}


class ComponentRegistry(
    Registry[Tuple[SkillId, str], SkillComponentType], Generic[SkillComponentType]
):
    """This class implements a generic registry for skill components."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._items = {}  # type: Dict[SkillId, Dict[str, SkillComponentType]]

    def register(self, item_id: Tuple[SkillId, str], item: SkillComponentType) -> None:
        """
        Register a item.

        :param item_id: a pair (skill id, item name).
        :param item: the item to register.
        :return: None
        :raises: ValueError if an item is already registered with that item id.
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        if item_name in self._items.get(skill_id, {}).keys():
            raise ValueError(
                "Item already registered with skill id '{}' and name '{}'".format(
                    skill_id, item_name
                )
            )
        self._items.setdefault(skill_id, {})[item_name] = item

    def unregister(self, item_id: Tuple[SkillId, str]) -> None:
        """
        Unregister a item.

        :param item_id: a pair (skill id, item name).
        :return: None
        :raises: ValueError if no item registered with that item id.
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        name_to_item = self._items.get(skill_id, {})
        if item_name not in name_to_item:
            raise ValueError(
                "No item registered with component id '{}'".format(item_id)
            )
        logger.debug("Unregistering item with id {}".format(item_id))
        name_to_item.pop(item_name)

        if len(name_to_item) == 0:
            self._items.pop(skill_id, None)

    def fetch(self, item_id: Tuple[SkillId, str]) -> Optional[SkillComponentType]:
        """
        Fetch an item.

        :param item_id: the public id of the item.
        :return: the Item
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        return self._items.get(skill_id, {}).get(item_name, None)

    def fetch_by_skill(self, skill_id: SkillId) -> List[Item]:
        """Fetch all the items of a given skill."""
        return [*self._items.get(skill_id, {}).values()]

    def fetch_all(self) -> List[SkillComponentType]:
        """Fetch all the items."""
        return [
            item for skill_id, items in self._items.items() for item in items.values()
        ]

    def unregister_by_skill(self, skill_id: SkillId) -> None:
        """Unregister all the components by skill."""
        if skill_id not in self._items:
            raise ValueError(
                "No component of skill {} present in the registry.".format(skill_id)
            )
        self._items.pop(skill_id, None)

    def setup(self) -> None:
        """
        Set up the items in the registry.

        :return: None
        """
        for item in self.fetch_all():
            item.setup()

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for skill_id, items in self._items.items():
            for _, item in items.items():
                try:
                    item.teardown()
                except Exception as e:
                    logger.warning(
                        "An error occurred while tearing down item {}/{}: {}".format(
                            skill_id, type(item).__name__, str(e)
                        )
                    )


class HandlerRegistry(ComponentRegistry[Handler]):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        super().__init__()
        self._items_by_protocol_and_skill = (
            {}
        )  # type: Dict[ProtocolId, Dict[SkillId, Handler]]

    def register(self, item_id: Tuple[SkillId, str], item: Handler) -> None:
        """
        Register a handler.

        :param item_id: the item id.
        :param item: the handler.
        :return: None
        :raises ValueError: if the protocol is None, or an item with pair (skill_id, protocol_id_ already exists.
        """
        super().register(item_id, item)

        skill_id = item_id[0]

        protocol_id = item.SUPPORTED_PROTOCOL
        if protocol_id is None:
            raise ValueError(
                "Please specify a supported protocol for handler class '{}'".format(
                    item.__class__.__name__
                )
            )

        protocol_handlers_by_skill = self._items_by_protocol_and_skill.get(
            protocol_id, {}
        )
        if skill_id in protocol_handlers_by_skill:
            # clean up previous modifications done by super().register
            super().unregister(item_id)
            raise ValueError(
                "A handler already registered with pair of protocol id {} and skill id {}".format(
                    protocol_id, skill_id
                )
            )

        self._items_by_protocol_and_skill.setdefault(protocol_id, {})[skill_id] = item

    def unregister(self, item_id: Tuple[SkillId, str]) -> None:
        """
        Unregister a item.

        :param item_id: a pair (skill id, item name).
        :return: None
        :raises: ValueError if no item is registered with that item id.
        """
        # remove from main index
        skill_id = item_id[0]
        item_name = item_id[1]
        name_to_item = self._items.get(skill_id, {})
        if item_name not in name_to_item:
            raise ValueError(
                "No item registered with component id '{}'".format(item_id)
            )
        logger.debug("Unregistering item with id {}".format(item_id))
        handler = name_to_item.pop(item_name)

        if len(name_to_item) == 0:
            self._items.pop(skill_id, None)

        # remove from index by protocol and skill
        protocol_id = cast(ProtocolId, handler.SUPPORTED_PROTOCOL)
        protocol_handlers_by_skill = self._items_by_protocol_and_skill.get(
            protocol_id, {}
        )
        protocol_handlers_by_skill.pop(skill_id, None)
        if len(protocol_handlers_by_skill) == 0:
            self._items_by_protocol_and_skill.pop(protocol_id, None)

    def unregister_by_skill(self, skill_id: SkillId) -> None:
        """Unregister all the components by skill."""
        # unregister from the main index.
        if skill_id not in self._items:
            raise ValueError(
                "No component of skill {} present in the registry.".format(skill_id)
            )
        handlers = self._items.pop(skill_id).values()

        # unregister from the protocol-skill index
        for handler in handlers:
            protocol_id = cast(ProtocolId, handler.SUPPORTED_PROTOCOL)
            self._items_by_protocol_and_skill.get(protocol_id, {}).pop(skill_id, None)

    def fetch_by_protocol(self, protocol_id: ProtocolId) -> List[Handler]:
        """
        Fetch the handler by the pair protocol id and skill id.

        :param protocol_id: the protocol id
        :return: the handlers registered for the protocol_id and skill_id
        """
        protocol_handlers_by_skill = self._items_by_protocol_and_skill.get(
            protocol_id, {}
        )
        handlers = [
            protocol_handlers_by_skill[skill_id]
            for skill_id in protocol_handlers_by_skill
        ]
        return handlers

    def fetch_by_protocol_and_skill(
        self, protocol_id: ProtocolId, skill_id: SkillId
    ) -> Optional[Handler]:
        """
        Fetch the handler by the pair protocol id and skill id.

        :param protocol_id: the protocol id
        :param skill_id: the skill id.
        :return: the handlers registered for the protocol_id and skill_id
        """
        return self._items_by_protocol_and_skill.get(protocol_id, {}).get(
            skill_id, None
        )

    def fetch_internal_handler(self, skill_id: SkillId) -> Optional[Handler]:
        """
        Fetch the internal handler.

        :param skill_id: the skill id
        :return: the internal handler registered for the skill id
        """
        return self.fetch_by_protocol_and_skill(INTERNAL_PROTOCOL_ID, skill_id)
