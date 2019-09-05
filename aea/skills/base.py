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
import re
from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from aea.mail.base import OutBox, ProtocolId, Envelope
from aea.protocols.base.protocol import Protocol

logger = logging.getLogger(__name__)

SkillId = str


class Context:
    """Save relevant data for the agent."""

    def __init__(self, agent_name: str, outbox: OutBox):
        """Initialize a context object."""
        self.agent_name = agent_name
        self.outbox = outbox


class Behaviour(ABC):
    """This class implements an abstract behaviour."""

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


class Handler(ABC):
    """This class implements an abstract behaviour."""

    SUPPORTED_PROTOCOL = None  # type: Optional[ProtocolId]

    def __init__(self, context: Context):
        """Initialize a handler object."""
        self.context = context

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


class Task(ABC):
    """This class implements an abstract task."""

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


class Skill:
    """This class implements a skill."""

    def __init__(self, handler: Handler,
                 behaviours: List[Behaviour],
                 tasks: List[Task]):
        """
        Initialize a skill.

        :param handler: the handler to handle incoming envelopes.
        :param behaviours: the list of behaviours that defines the proactive component of the agent.
        :param tasks: the list of tasks executed at every iteration of the main loop.
        """
        self.handler = handler
        self.behaviours = behaviours
        self.tasks = tasks


class Registry(ABC):
    """This class implements an abstract registry."""

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

    def populate(self, directory: str) -> None:
        """
        Load the handlers as specified in the config and apply consistency checks.

        :param directory: the filepath to the agent's resource directory.
        :return: None
        """
        protocols_spec = importlib.util.spec_from_file_location("protocols",
                                                                os.path.join(directory, "protocols", "__init__.py"))
        if protocols_spec is None:
            logger.warning("No protocol found.")
            return

        protocols_packages = list(filter(lambda x: not x.startswith("__"), protocols_spec.loader.contents()))
        logger.debug("Processing the following protocol package: {}".format(protocols_packages))
        for protocol_name in protocols_packages:
            try:
                self._add_protocol(directory, protocol_name)
            except Exception:
                logger.exception("Not able to add protocol {}.".format(protocol_name))

    def fetch_protocol(self, protocol_id: ProtocolId) -> Optional[Protocol]:
        """
        Fetch the protocol for the envelope.

        :pass protocol_id: the protocol id
        :return: the protocol id or None if the protocol is not registered
        """
        return self._protocols.get(protocol_id, None)

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
        serialization_spec.loader.exec_module(serialization_module)
        classes = inspect.getmembers(serialization_module, inspect.isclass)
        serializer_classes = list(filter(lambda x: re.match("\\w+Serializer", x[0]), classes))
        serializer_class = serializer_classes[0][1]

        logger.debug("Found serializer class {serializer_class} for protocol {protocol_name}"
                     .format(serializer_class=serializer_class, protocol_name=protocol_name))
        serializer = serializer_class()

        # instantiate the protocol manager.
        protocol = Protocol(protocol_name, serializer)
        self._protocols[protocol_name] = protocol


class HandlerRegistry(Registry):
    """This class implements the handlers registry."""

    def __init__(self, context: Context) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._handlers = {}  # type: Dict[SkillId, Handler]
        self.context = context

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

        skills_packages = list(filter(lambda x: not x.startswith("__"), skills_spec.loader.contents()))
        logger.debug("Processing the following skill package: {}".format(skills_packages))
        for skill_name in skills_packages:
            try:
                self._add_skill_handler(directory, skill_name)
            except Exception:
                logger.exception("Not able to add handler for skill {}.".format(skill_name))

    def fetch_handler(self, protocol_id: ProtocolId) -> Optional[Handler]:
        """
        Fetch the handler for the protocol_id.

        :param protocol_id: the protocol id
        :return: the handler
        """
        return self._handlers.get(protocol_id, None)

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for handler in self._handlers.values():
            handler.teardown()
        self._handlers = {}

    def _add_skill_handler(self, directory, skill_name):
        """Add a skill handler."""

        handler_spec = importlib.util.spec_from_file_location("handler",
                                                              os.path.join(directory, "skills", skill_name, "handler.py"))
        handler_module = importlib.util.module_from_spec(handler_spec)
        handler_spec.loader.exec_module(handler_module)
        classes = inspect.getmembers(handler_module, inspect.isclass)
        handler_classes = list(filter(lambda x: re.match("\\w+Handler", x[0]), classes))
        handler_class = handler_classes[0][1]

        logger.debug("Found handler class {handler_class} for skill {skill_name}"
                     .format(handler_class=handler_class, skill_name=skill_name))
        handler = handler_class(self.context)
        self._handlers[handler.SUPPORTED_PROTOCOL] = handler


class BehaviourRegistry(Registry):
    """This class implements the behaviour registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._behaviours = {}  # type: Dict[SkillId, Behaviour]

    def populate(self, directory: str) -> None:
        """
        Load the behaviours as specified in the config and apply consistency checks.

        :param directory: the agent's resources directory.
        :return: None
        """
        pass

    def fetch_behaviours(self) -> List[Behaviour]:
        """
        Return a list of behaviours for processing.

        :return: the list of behaviours
        """
        return []

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for behaviour in self._behaviours.values():
            behaviour.teardown()
        self._behaviours = {}


class TaskRegistry(Registry):
    """This class implements the task registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._tasks = {}  # type: Dict[SkillId, Task]

    def populate(self, directory: str) -> None:
        """
        Load the tasks as specified in the config and apply consistency checks.

        :param directory: the agent's resources directory.
        :return: None
        """
        pass

    def fetch_tasks(self) -> List[Task]:
        """
        Return a list of tasks for processing.

        :return: a list of tasks.
        """
        return []

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for task in self._tasks.values():
            task.teardown()
        self._tasks = {}


class Resources(object):
    """This class implements the resources of an AEA."""

    def __init__(self, context: Context):
        """Instantiate the resources."""
        self.context = context
        self.protocol_registry = ProtocolRegistry()
        self.handler_registry = HandlerRegistry(context)
        self.behaviour_registry = BehaviourRegistry()
        self.task_registry = TaskRegistry()
        self._skills = dict()  # type: Dict[SkillId, Skill]

        self._registries = [self.protocol_registry, self.handler_registry, self.behaviour_registry, self.task_registry]

    def populate(self, directory: str) -> None:
        """
        Populate the resources based on the registries.

        :param directory: the agent's resources directory.
        :return: None
        """
        for r in self._registries:
            r.populate(directory)

    def teardown(self):
        """
        Teardown the resources.

        :return: None
        """
        for r in self._registries:
            r.teardown()

