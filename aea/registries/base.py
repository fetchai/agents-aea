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
import re
from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue
from typing import Dict, Generic, List, Optional, Tuple, TypeVar, Union, cast

from aea.configurations.base import (
    DEFAULT_PROTOCOL_CONFIG_FILE,
    ProtocolConfig,
    ProtocolId,
    PublicId,
    SkillId,
)
from aea.configurations.loader import ConfigLoader
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message, Protocol
from aea.skills.base import AgentContext, Behaviour, Handler, Skill, Task

logger = logging.getLogger(__name__)

PACKAGE_NAME_REGEX = re.compile(
    "^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
)
INTERNAL_PROTOCOL_ID = PublicId.from_string("fetchai/internal:0.1.0")
DECISION_MAKER = "decision_maker"


Item = TypeVar("Item")
ItemId = TypeVar("ItemId")
ComponentId = Tuple[SkillId, str]
SkillComponentType = TypeVar("SkillComponentType", Handler, Behaviour, Task)


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
                "Protocol already registered with protocl id '{}'".format(item_id)
            )
        self._protocols[item_id] = protocol

    def unregister(self, protocol_id: ProtocolId) -> None:
        """Unregister a protocol."""
        self._protocols.pop(protocol_id, None)

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

        protocols_packages_paths = list(filter(lambda x: PACKAGE_NAME_REGEX.match(str(x.name)) and x.is_dir(), protocol_directory_paths))  # type: ignore
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
        # get the serializer
        protocol_name = protocol_directory.name
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

        config_loader = ConfigLoader("protocol-config_schema.json", ProtocolConfig)
        protocol_config = config_loader.load(
            open(protocol_directory / DEFAULT_PROTOCOL_CONFIG_FILE)
        )

        # instantiate the protocol manager.
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
        """

        skill_id = item_id[0]
        item_name = item_id[1]
        name_to_handlers = self._items.get(skill_id, {})
        name_to_handlers.pop(item_name, None)

        if len(name_to_handlers) == 0:
            self._items.pop(skill_id, None)

    def fetch(self, item_id: Tuple[SkillId, str]) -> Optional[SkillComponentType]:
        """
        Return a item.

        :return: the list of items
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        return self._items.get(skill_id, {}).get(item_name, None)

    def fetch_by_skill(self, skill_id: SkillId) -> List[Item]:
        """Fetch all the items of a given skill."""
        return list(*self._items.get(skill_id, {}).values())

    def fetch_all(self) -> List[SkillComponentType]:
        """Fetch all the items."""
        return [
            item for skill_id, items in self._items.items() for item in items.values()
        ]

    def unregister_by_skill(self, skill_id: SkillId) -> None:
        """Unregister all the components by skill."""
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

    def fetch_by_protocol(self, protocol_id: ProtocolId) -> List[Handler]:
        """
        Fetch the handler by the pair protocol id and skill id.

        :param protocol_id: the protocol id
        :return: the handlers registered for the protocol_id and skill_id
        """
        # TODO this could be optimized by having an index by protocol
        #      however that requires extending the superclass methods.
        handlers = self.fetch_all()
        return [
            handler
            for handler in filter(
                lambda handler: handler.SUPPORTED_PROTOCOL == protocol_id, handlers
            )
        ]

    def fetch_by_protocol_and_skill(
        self, protocol_id: ProtocolId, skill_id: SkillId
    ) -> Optional[Handler]:
        """
        Fetch the handler by the pair protocol id and skill id.

        :param protocol_id: the protocol id
        :param skill_id: the skill id.
        :return: the handlers registered for the protocol_id and skill_id
        """
        result = []
        for _, handler in self._items.get(skill_id, {}).items():
            if handler.SUPPORTED_PROTOCOL == protocol_id:
                result.append(handler)
        assert len(result) <= 1, "at most one handler allowed per (skill, protocol)"
        return result[0] if len(result) == 1 else None

    def fetch_internal_handler(self, skill_id: SkillId) -> Optional[Handler]:
        """
        Fetch the internal handler.

        :param skill_id: the skill id
        :return: the internal handler registered for the skill id
        """
        return self.fetch_by_protocol_and_skill(INTERNAL_PROTOCOL_ID, skill_id)


class Resources(object):
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
        self.task_registry = ComponentRegistry[Task]()
        self._skills = dict()  # type: Dict[SkillId, Skill]

        self._registries = [
            self.protocol_registry,
            self.handler_registry,
            self.behaviour_registry,
            self.task_registry,
        ]

    @property
    def directory(self) -> str:
        """Get the directory."""
        return self._directory

    def load(self, agent_context: AgentContext) -> None:
        """Load all the resources."""
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

        skills_packages_paths = list(filter(lambda x: PACKAGE_NAME_REGEX.match(str(x.name)) and x.is_dir(), skill_directory_paths))  # type: ignore
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
            except Exception as e:
                logger.warning(
                    "A problem occurred while parsing the skill directory {}. Exception: {}".format(
                        skill_directory, str(e)
                    )
                )

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
        if skill.tasks is not None:
            for task in skill.tasks.values():
                self.task_registry.register((skill_id, task.name), task)

    def get_skill(self, skill_id: SkillId) -> Optional[Skill]:
        """Get the skill."""
        return self._skills.get(skill_id, None)

    def remove_skill(self, skill_id: SkillId):
        """Remove a skill from the set of resources."""
        self._skills.pop(skill_id, None)
        self.handler_registry.unregister_by_skill(skill_id)
        self.behaviour_registry.unregister_by_skill(skill_id)
        self.task_registry.unregister_by_skill(skill_id)

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


class Filter(object):
    """This class implements the filter of an AEA."""

    def __init__(self, resources: Resources, decision_maker_out_queue: Queue):
        """
        Instantiate the filter.

        :param resources: the resources
        :param decision_maker_out_queue: the decision maker queue
        """
        self._resources = resources
        self._decision_maker_out_queue = decision_maker_out_queue
        # TODO: self._inactive_handlers = {}  # type: Dict[SkillId, List[HandlerId]]
        # TODO: self._inactive_behaviours = {}  # type: Dict[SkillId, List[BehaviourId]]
        # TODO: self._inactive_tasks = {}  # type: Dict[SkillId, List[TaskId]]

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
        :return: list of handlers
        """
        handlers = self.resources.handler_registry.fetch_by_protocol(protocol_id)
        # TODO: add option for advanced filtering, currently each handler independently acts on the message
        return handlers

    def get_active_tasks(self) -> List[Task]:
        """
        Get the active tasks.

        :return: the list of tasks currently active
        """
        tasks = self.resources.task_registry.fetch_all()
        # TODO: add filtering, remove inactive tasks
        return tasks

    def get_active_behaviours(self) -> List[Behaviour]:
        """
        Get the active behaviours.

        :return: the list of behaviours currently active
        """
        behaviours = self.resources.behaviour_registry.fetch_all()
        return [b for b in behaviours if not b.done()]

    def handle_internal_messages(self) -> None:
        """
        Handle the messages from the decision maker.

        :return: None
        """
        while not self.decision_maker_out_queue.empty():
            tx_message = (
                self.decision_maker_out_queue.get_nowait()
            )  # type: Optional[TransactionMessage]
            if tx_message is not None:
                skill_callback_ids = tx_message.skill_callback_ids
                for skill_id in skill_callback_ids:
                    handler = self.resources.handler_registry.fetch_internal_handler(
                        skill_id
                    )
                    if handler is not None:
                        logger.debug(
                            "Calling handler {} of skill {}".format(
                                type(handler), skill_id
                            )
                        )
                        handler.handle(cast(Message, tx_message))
                    else:
                        logger.warning(
                            "No internal handler fetched for skill_id={}".format(
                                skill_id
                            )
                        )
