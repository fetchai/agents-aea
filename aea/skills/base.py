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
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue
from typing import Optional, List, Dict, Any, cast

from aea.configurations.base import BehaviourConfig, HandlerConfig, TaskConfig, SharedClassConfig, SkillConfig, ProtocolId, DEFAULT_SKILL_CONFIG_FILE
from aea.configurations.loader import ConfigLoader
from aea.context.base import AgentContext
from aea.decision_maker.base import OwnershipState, Preferences
from aea.mail.base import OutBox, Envelope

logger = logging.getLogger(__name__)


class SkillContext:
    """This class implements the context of a skill."""

    def __init__(self, agent_context: AgentContext):
        """
        Initialize a skill context.

        :param agent_context: the agent's context
        """
        self._agent_context = agent_context
        self._skill = None  # type: Optional[Skill]

    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self._agent_context.agent_name

    @property
    def agent_public_key(self) -> str:
        """Get public key."""
        return self._agent_context.public_key

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._agent_context.outbox

    @property
    def decision_maker_message_queue(self) -> Queue:
        """Get message queue of decision maker."""
        return self._agent_context.decision_maker_message_queue

    @property
    def ownership_state(self) -> OwnershipState:
        """Get ownership state."""
        return self._agent_context.ownership_state

    @property
    def preferences(self) -> Preferences:
        """Get preferences."""
        return self._agent_context.preferences

    @property
    def handlers(self) -> Optional[List['Handler']]:
        """Get handlers of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return self._skill.handlers

    @property
    def behaviours(self) -> Optional[List['Behaviour']]:
        """Get behaviours of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return self._skill.behaviours

    @property
    def tasks(self) -> Optional[List['Task']]:
        """Get tasks of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return self._skill.tasks


class Behaviour(ABC):
    """This class implements an abstract behaviour."""

    def __init__(self, **kwargs):
        """
        Initialize a behaviour.

        :param skill_context: the skill context
        :param kwargs: keyword arguments
        """
        self._context = kwargs.pop('skill_context')  # type: SkillContext
        self._config = kwargs

    @property
    def context(self) -> SkillContext:
        """Get the context of the behaviour."""
        return self._context

    @property
    def config(self) -> Dict[Any, Any]:
        """Get the config of the behaviour."""
        return self._config

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
    def parse_module(cls, path: str, behaviours_configs: List[BehaviourConfig], skill_context: SkillContext) -> List['Behaviour']:
        """
        Parse the behaviours module.

        :param path: path to the Python module containing the Behaviour classes.
        :param behaviours_configs: a list of behaviour configurations.
        :param skill_context: the skill context
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
                assert 'skill_context' not in args.keys(), "'skill_context' is a reserved key. Please rename your arguments!"
                args['skill_context'] = skill_context
                behaviour = behaviour_class(**args)
                behaviours.append(behaviour)

        return behaviours


class Handler(ABC):
    """This class implements an abstract behaviour."""

    SUPPORTED_PROTOCOL = None  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """
        Initialize a handler object.

        :param skill_context: the skill context
        :param kwargs: keyword arguments
        """
        self._context = kwargs.pop('skill_context')  # type: SkillContext
        self._config = kwargs

    @property
    def context(self) -> SkillContext:
        """Get the context of the handler."""
        return self._context

    @property
    def config(self) -> Dict[Any, Any]:
        """Get the config of the handler."""
        return self._config

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
    def parse_module(cls, path: str, handler_configs: List[HandlerConfig], skill_context: SkillContext) -> List['Handler']:
        """
        Parse the handler module.

        :param path: path to the Python module containing the Handler class.
        :param handler_configs: the list of handler configurations.
        :param skill_context: the skill context
        :return: an handler, or None if the parsing fails.
        """
        handlers = []
        handler_spec = importlib.util.spec_from_file_location("handlers", location=path)
        handler_module = importlib.util.module_from_spec(handler_spec)
        handler_spec.loader.exec_module(handler_module)  # type: ignore
        classes = inspect.getmembers(handler_module, inspect.isclass)
        handler_classes = list(filter(lambda x: re.match("\\w+Handler", x[0]), classes))

        name_to_class = dict(handler_classes)
        for handler_config in handler_configs:
            handler_class_name = cast(str, handler_config.class_name)
            logger.debug("Processing handler {}".format(handler_class_name))
            handler_class = name_to_class.get(handler_class_name, None)
            if handler_class is None:
                logger.warning("Handler '{}' cannot be found.".format(handler_class_name))
            else:
                args = handler_config.args
                assert 'skill_context' not in args.keys(), "'skill_context' is a reserved key. Please rename your arguments!"
                args['skill_context'] = skill_context
                handler = handler_class(**args)
                handlers.append(handler)

        return handlers


class Task(ABC):
    """This class implements an abstract task."""

    def __init__(self, *args, **kwargs):
        """
        Initialize a task.

        :param skill_context: the skill context
        :param kwargs: keyword arguments.
        """
        self._context = kwargs.pop('skill_context')  # type: SkillContext
        self._config = kwargs

    @property
    def context(self) -> SkillContext:
        """Get the context of the task."""
        return self._context

    @property
    def config(self) -> Dict[Any, Any]:
        """Get the config of the task."""
        return self._config

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
    def parse_module(cls, path: str, tasks_configs: List[TaskConfig], skill_context: SkillContext) -> List['Task']:
        """
        Parse the tasks module.

        :param path: path to the Python module containing the Task classes.
        :param tasks_configs: a list of tasks configurations.
        :param skill_context: the skill context
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
                assert 'skill_context' not in args.keys(), "'skill_context' is a reserved key. Please rename your arguments!"
                args['skill_context'] = skill_context
                task = task_class(**args)
                tasks.append(task)

        return tasks


class SharedClass(ABC):
    """This class implements an abstract shared class."""

    def __init__(self, *args, **kwargs):
        """
        Initialize a task.

        :param skill_context: the skill context
        :param kwargs: keyword arguments.
        """
        self._context = kwargs.pop('skill_context')  # type: SkillContext
        self._config = kwargs

    @property
    def context(self) -> SkillContext:
        """Get the context of the task."""
        return self._context

    @property
    def config(self) -> Dict[Any, Any]:
        """Get the config of the task."""
        return self._config

    @classmethod
    def parse_module(cls, path: str, shared_classes_configs: List[SharedClassConfig], skill_context: SkillContext) -> List['SharedClass']:
        """
        Parse the tasks module.

        :param path: path to the Python skill module.
        :param shared_classes_configs: a list of shared class configurations.
        :param skill_context: the skill context
        :return: a list of SharedClass.
        """
        instances = []
        shared_classes = []

        shared_classes_names = set(config.class_name for config in shared_classes_configs)

        # get all Python modules except the standard ones
        ignore_regex = "|".join(["handlers.py", "behaviours.py", "tasks.py", "skill.yaml", "__.*"])
        module_paths = set(map(str, filter(lambda x: not re.match(ignore_regex, x.name), Path(path).iterdir())))

        for module_path in module_paths:
            module_name = module_path.replace(".py", "")
            shared_class_spec = importlib.util.spec_from_file_location(module_name, location=module_path)
            shared_class_module = importlib.util.module_from_spec(shared_class_spec)
            shared_class_spec.loader.exec_module(shared_class_module)  # type: ignore
            classes = inspect.getmembers(shared_class_module, inspect.isclass)
            filtered_classes = list(
                filter(
                    lambda x:
                        any(re.match(shared, x[0]) for shared in shared_classes_names)
                        and
                        SharedClass in inspect.getmro(x[1]),
                    classes)
            )
            shared_classes.extend(filtered_classes)

        name_to_class = dict(shared_classes)
        for shared_class_config in shared_classes_configs:
            shared_class_name = shared_class_config.class_name
            logger.debug("Processing shared class {}".format(shared_class_name))
            shared_class = name_to_class.get(shared_class_name, None)
            if shared_class is None:
                logger.warning("SharedClass '{}' cannot be found.".format(shared_class))
            else:
                args = shared_class_config.args
                assert 'skill_context' not in args.keys(), "'skill_context' is a reserved key. Please rename your arguments!"
                args['skill_context'] = skill_context
                shared_class_instance = shared_class(**args)
                instances.append(shared_class_instance)
                setattr(skill_context, shared_class_name.lower(), shared_class_instance)
        return instances


class Skill:
    """This class implements a skill."""

    def __init__(self, config: SkillConfig,
                 skill_context: SkillContext,
                 handlers: Optional[List[Handler]],
                 behaviours: Optional[List[Behaviour]],
                 tasks: Optional[List[Task]],
                 shared_classes: Optional[List[SharedClass]]):
        """
        Initialize a skill.

        :param config: the skill configuration.
        :param handlers: the list of handlers to handle incoming envelopes.
        :param behaviours: the list of behaviours that defines the proactive component of the agent.
        :param tasks: the list of tasks executed at every iteration of the main loop.
        :param shared_classes: the list of classes shared across tasks, behaviours and
        """
        self.config = config
        self.skill_context = skill_context
        self.handlers = handlers
        self.behaviours = behaviours
        self.tasks = tasks
        self.shared_classes = shared_classes

    @classmethod
    def from_dir(cls, directory: str, agent_context: AgentContext) -> Optional['Skill']:
        """
        Load a skill from a directory.

        :param directory: the skill
        :param agent_context: the agent's context
        :return: the Skill object. None if the parsing failed.
        """
        # check if there is the config file. If not, then return None.
        skill_loader = ConfigLoader("skill-config_schema.json", SkillConfig)
        skill_config = skill_loader.load(open(os.path.join(directory, DEFAULT_SKILL_CONFIG_FILE)))
        if skill_config is None:
            return None

        skills_spec = importlib.util.spec_from_file_location(skill_config.name, os.path.join(directory, "__init__.py"))
        if skills_spec is None:
            logger.warning("No skill found.")
            return None

        skill_module = importlib.util.module_from_spec(skills_spec)
        sys.modules[skill_config.name + "_skill"] = skill_module
        skills_packages = list(filter(lambda x: not x.startswith("__"), skills_spec.loader.contents()))  # type: ignore
        logger.debug("Processing the following skill package: {}".format(skills_packages))

        skill_context = SkillContext(agent_context)

        handler_configurations = list(dict(skill_config.handlers.read_all()).values())
        handlers = Handler.parse_module(os.path.join(directory, "handlers.py"), handler_configurations, skill_context)
        behaviours_configurations = list(dict(skill_config.behaviours.read_all()).values())
        behaviours = Behaviour.parse_module(os.path.join(directory, "behaviours.py"), behaviours_configurations, skill_context)
        tasks_configurations = list(dict(skill_config.tasks.read_all()).values())
        tasks = Task.parse_module(os.path.join(directory, "tasks.py"), tasks_configurations, skill_context)
        shared_classes_configurations = list(dict(skill_config.shared_classes.read_all()).values())
        shared_classes_instances = SharedClass.parse_module(directory, shared_classes_configurations, skill_context)

        skill = Skill(skill_config, skill_context, handlers, behaviours, tasks, shared_classes_instances)
        skill_context._skill = skill

        return skill
