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
import logging
import pprint
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Generic, List, Optional, Set, Tuple, TypeVar, cast

from aea.configurations.base import (
    DEFAULT_PROTOCOL_CONFIG_FILE,
    ProtocolConfig,
    ProtocolId,
    PublicId,
    SkillId,
)
from aea.configurations.loader import ConfigLoader
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

    def populate(
        self, directory: str, allowed_protocols: Optional[Set[PublicId]] = None
    ) -> None:
        """
        Load the handlers as specified in the config and apply consistency checks.

        :param directory: the filepath to the agent's resource directory.
        :param allowed_protocols: an optional set of allowed protocols (public ids_.
                                  If None, every protocol is allowed.
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
        for protocol_package_path in protocols_packages_paths:
            try:
                logger.debug(
                    "Processing the protocol package '{}'".format(protocol_package_path)
                )
                self._add_protocol(
                    protocol_package_path, allowed_protocols=allowed_protocols
                )
            except Exception:
                logger.exception(
                    "Not able to add protocol '{}'.".format(protocol_package_path.name)
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

    def _add_protocol(
        self,
        protocol_directory: Path,
        allowed_protocols: Optional[Set[PublicId]] = None,
    ):
        """
        Add a protocol. If the protocol is not allowed, it is ignored.

        :param protocol_directory: the directory of the protocol to be added.
        :param allowed_protocols: an optional set of allowed protocols.
                                  If None, every protocol is allowed.
        :return: None
        """
        protocol_name = protocol_directory.name
        config_loader = ConfigLoader("protocol-config_schema.json", ProtocolConfig)
        protocol_config = config_loader.load(
            open(protocol_directory / DEFAULT_PROTOCOL_CONFIG_FILE)
        )
        protocol_public_id = PublicId(
            protocol_config.author, protocol_config.name, protocol_config.version
        )
        if (
            allowed_protocols is not None
            and protocol_public_id not in allowed_protocols
        ):
            logger.debug(
                "Ignoring protocol {}, not declared in the configuration file.".format(
                    protocol_public_id
                )
            )
            return

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
