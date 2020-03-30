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
import os
import pprint
import queue
import re
from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue
from typing import Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union, cast

from aea.configurations.base import (
    AgentConfig,
    ConfigurationType,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    ProtocolConfig,
    ProtocolId,
    PublicId,
    SkillId,
)
from aea.configurations.loader import ConfigLoader
from aea.decision_maker.messages.base import InternalMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.mail.base import EnvelopeContext
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


class Resources:
    """This class implements the resources of an AEA."""

    def __init__(self, directory: Optional[Union[str, os.PathLike]] = None):
        """Instantiate the resources."""
        self._directory = (
            str(Path(directory).absolute())
            if directory is not None
            else str(Path(".").absolute())
        )
        self.protocol_registry = ProtocolRegistry()
        self.handler_registry = HandlerRegistry()
        self.behaviour_registry = ComponentRegistry[Behaviour]()
        self.model_registry = ComponentRegistry[Model]()
        self._skills = dict()  # type: Dict[SkillId, Skill]

        self._registries = [
            self.protocol_registry,
            self.handler_registry,
            self.behaviour_registry,
            self.model_registry,
        ]

    @property
    def directory(self) -> str:
        """Get the directory."""
        return self._directory

    def add_skill(self, skill: Skill):
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

    def remove_protocol(self, protocol_id: ProtocolId):
        """Add a protocol to the set of resources."""
        self.protocol_registry.unregister(protocol_id)

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

    def get_active_handlers(
        self, protocol_id: PublicId, envelope_context: Optional[EnvelopeContext]
    ) -> List[Handler]:
        """
        Get active handlers.

        :param protocol_id: the protocol id
        :param envelope context: the envelope context
        :return: the list of handlers currently active
        """
        skill_id = None  # Optional[PublicId]
        if envelope_context is not None and envelope_context.uri is not None:
            uri_path = envelope_context.uri.path
            try:
                skill_id = PublicId.from_uri_path(uri_path)
            except ValueError:
                logger.warning("URI - {} - not a valid skill id.".format(uri_path))

        if skill_id is not None:
            handler = self.resources.handler_registry.fetch_by_protocol_and_skill(
                protocol_id, skill_id
            )
            active_handlers = (
                [] if handler is None or not handler.context.is_active else [handler]
            )
        else:
            handlers = self.resources.handler_registry.fetch_by_protocol(protocol_id)
            active_handlers = list(
                filter(lambda handler: handler.context.is_active, handlers)
            )
        return active_handlers

    def get_active_behaviours(self) -> List[Behaviour]:
        """
        Get the active behaviours.

        :return: the list of behaviours currently active
        """
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
