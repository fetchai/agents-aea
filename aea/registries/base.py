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
from typing import Optional, List, Dict, Any, Tuple, cast, Union

from aea.configurations.base import ProtocolId, SkillId, ProtocolConfig, DEFAULT_PROTOCOL_CONFIG_FILE
from aea.configurations.loader import ConfigLoader
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Protocol, Message
from aea.skills.base import Handler, Behaviour, Task, Skill, AgentContext

logger = logging.getLogger(__name__)

PACKAGE_NAME_REGEX = re.compile("^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE)
INTERNAL_PROTOCOL_ID = 'internal'
DECISION_MAKER = 'decision_maker'


class Registry(ABC):
    """This class implements an abstract registry."""

    @abstractmethod
    def register(self, id: Tuple[Any, Any], item: Any) -> None:
        """
        Register an item.

        :param id: the identifier of the item.
        :param item: the item.
        :return: None
        """

    @abstractmethod
    def unregister(self, id: Any) -> None:
        """
        Unregister an item.

        :param id: the identifier of the item.
        :return: None
        """

    @abstractmethod
    def fetch(self, id: Any) -> Optional[Any]:
        """
        Fetch an item.

        :param id: the identifier of the item.
        :return: the Item
        """

    @abstractmethod
    def fetch_all(self) -> Optional[List[Any]]:
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


class ProtocolRegistry(Registry):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._protocols = {}  # type: Dict[ProtocolId, Protocol]

    def register(self, ids: Tuple[ProtocolId, None], protocol: Protocol) -> None:
        """
        Register a protocol.

        :param ids: the tuple of ids
        """
        protocol_id = ids[0]
        self._protocols[protocol_id] = protocol

    def unregister(self, protocol_id: ProtocolId) -> None:
        """Unregister a protocol."""
        self._protocols.pop(protocol_id, None)

    def fetch(self, protocol_id: ProtocolId) -> Optional[Protocol]:
        """
        Fetch the protocol for the envelope.

        :pass protocol_id: the protocol id
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
        protocol_directory_paths.update(Path(directory, "vendor").glob("./*/protocols/*/"))
        # find all protocol directories from protocols/
        protocol_directory_paths.update(Path(directory, "protocols").glob("./*/"))

        protocols_packages_paths = list(filter(lambda x: PACKAGE_NAME_REGEX.match(str(x.name)) and x.is_dir(), protocol_directory_paths))  # type: ignore
        logger.debug("Found the following protocol packages: {}".format(pprint.pformat(map(str, protocol_directory_paths))))
        for protocol_package in protocols_packages_paths:
            try:
                logger.debug("Processing the protocol package '{}'".format(protocol_package))
                self._add_protocol(protocol_package)
            except Exception:
                logger.exception("Not able to add protocol '{}'.".format(protocol_package.name))

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
        serialization_spec = importlib.util.spec_from_file_location("serialization", protocol_directory / "serialization.py")
        serialization_module = importlib.util.module_from_spec(serialization_spec)
        serialization_spec.loader.exec_module(serialization_module)  # type: ignore
        classes = inspect.getmembers(serialization_module, inspect.isclass)
        serializer_classes = list(filter(lambda x: re.match("\\w+Serializer", x[0]), classes))
        serializer_class = serializer_classes[0][1]

        logger.debug("Found serializer class {serializer_class} for protocol {protocol_name}"
                     .format(serializer_class=serializer_class, protocol_name=protocol_name))
        serializer = serializer_class()

        config_loader = ConfigLoader("protocol-config_schema.json", ProtocolConfig)
        protocol_config = config_loader.load(open(protocol_directory / DEFAULT_PROTOCOL_CONFIG_FILE))

        # instantiate the protocol manager.
        protocol = Protocol(protocol_name, serializer, protocol_config)
        self.register((protocol_name, None), protocol)


class HandlerRegistry(Registry):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._handlers = {}  # type: Dict[ProtocolId, Dict[SkillId, Handler]]

    def register(self, ids: Tuple[None, SkillId], handlers: List[Handler]) -> None:
        """
        Register a handler.

        :param ids: the pair (protocol id, skill id).
        :param handlers: the list of handlers.
        :return: None
        """
        skill_id = ids[1]
        for handler in handlers:
            protocol_id = cast(str, handler.SUPPORTED_PROTOCOL)
            if protocol_id in self._handlers.keys():
                logger.debug("More than one handler registered against protocol with id '{}'".format(protocol_id))
            self._handlers.setdefault(protocol_id, {})[skill_id] = handler

    def unregister(self, skill_id: SkillId) -> None:
        """
        Unregister a handler.

        :param skill_id: the skill id.
        :return: None
        """
        protocol_ids_to_remove = set()
        for protocol_id, skill_to_handler_dict in self._handlers.items():
            if skill_id in skill_to_handler_dict.keys():
                self._handlers[protocol_id].pop(skill_id, None)
            if len(self._handlers[protocol_id]) == 0:
                protocol_ids_to_remove.add(protocol_id)

        # clean the dictionary up
        for protocol_id in protocol_ids_to_remove:
            self._handlers.pop(protocol_id, None)

    def fetch(self, protocol_id: ProtocolId) -> Optional[List[Handler]]:
        """
        Fetch the handlers for the protocol_id.

        :param protocol_id: the protocol id
        :return: the list of handlers registered for the protocol_id
        """
        result = self._handlers.get(protocol_id, None)
        if result is None:
            return None
        else:
            # TODO: introduce a filter class which intelligently selects the appropriate handler.
            return [handler for handler in result.values()]

    def fetch_by_skill(self, protocol_id: ProtocolId, skill_id: SkillId) -> Optional[Handler]:
        """
        Fetch the handler for the protocol_id and skill id.

        :param protocol_id: the protocol id
        :param skill_id: the skill id
        :return: the handlers registered for the protocol_id and skill_id
        """
        return self._handlers.get(protocol_id, {}).get(skill_id, None)

    def fetch_all(self) -> List[Handler]:
        """
        Fetch all the handlers.

        :return: the list of handlers.
        """
        result = []
        for skill_id_to_handler_dict in self._handlers.values():
            for handler in skill_id_to_handler_dict.values():
                result.append(handler)
        return result

    def fetch_internal_handler(self, skill_id: SkillId) -> Optional[Handler]:
        """
        Fetch the internal handler.

        :param skill_id: the skill id
        :return: the internal handler registered for the skill id
        """
        return self._handlers.get(INTERNAL_PROTOCOL_ID, {}).get(skill_id, None)

    def setup(self) -> None:
        """
        Set up the handlers in the registry.

        :return: None
        """
        for skill_id_to_handler_dict in self._handlers.values():
            for handler in skill_id_to_handler_dict.values():
                handler.setup()

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for skill_id_to_handler_dict in self._handlers.values():
            for skill_id, handler in skill_id_to_handler_dict.items():
                try:
                    handler.teardown()
                except Exception as e:
                    logger.warning("An error occurred while tearing down handler {}/{}: {}"
                                   .format(skill_id, type(handler).__name__, str(e)))
        self._handlers = {}


class BehaviourRegistry(Registry):
    """This class implements the behaviour registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._behaviours = {}  # type: Dict[SkillId, List[Behaviour]]

    def register(self, ids: Tuple[None, SkillId], behaviours: List[Behaviour]) -> None:
        """
        Register a behaviour.

        :param ids: the skill id.
        :param behaviours: the behaviours of the skill.
        :return: None
        """
        skill_id = ids[1]
        if skill_id in self._behaviours.keys():
            logger.warning("Behaviours already registered with skill id '{}'".format(skill_id))
        self._behaviours.setdefault(skill_id, []).extend(behaviours)

    def unregister(self, skill_id: SkillId) -> None:
        """
        Unregister a behaviour.

        :param skill_id: the skill id.
        :return: None
        """
        self._behaviours.pop(skill_id, None)

    def fetch(self, skill_id: SkillId) -> Optional[List[Behaviour]]:
        """
        Return a behaviour.

        :return: the list of behaviours
        """
        return self._behaviours.get(skill_id, None)

    def fetch_all(self) -> List[Behaviour]:
        """Fetch all the behaviours."""
        return [b for skill_behaviours in self._behaviours.values() for b in skill_behaviours]

    def setup(self) -> None:
        """
        Set up the behaviours in the registry.

        :return: None
        """
        for behaviours in self._behaviours.values():
            for behaviour in behaviours:
                behaviour.setup()

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for skill_id, behaviours in self._behaviours.items():
            for behaviour in behaviours:
                try:
                    behaviour.teardown()
                except Exception as e:
                    logger.warning("An error occurred while tearing down behaviour {}/{}: {}"
                                   .format(skill_id, type(behaviour).__name__, str(e)))
        self._behaviours = {}


class TaskRegistry(Registry):
    """This class implements the task registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._tasks = {}  # type: Dict[SkillId, List[Task]]

    def register(self, ids: Tuple[None, SkillId], tasks: List[Task]) -> None:
        """
        Register a task.

        :param ids: the skill id.
        :param tasks: the tasks list.
        :return: None
        """
        skill_id = ids[1]
        if skill_id in self._tasks.keys():
            logger.warning("Tasks already registered with skill id '{}'".format(skill_id))
        self._tasks.setdefault(skill_id, []).extend(tasks)

    def unregister(self, skill_id: SkillId) -> None:
        """
        Unregister a task.

        :param skill_id: the skill id.
        :return: None
        """
        self._tasks.pop(skill_id, None)

    def fetch(self, skill_id: SkillId) -> Optional[List[Task]]:
        """
        Return a task.

        :return: the list of tasks
        """
        return self._tasks.get(skill_id, None)

    def fetch_all(self) -> List[Task]:
        """
        Return a list of tasks for processing.

        :return: a list of tasks.
        """
        return [t for skill_tasks in self._tasks.values() for t in skill_tasks]

    def setup(self) -> None:
        """
        Set up the tasks in the registry.

        :return: None
        """
        for tasks in self._tasks.values():
            for task in tasks:
                task.setup()

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for skill_id, tasks in self._tasks.items():
            for task in tasks:
                try:
                    task.teardown()
                except Exception as e:
                    logger.warning("An error occurred while tearing down task {}/{}: {}"
                                   .format(skill_id, type(task).__name__, str(e)))
        self._tasks = {}


class Resources(object):
    """This class implements the resources of an AEA."""

    def __init__(self, directory: Optional[Union[str, os.PathLike]] = None):
        """Instantiate the resources."""
        self._directory = str(Path(directory).absolute()) if directory is not None else str(Path(".").absolute())
        self.protocol_registry = ProtocolRegistry()
        self.handler_registry = HandlerRegistry()
        self.behaviour_registry = BehaviourRegistry()
        self.task_registry = TaskRegistry()
        self._skills = dict()  # type: Dict[SkillId, Skill]

        self._registries = [self.protocol_registry, self.handler_registry, self.behaviour_registry, self.task_registry]

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
        logger.debug("Found the following skill packages: {}".format(pprint.pformat(map(str, skills_packages_paths))))
        for skill_directory in skills_packages_paths:
            logger.debug("Processing the following skill directory: '{}".format(skill_directory))
            try:
                skill = Skill.from_dir(str(skill_directory), agent_context)
                assert skill is not None
                self.add_skill(skill)
            except Exception as e:
                logger.warning("A problem occurred while parsing the skill directory {}. Exception: {}"
                               .format(skill_directory, str(e)))

    def add_skill(self, skill: Skill):
        """Add a skill to the set of resources."""
        skill_id = skill.config.name
        self._skills[skill_id] = skill
        if skill.handlers is not None:
            self.handler_registry.register((None, skill_id), cast(List[Handler], list(skill.handlers.values())))
        if skill.behaviours is not None:
            self.behaviour_registry.register((None, skill_id), cast(List[Behaviour], list(skill.behaviours.values())))
        if skill.tasks is not None:
            self.task_registry.register((None, skill_id), cast(List[Task], list(skill.tasks.values())))

    def get_skill(self, skill_id: SkillId) -> Optional[Skill]:
        """Get the skill."""
        return self._skills.get(skill_id, None)

    def remove_skill(self, skill_id: SkillId):
        """Remove a skill from the set of resources."""
        self._skills.pop(skill_id, None)
        self.handler_registry.unregister(skill_id)
        self.behaviour_registry.unregister(skill_id)
        self.task_registry.unregister(skill_id)

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

    def get_active_handlers(self, protocol_id: str) -> Optional[List[Handler]]:
        """
        Get active handlers.

        :param protocol_id: the protocol id
        :return: list of handlers
        """
        handlers = self.resources.handler_registry.fetch(protocol_id)
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
            tx_message = self.decision_maker_out_queue.get_nowait()  # type: Optional[TransactionMessage]
            if tx_message is not None:
                skill_callback_ids = tx_message.skill_callback_ids
                for skill_id in skill_callback_ids:
                    handler = self.resources.handler_registry.fetch_internal_handler(skill_id)
                    if handler is not None:
                        logger.debug("Calling handler {} of skill {}".format(type(handler), skill_id))
                        handler.handle(cast(Message, tx_message))
                    else:
                        logger.warning("No internal handler fetched for skill_id={}".format(skill_id))
