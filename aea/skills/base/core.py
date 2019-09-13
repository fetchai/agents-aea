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

"""This module contains the base classes for the skills."""
import importlib.util
import inspect
import logging
import os
import pprint
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any, cast

from aea.skills.base.config import BehaviourConfig, HandlerConfig, TaskConfig, SkillConfig
from aea.skills.base.loader import ConfigLoader
from aea.mail.base import OutBox, ProtocolId, Envelope
from aea.protocols.base.protocol import Protocol

logger = logging.getLogger(__name__)

DEFAULT_SKILL_CONFIG_FILE = "skill.yaml"
SkillId = str


class Context:
    """Save relevant data for the agent."""

    def __init__(self, agent_name: str, outbox: OutBox):
        """Initialize a context object."""
        self.agent_name = agent_name
        self.outbox = outbox
        self.skill_loader = ConfigLoader("skill-config_schema.json", SkillConfig)


class Behaviour(ABC):
    """This class implements an abstract behaviour."""

    def __init__(self, **kwargs):
        """
        Initialize a behaviour.

        :param kwargs: keyword arguments.
        """

    @abstractmethod
    def act(self) -> None:
        """
        Implement the behaviour.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Implement the behaviour teardown.

        :return: None
        """

    @classmethod
    def parse_module(cls, path: str, behaviours_configs: List[BehaviourConfig]) -> List['Behaviour']:
        """
        Parse the behaviours module.

        :param path: path to the Python module containing the Behaviour classes.
        :param behaviours_configs: a list of behaviour configurations.
        :return: a list of Behaviour.
        """
        behaviours = []
        behaviours_spec = importlib.util.spec_from_file_location("behaviours", location=path)
        behaviour_module = importlib.util.module_from_spec(behaviours_spec)
        behaviours_spec.loader.exec_module(behaviour_module)  # type: ignore
        classes = inspect.getmembers(behaviour_module, inspect.isclass)
        behaviours_classes = list(filter(lambda x: re.match("\\w+Behaviour", x[0]), classes))

        name_to_class = dict(behaviours_classes)
        for behaviour_config in behaviours_configs:
            behaviour_class_name = cast(str, behaviour_config.class_name)
            logger.debug("Processing behaviour {}".format(behaviour_class_name))
            behaviour_class = name_to_class.get(behaviour_class_name, None)
            if behaviour_class is None:
                logger.warning("Behaviour '{}' cannot be found.".format(behaviour_class))
            else:
                args = behaviour_config.args
                behaviour = behaviour_class(**args)
                behaviours.append(behaviour)

        return behaviours


class Handler(ABC):
    """This class implements an abstract behaviour."""

    SUPPORTED_PROTOCOL = None  # type: Optional[ProtocolId]

    context: Context

    def __init__(self, *args, **kwargs):
        """Initialize a handler object."""
        self.config = kwargs

    @abstractmethod
    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """

    @classmethod
    def parse_module(cls, path: str, handler_config: HandlerConfig) -> Optional['Handler']:
        """
        Parse the handler module.

        :param path: path to the Python module containing the Handler class.
        :param handler_config: the handler configuration.
        :return: an handler, or None if the parsing fails.
        """
        handler_spec = importlib.util.spec_from_file_location("handler", location=path)
        handler_module = importlib.util.module_from_spec(handler_spec)
        handler_spec.loader.exec_module(handler_module)  # type: ignore
        classes = inspect.getmembers(handler_module, inspect.isclass)
        handler_classes = list(filter(lambda x: re.match("\\w+Handler", x[0]), classes))

        name_to_class = dict(handler_classes)
        handler_class_name = cast(str, handler_config.class_name)
        logger.debug("Processing handler {}".format(handler_class_name))
        handler_class = name_to_class.get(handler_class_name, None)
        if handler_class is None:
            logger.warning("Handler '{}' cannot be found.".format(handler_class_name))
            return None
        else:
            args = handler_config.args
            handler = handler_class(**args)
            return handler


class Task(ABC):
    """This class implements an abstract task."""

    def __init__(self, **kwargs):
        """
        Initialize a task.

        :param kwargs: keyword arguments.
        """

    @abstractmethod
    def execute(self) -> None:
        """
        Run the task logic.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Teardown the task.

        :return: None
        """

    @classmethod
    def parse_module(cls, path: str, tasks_configs: List[TaskConfig]) -> List['Task']:
        """
        Parse the tasks module.

        :param path: path to the Python module containing the Task classes.
        :param tasks_configs: a list of tasks configurations.
        :return: a list of Tasks.
        """
        tasks = []
        tasks_spec = importlib.util.spec_from_file_location("tasks", location=path)
        task_module = importlib.util.module_from_spec(tasks_spec)
        tasks_spec.loader.exec_module(task_module)  # type: ignore
        classes = inspect.getmembers(task_module, inspect.isclass)
        tasks_classes = list(filter(lambda x: re.match("\\w+Task", x[0]), classes))

        name_to_class = dict(tasks_classes)
        for task_config in tasks_configs:
            task_class_name = task_config.class_name
            logger.debug("Processing task {}".format(task_class_name))
            task_class = name_to_class.get(task_class_name, None)
            if task_class is None:
                logger.warning("Task '{}' cannot be found.".format(task_class))
            else:
                args = task_config.args
                task = task_class(**args)
                tasks.append(task)

        return tasks


class Skill:
    """This class implements a skill."""

    def __init__(self, config: SkillConfig,
                 handler: Optional[Handler],
                 behaviours: Optional[List[Behaviour]],
                 tasks: Optional[List[Task]]):
        """
        Initialize a skill.

        :param config: the skill configuration.
        :param handler: the handler to handle incoming envelopes.
        :param behaviours: the list of behaviours that defines the proactive component of the agent.
        :param tasks: the list of tasks executed at every iteration of the main loop.
        """
        self.config = config
        self.handler = handler
        self.behaviours = behaviours
        self.tasks = tasks

    @classmethod
    def from_dir(cls, directory: str, context: Context) -> Optional['Skill']:
        """
        Load a skill from a directory.

        :param directory: the skill
        :return: the Skill object. None if the parsing failed.
        """
        # check if there is the config file. If not, then return None.
        skill_config = context.skill_loader.load(open(os.path.join(directory)))
        if skill_config is None:
            return None

        skills_spec = importlib.util.spec_from_file_location("skill_module", os.path.join(directory, "__init__.py"))
        if skills_spec is None:
            logger.warning("No skill found.")
            return None

        skills_packages = list(filter(lambda x: not x.startswith("__"), skills_spec.loader.contents()))  # type: ignore
        logger.debug("Processing the following skill package: {}".format(skills_packages))

        handler = Handler.parse_module(os.path.join(directory, "handler.py"), skill_config.handler)
        if handler is not None:
            handler.context = context

        behaviours_configurations = list(dict(skill_config.behaviours.read_all()).values())
        behaviours = Behaviour.parse_module(os.path.join(directory, "behaviours.py"), behaviours_configurations)

        tasks_configurations = list(dict(skill_config.tasks.read_all()).values())
        tasks = Task.parse_module(os.path.join(directory, "tasks.py"), tasks_configurations)

        skill = Skill(skill_config, handler, behaviours, tasks)
        return skill


class Registry(ABC):
    """This class implements an abstract registry."""

    @abstractmethod
    def register(self, id: Any, item: Any) -> None:
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
    def fetch_all(self) -> List[Any]:
        """
        Fetch all the items.

        :return: the list of items.
        """

    @abstractmethod
    def populate(self, directory: str) -> None:
        """
        Load into the registry as specified in the config and apply consistency checks.

        :param directory: the filepath to the agent's resource directory.
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

    def register(self, protocol_id: ProtocolId, protocol: Protocol) -> None:
        """Register a protocol."""
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
        protocols_spec = importlib.util.spec_from_file_location("protocols",
                                                                os.path.join(directory, "protocols", "__init__.py"))
        path = cast(str, protocols_spec.origin)
        if protocols_spec is None or not os.path.exists(path):
            logger.warning("No protocol found.")
            return

        protocols_packages = list(filter(lambda x: not x.startswith("__"), protocols_spec.loader.contents()))  # type: ignore
        logger.debug("Processing the following protocol package: {}".format(protocols_packages))
        for protocol_name in protocols_packages:
            try:
                self._add_protocol(directory, protocol_name)
            except Exception:
                logger.exception("Not able to add protocol {}.".format(protocol_name))

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        self._protocols = {}

    def _add_protocol(self, directory: str, protocol_name: str):
        """
        Add a protocol.

        :param directory: the agent's resources directory.
        :param protocol_name: the name of the protocol to be added.
        :return: None
        """
        # get the serializer
        serialization_spec = importlib.util.spec_from_file_location("serialization",
                                                                    os.path.join(directory, "protocols", protocol_name, "serialization.py"))
        serialization_module = importlib.util.module_from_spec(serialization_spec)
        serialization_spec.loader.exec_module(serialization_module)  # type: ignore
        classes = inspect.getmembers(serialization_module, inspect.isclass)
        serializer_classes = list(filter(lambda x: re.match("\\w+Serializer", x[0]), classes))
        serializer_class = serializer_classes[0][1]

        logger.debug("Found serializer class {serializer_class} for protocol {protocol_name}"
                     .format(serializer_class=serializer_class, protocol_name=protocol_name))
        serializer = serializer_class()

        # instantiate the protocol manager.
        protocol = Protocol(protocol_name, serializer)
        self.register(protocol_name, protocol)


class HandlerRegistry(Registry):
    """This class implements the handlers registry."""

    def __init__(self, context: Context) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._handlers = {}  # type: Dict[SkillId, Handler]
        self.context = context

    def register(self, skill_id: SkillId, handler: Handler) -> None:
        """
        Register a behaviour.

        :param skill_id: the skill id.
        :param handler: the handler.
        :return: None
        """
        if skill_id in self._handlers.keys():
            logger.warning("Another handler already registered with skill id '{}'".format(skill_id))
        self._handlers[skill_id] = handler

    def unregister(self, skill_id: SkillId) -> None:
        """
        Unregister a handler.

        :param skill_id: the skill id.
        :return: None
        """
        self._handlers.pop(skill_id, None)

    def fetch(self, protocol_id: ProtocolId) -> Optional[Handler]:
        """
        Fetch the handler for the protocol_id.

        :param protocol_id: the protocol id
        :return: the handler
        """
        return self._handlers.get(protocol_id, None)

    def fetch_all(self) -> List[Handler]:
        """Fetch all the handlers."""
        return list(self._handlers.values())

    def populate(self, directory: str) -> None:
        """
        Load the handlers as specified in the config and apply consistency checks.

        :param directory: the agent's resources directory.
        :return: None
        """
        skills_spec = importlib.util.spec_from_file_location("skills",
                                                             os.path.join(directory, "skills", "__init__.py"))
        if skills_spec is None:
            logger.warning("No skill found.")
            return

        skills_packages = list(filter(lambda x: not x.startswith("__"), skills_spec.loader.contents()))  # type: ignore
        logger.debug("Processing the following skill package: {}".format(skills_packages))
        for skill_name in skills_packages:
            try:
                self._add_skill_handler(directory, skill_name)
            except Exception:
                logger.exception("Not able to add handler for skill {}.".format(skill_name))

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for handler in self._handlers.values():
            handler.teardown()
        self._handlers = {}

    def _add_skill_handler(self, directory: str, skill_name: str) -> None:
        """
        Add a skill handler.

        :param directory: the agent's resources directory.
        :param skill_name: the skill's name
        :return: None
        """
        handler_spec = importlib.util.spec_from_file_location("handler",
                                                              os.path.join(directory, "skills", skill_name, "handler.py"))
        handler_module = importlib.util.module_from_spec(handler_spec)
        handler_spec.loader.exec_module(handler_module)  # type: ignore
        classes = inspect.getmembers(handler_module, inspect.isclass)
        handler_classes = list(filter(lambda x: re.match("\\w+Handler", x[0]), classes))
        handler_class = handler_classes[0][1]

        logger.debug("Found handler class {handler_class} for skill {skill_name}"
                     .format(handler_class=handler_class, skill_name=skill_name))
        handler = handler_class(self.context)
        self.register(skill_name, handler)


class BehaviourRegistry(Registry):
    """This class implements the behaviour registry."""

    def __init__(self, context: Context) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._behaviours = {}  # type: Dict[SkillId, List[Behaviour]]
        self.context = context

    def register(self, skill_id: SkillId, behaviours: List[Behaviour]) -> None:
        """
        Register a behaviour.

        :param skill_id: the skill id.
        :param behaviours: the behaviours of the skill.
        :return: None
        """
        if skill_id in self._behaviours.keys():
            logger.warning("Behaviours already registered with skill id '{}'".format(skill_id))
        self._behaviours[skill_id] = behaviours

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

    def populate(self, directory: str) -> None:
        """
        Load the behaviours as specified in the config and apply consistency checks.

        :param directory: the agent's resources directory.
        :return: None
        """
        logger.debug("Populating the behaviour registry. Resource directory: {}".format(directory))
        skills_spec = importlib.util.spec_from_file_location("skills",
                                                             os.path.join(directory, "skills", "__init__.py"))
        if skills_spec is None:
            logger.warning("No skill found.")
            return

        skills_packages = list(filter(lambda x: not x.startswith("__"), skills_spec.loader.contents()))  # type: ignore
        logger.debug("Processing the following skill package: {}".format(skills_packages))
        for skill_name in skills_packages:
            try:
                self._add_skill_behaviours(directory, skill_name)
            except Exception:
                logger.exception("Not able to add handler for skill {}.".format(skill_name))

    def _add_skill_behaviours(self, directory: str, skill_name: str) -> None:
        """
        Add skill behaviours.

        :param directory: the agent's resources directory.
        :param skill_name: the skill's name
        :return: None
        """
        behaviours_spec = importlib.util.spec_from_file_location("behaviours",
                                                                 os.path.join(directory, "skills", skill_name, "behaviours.py"))
        behaviour_module = importlib.util.module_from_spec(behaviours_spec)
        behaviours_spec.loader.exec_module(behaviour_module)  # type: ignore
        classes = inspect.getmembers(behaviour_module, inspect.isclass)
        behaviours_classes = list(filter(lambda x: re.match("\\w+Behaviour", x[0]), classes))
        for _, behaviour_class in behaviours_classes:
            logger.debug("Found behaviour class {behaviour_class} for skill {skill_name}"
                         .format(behaviour_class=behaviour_class, skill_name=skill_name))
            behaviour = behaviour_class()
            self.register(skill_name, behaviour)

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for behaviours in self._behaviours.values():
            for behaviour in behaviours:
                behaviour.teardown()
        self._behaviours = {}


class TaskRegistry(Registry):
    """This class implements the task registry."""

    def __init__(self, context: Context) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._tasks = {}  # type: Dict[SkillId, List[Task]]
        self.context = context

    def register(self, skill_id: SkillId, tasks: List[Task]) -> None:
        """
        Register a task.

        :param skill_id: the skill id.
        :param tasks: the tasks list.
        :return: None
        """
        if skill_id in self._tasks.keys():
            logger.warning("Tasks already registered with skill id '{}'".format(skill_id))
        self._tasks[skill_id] = tasks

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

    def populate(self, directory: str) -> None:
        """
        Load the tasks as specified in the config and apply consistency checks.

        :param directory: the agent's resources directory.
        :return: None
        """
        logger.debug("Populating the task registry. Resource directory: {}".format(directory))
        skills_spec = importlib.util.spec_from_file_location("skills", os.path.join(directory, "skills", "__init__.py"))
        if skills_spec is None:
            logger.warning("No skill found.")
            return

        skills_packages = list(filter(lambda x: not x.startswith("__"), skills_spec.loader.contents()))  # type: ignore
        logger.debug("Processing the following skill package: {}".format(skills_packages))
        for skill_name in skills_packages:
            try:
                self._add_skill_tasks(directory, skill_name)
            except Exception:
                logger.exception("Not able to add handler for skill {}.".format(skill_name))

    def _add_skill_tasks(self, directory, skill_name):
        """
        Add skill tasks.

        :param directory: the agent's resources directory.
        :param skill_name: the skill's name
        :return: None
        """
        tasks_spec = importlib.util.spec_from_file_location("tasks",
                                                            os.path.join(directory, "skills", skill_name, "tasks.py"))
        task_module = importlib.util.module_from_spec(tasks_spec)
        tasks_spec.loader.exec_module(task_module)
        classes = inspect.getmembers(task_module, inspect.isclass)
        task_classes = list(filter(lambda x: re.match("\\w+Task", x[0]), classes))
        for _, task_class in task_classes:
            logger.debug("Found task class {task_class} for skill {skill_name}"
                         .format(task_class=task_class, skill_name=skill_name))
            task = task_class()
            self.register(skill_name, task)

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for tasks in self._tasks.values():
            for task in tasks:
                task.teardown()
        self._tasks = {}


class Resources(object):
    """This class implements the resources of an AEA."""

    def __init__(self, context: Context):
        """Instantiate the resources."""
        self.context = context
        self.protocol_registry = ProtocolRegistry()
        self.handler_registry = HandlerRegistry(context)
        self.behaviour_registry = BehaviourRegistry(context)
        self.task_registry = TaskRegistry(context)
        self._skills = dict()  # type: Dict[SkillId, Skill]

        self._registries = [self.protocol_registry, self.handler_registry, self.behaviour_registry, self.task_registry]

    @classmethod
    def from_resource_dir(cls, directory: str, context: Context) -> Optional['Resources']:
        """
        Parse the resource directory.

        :param directory: the agent's resources directory.
        :param context: the agent's context object
        :return: None
        """
        resource = Resources(context)
        resource.protocol_registry.populate(directory)
        resource.populate_skills(directory, context)
        return resource

    def populate_skills(self, directory: str, context: Context) -> None:
        """
        Populate skills.

        :param directory: the agent's resources directory.
        :param context: the agent's context object
        :return: None
        """
        root_skill_directory = os.path.join(directory, "skills")
        if not os.path.exists(root_skill_directory):
            logger.warning("No skill found.")
            return

        skill_directories = [str(x) for x in Path(root_skill_directory).iterdir() if x.is_dir()]
        logger.debug("Processing the following skill directories: {}".format(pprint.pformat(skill_directories)))
        for skill_directory in skill_directories:
            try:
                skill = Skill.from_dir(skill_directory, context)
                assert skill is not None
                self.add_skill(skill)
            except Exception as e:
                logger.warning("A problem occurred while parsing the skill directory {}. Exception: {}"
                               .format(skill_directory, str(e)))

    def add_skill(self, skill: Skill):
        """Add a skill to the set of resources."""
        skill_id = skill.config.name
        self._skills[skill_id] = skill
        if skill.handler is not None:
            self.handler_registry.register(skill_id, cast(Handler, skill.handler))
        if skill.behaviours is not None:
            self.behaviour_registry.register(skill_id, cast(List[Behaviour], skill.behaviours))
        if skill.tasks is not None:
            self.task_registry.register(skill_id, cast(List[Task], skill.tasks))

    def remove_skill(self, skill_id: SkillId):
        """Remove a skill from the set of resources."""
        self._skills.pop(skill_id, None)
        self.handler_registry.unregister(skill_id)
        self.behaviour_registry.unregister(skill_id)
        self.task_registry.unregister(skill_id)

    def teardown(self):
        """
        Teardown the resources.

        :return: None
        """
        for r in self._registries:
            r.teardown()
