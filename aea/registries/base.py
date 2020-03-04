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

import importlib.util
import inspect
import json
import logging
import os
import pprint
import queue
import re
from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue
from typing import Dict, Generic, List, Optional, Tuple, TypeVar, Union, cast

from aea.configurations.base import (
    ContractConfig,
    ContractId,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    ProtocolConfig,
    ProtocolId,
    PublicId,
    SkillId,
)
from aea.configurations.loader import ConfigLoader
from aea.contracts.base import Contract
from aea.decision_maker.messages.base import InternalMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message, Protocol
from aea.skills.base import AgentContext, Behaviour, Handler, Model, Skill
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

    def populate(self, directory: str) -> None:
        """
        Load the contract from the directory

        :param directory: the filepath to the agent's resource directory.
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
                self._add_contract(contract_package_path)
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

    def _add_contract(self, contract_directory: Path):
        """
        Add a contract.

        :param contract_directory: the directory of the contract to be added.
        :return: None
        """
        config_loader = ConfigLoader("contract-config_schema.json", ContractConfig)
        contract_config = config_loader.load(
            open(contract_directory / DEFAULT_CONTRACT_CONFIG_FILE)
        )
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
        contract_public_id = PublicId(
            contract_config.author, contract_config.name, contract_config.version
        )
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

    def populate(self, directory: str) -> None:
        """
        Load the handlers as specified in the config and apply consistency checks.

        :param directory: the filepath to the agent's resource directory.
        :return: None
        """
        protocol_directory_paths = set()  # type: ignore

        # find all protocol directories from vendor/*/protocols
        protocol_directory_paths.update(
            Path(directory, "vendor").glob("./*/protocols/*/")
        )
        # find all protocol directories from protocols/
        protocol_directory_paths.update(Path(directory, "protocols").glob("./*/"))

        protocols_packages_paths = list(
            filter(
                lambda x: PACKAGE_NAME_REGEX.match(str(x.name)) and x.is_dir(),
                protocol_directory_paths,
            )
        )  # type: ignore
        logger.debug(
            "Found the following protocol packages: {}".format(
                pprint.pformat(map(str, protocol_directory_paths))
            )
        )
        for protocol_package in protocols_packages_paths:
            try:
                logger.debug(
                    "Processing the protocol package '{}'".format(protocol_package)
                )
                self._add_protocol(protocol_package)
            except Exception:
                logger.exception(
                    "Not able to add protocol '{}'.".format(protocol_package.name)
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
        self._protocols = {}

    def _add_protocol(self, protocol_directory: Path):
        """
        Add a protocol.

        :param protocol_directory: the directory of the protocol to be added.
        :return: None
        """
        protocol_name = protocol_directory.name
        config_loader = ConfigLoader("protocol-config_schema.json", ProtocolConfig)
        protocol_config = config_loader.load(
            open(protocol_directory / DEFAULT_PROTOCOL_CONFIG_FILE)
        )

        # get the serializer
        serialization_spec = importlib.util.spec_from_file_location(
            "serialization", protocol_directory / "serialization.py"
        )
        serialization_module = importlib.util.module_from_spec(serialization_spec)
        serialization_spec.loader.exec_module(serialization_module)  # type: ignore
        classes = inspect.getmembers(serialization_module, inspect.isclass)
        serializer_classes = list(
            filter(lambda x: re.match("\\w+Serializer", x[0]), classes)
        )
        serializer_class = serializer_classes[0][1]

        logger.debug(
            "Found serializer class {serializer_class} for protocol {protocol_name}".format(
                serializer_class=serializer_class, protocol_name=protocol_name
            )
        )
        serializer = serializer_class()

        # instantiate the protocol
        protocol = Protocol(protocol_config.public_id, serializer, protocol_config)
        protocol_public_id = PublicId(
            protocol_config.author, protocol_config.name, protocol_config.version
        )
        self.register(protocol_public_id, protocol)


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


class Resources:
    """This class implements the resources of an AEA."""

    def __init__(self, directory: Optional[Union[str, os.PathLike]] = None):
        """Instantiate the resources."""
        self._directory = (
            str(Path(directory).absolute())
            if directory is not None
            else str(Path(".").absolute())
        )
        self.contract_registry = ContractRegistry()
        self.protocol_registry = ProtocolRegistry()
        self.handler_registry = HandlerRegistry()
        self.behaviour_registry = ComponentRegistry[Behaviour]()
        self.model_registry = ComponentRegistry[Model]()
        self._skills = dict()  # type: Dict[SkillId, Skill]

        self._registries = [
            self.contract_registry,
            self.protocol_registry,
            self.handler_registry,
            self.behaviour_registry,
            self.model_registry,
        ]

    @property
    def directory(self) -> str:
        """Get the directory."""
        return self._directory

    def load(self, agent_context: AgentContext) -> None:
        """Load all the resources."""
        self.contract_registry.populate(self.directory)
        self.protocol_registry.populate(self.directory)
        self.populate_skills(self.directory, agent_context)

    def populate_skills(self, directory: str, agent_context: AgentContext) -> None:
        """
        Populate skills.

        :param directory: the agent's resources directory.
        :param agent_context: the agent's context object
        :return: None
        """
        skill_directory_paths = set()  # type: ignore

        # find all skill directories from vendor/*/skills
        skill_directory_paths.update(Path(directory, "vendor").glob("./*/skills/*/"))
        # find all skill directories from skills/
        skill_directory_paths.update(Path(directory, "skills").glob("./*/"))

        skills_packages_paths = list(
            filter(
                lambda x: PACKAGE_NAME_REGEX.match(str(x.name)) and x.is_dir(),
                skill_directory_paths,
            )
        )  # type: ignore
        logger.debug(
            "Found the following skill packages: {}".format(
                pprint.pformat(map(str, skills_packages_paths))
            )
        )
        for skill_directory in skills_packages_paths:
            logger.debug(
                "Processing the following skill directory: '{}".format(skill_directory)
            )
            try:
                skill = Skill.from_dir(str(skill_directory), agent_context)
                assert skill is not None
                self.add_skill(skill)
                self.inject_contracts(skill)
            except Exception as e:
                logger.warning(
                    "A problem occurred while parsing the skill directory {}. Exception: {}".format(
                        skill_directory, str(e)
                    )
                )

    def add_skill(self, skill: Skill) -> None:
        """Add a skill to the set of resources."""
        skill_id = skill.config.public_id
        self._skills[skill_id] = skill
        if skill.handlers is not None:
            for handler in skill.handlers.values():
                self.handler_registry.register((skill_id, handler.name), handler)
        if skill.behaviours is not None:
            for behaviour in skill.behaviours.values():
                self.behaviour_registry.register((skill_id, behaviour.name), behaviour)
        if skill.models is not None:
            for model in skill.models.values():
                self.model_registry.register((skill_id, model.name), model)

    def add_protocol(self, protocol: Protocol):
        """Add a protocol to the set of resources."""
        self.protocol_registry.register(protocol.id, protocol)

    def inject_contracts(self, skill: Skill) -> None:
        if skill.config.contracts is not None:
            # check all contracts are present
            contracts = {}  # type: Dict[str, Contract]
            for contract_id in skill.config.contracts:
                contract = self.contract_registry.fetch(contract_id)
                if contract is None:
                    raise ValueError(
                        "Missing contract for contract id {}".format(contract_id)
                    )
                contracts[contract_id.name] = contract
            skill.inject_contracts(contracts)

    def get_skill(self, skill_id: SkillId) -> Optional[Skill]:
        """Get the skill."""
        return self._skills.get(skill_id, None)

    def get_all_skills(self) -> List[Skill]:
        """
        Get the list of all the skills.

        :return: the list of skills.
        """
        return list(self._skills.values())

    def remove_skill(self, skill_id: SkillId):
        """Remove a skill from the set of resources."""
        self._skills.pop(skill_id, None)
        try:
            self.handler_registry.unregister_by_skill(skill_id)
        except ValueError:
            pass

        try:
            self.behaviour_registry.unregister_by_skill(skill_id)
        except ValueError:
            pass

    def setup(self):
        """
        Set up the resources.

        :return: None
        """
        for r in self._registries:
            r.setup()

    def teardown(self):
        """
        Teardown the resources.

        :return: None
        """
        for r in self._registries:
            r.teardown()


class Filter:
    """This class implements the filter of an AEA."""

    def __init__(self, resources: Resources, decision_maker_out_queue: Queue):
        """
        Instantiate the filter.

        :param resources: the resources
        :param decision_maker_out_queue: the decision maker queue
        """
        self._resources = resources
        self._decision_maker_out_queue = decision_maker_out_queue

    @property
    def resources(self) -> Resources:
        """Get resources."""
        return self._resources

    @property
    def decision_maker_out_queue(self) -> Queue:
        """Get decision maker (out) queue."""
        return self._decision_maker_out_queue

    def get_active_handlers(self, protocol_id: PublicId) -> List[Handler]:
        """
        Get active handlers.

        :param protocol_id: the protocol id
        :return: the list of handlers currently active
        """
        # TODO naive implementation
        handlers = self.resources.handler_registry.fetch_by_protocol(protocol_id)
        active_handlers = list(filter(lambda h: h.context.is_active, handlers))
        return active_handlers

    def get_active_behaviours(self) -> List[Behaviour]:
        """
        Get the active behaviours.

        :return: the list of behaviours currently active
        """
        # TODO naive implementation
        behaviours = self.resources.behaviour_registry.fetch_all()
        active_behaviour = list(
            filter(lambda b: b.context.is_active and not b.is_done(), behaviours,)
        )
        return active_behaviour

    def handle_internal_messages(self) -> None:
        """
        Handle the messages from the decision maker.

        :return: None
        """
        while not self.decision_maker_out_queue.empty():
            try:
                internal_message = (
                    self.decision_maker_out_queue.get_nowait()
                )  # type: Optional[InternalMessage]
            except queue.Empty:
                logger.warning("The decision maker out queue is unexpectedly empty.")
                continue
            if internal_message is None:
                logger.warning("Got 'None' while processing internal messages.")
            elif isinstance(internal_message, TransactionMessage):
                internal_message = cast(TransactionMessage, internal_message)
                self._handle_tx_message(internal_message)
            else:
                logger.warning(
                    "Cannot handle a {} message.".format(type(internal_message))
                )

        # get new behaviours from the agent skills
        for skill in self.resources.get_all_skills():
            while not skill.skill_context.new_behaviours.empty():
                new_behaviour = skill.skill_context.new_behaviours.get()
                try:
                    self.resources.behaviour_registry.register(
                        (skill.skill_context.skill_id, new_behaviour.name),
                        new_behaviour,
                    )
                except ValueError as e:
                    logger.warning(
                        "Error when trying to add a new behaviour: {}".format(str(e))
                    )

    def _handle_tx_message(self, tx_message: TransactionMessage):
        """Handle transaction message from the Decision Maker."""
        skill_callback_ids = tx_message.skill_callback_ids
        for skill_id in skill_callback_ids:
            handler = self.resources.handler_registry.fetch_internal_handler(skill_id)
            if handler is not None:
                logger.debug(
                    "Calling handler {} of skill {}".format(type(handler), skill_id)
                )
                handler.handle(cast(Message, tx_message))
            else:
                logger.warning(
                    "No internal handler fetched for skill_id={}".format(skill_id)
                )
