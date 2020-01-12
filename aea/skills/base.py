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
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Optional, Dict, Any, cast

from aea.configurations.base import BehaviourConfig, HandlerConfig, TaskConfig, SharedClassConfig, SkillConfig, \
    ProtocolId, DEFAULT_SKILL_CONFIG_FILE
from aea.configurations.loader import ConfigLoader
from aea.connections.base import ConnectionStatus
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import LedgerApis
from aea.decision_maker.base import OwnershipState, Preferences, GoalPursuitReadiness
from aea.helpers.base import load_module, add_agent_component_module_to_sys_modules, load_agent_component_package
from aea.mail.base import OutBox
from aea.protocols.base import Message

logger = logging.getLogger(__name__)


class SkillContext:
    """This class implements the context of a skill."""

    def __init__(self, agent_context: AgentContext):
        """
        Initialize a skill context.

        :param agent_context: the agent's context
        """
        self._agent_context = agent_context
        self._in_queue = Queue()  # type: Queue
        self._skill = None  # type: Optional[Skill]

    @property
    def shared_state(self) -> Dict[str, Any]:
        """Get the shared state dictionary."""
        return self._agent_context.shared_state

    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self._agent_context.agent_name

    @property
    def agent_public_key(self) -> str:
        """Get public key."""
        return self._agent_context.public_key

    @property
    def agent_public_keys(self) -> Dict[str, str]:
        """Get public keys."""
        return self._agent_context.public_keys

    @property
    def agent_addresses(self) -> Dict[str, str]:
        """Get addresses."""
        return self._agent_context.addresses

    @property
    def agent_address(self) -> str:
        """Get address."""
        return self._agent_context.address

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get connection status."""
        return self._agent_context.connection_status

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._agent_context.outbox

    @property
    def message_in_queue(self) -> Queue:
        """Get message in queue."""
        return self._in_queue

    @property
    def decision_maker_message_queue(self) -> Queue:
        """Get message queue of decision maker."""
        return self._agent_context.decision_maker_message_queue

    @property
    def agent_ownership_state(self) -> OwnershipState:
        """Get ownership state."""
        return self._agent_context.ownership_state

    @property
    def agent_preferences(self) -> Preferences:
        """Get preferences."""
        return self._agent_context.preferences

    @property
    def agent_goal_pursuit_readiness(self) -> GoalPursuitReadiness:
        """Get the goal pursuit readiness."""
        return self._agent_context.goal_pursuit_readiness

    @property
    def ledger_apis(self) -> LedgerApis:
        """Get ledger APIs."""
        return self._agent_context.ledger_apis

    @property
    def task_queue(self) -> Queue:
        """Get the task queue."""
        # TODO this is potentially dangerous - it exposes the task queue to other skills
        #      such that other skills can modify it.
        return self._agent_context.task_queue

    @property
    def handlers(self) -> SimpleNamespace:
        """Get handlers of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return SimpleNamespace(**self._skill.handlers)

    @property
    def behaviours(self) -> SimpleNamespace:
        """Get behaviours of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return SimpleNamespace(**self._skill.behaviours)

    @property
    def tasks(self) -> SimpleNamespace:
        """Get tasks of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return SimpleNamespace(**self._skill.tasks)

    def __getattr__(self, item) -> Any:
        """Get attribute."""
        return super().__getattribute__(item)  # pragma: no cover


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
    def setup(self) -> None:
        """
        Implement the behaviour setup.

        :return: None
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

    def done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return False

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
        self.act()

    @classmethod
    def parse_module(cls, path: str, behaviours_configs: Dict[str, BehaviourConfig], skill_context: SkillContext) -> Dict[str, 'Behaviour']:
        """
        Parse the behaviours module.

        :param path: path to the Python module containing the Behaviour classes.
        :param behaviours_configs: a list of behaviour configurations.
        :param skill_context: the skill context
        :return: a list of Behaviour.
        """
        behaviours = {}
        behaviour_module = load_module("behaviours", Path(path))
        classes = inspect.getmembers(behaviour_module, inspect.isclass)
        behaviours_classes = list(filter(lambda x: re.match("\\w+Behaviour", x[0]), classes))

        name_to_class = dict(behaviours_classes)
        for behaviour_id, behaviour_config in behaviours_configs.items():
            behaviour_class_name = cast(str, behaviour_config.class_name)
            logger.debug("Processing behaviour {}".format(behaviour_class_name))
            assert behaviour_id.isidentifier(), "'{}' is not a valid identifier.".format(behaviour_id)
            behaviour_class = name_to_class.get(behaviour_class_name, None)
            if behaviour_class is None:
                logger.warning("Behaviour '{}' cannot be found.".format(behaviour_class_name))
            else:
                args = behaviour_config.args
                assert 'skill_context' not in args.keys(), "'skill_context' is a reserved key. Please rename your arguments!"
                args['skill_context'] = skill_context
                behaviour = behaviour_class(**args)
                behaviours[behaviour_id] = behaviour

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
    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """

    @abstractmethod
    def setup(self) -> None:
        """
        Implement the behaviour setup.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """

    @classmethod
    def parse_module(cls, path: str, handler_configs: Dict[str, HandlerConfig], skill_context: SkillContext) -> Dict[str, 'Handler']:
        """
        Parse the handler module.

        :param path: path to the Python module containing the Handler class.
        :param handler_configs: the list of handler configurations.
        :param skill_context: the skill context
        :return: an handler, or None if the parsing fails.
        """
        handlers = {}
        handler_spec = importlib.util.spec_from_file_location("handlers", location=path)
        handler_module = importlib.util.module_from_spec(handler_spec)
        handler_spec.loader.exec_module(handler_module)  # type: ignore
        classes = inspect.getmembers(handler_module, inspect.isclass)
        handler_classes = list(filter(lambda x: re.match("\\w+Handler", x[0]), classes))

        name_to_class = dict(handler_classes)
        for handler_id, handler_config in handler_configs.items():
            handler_class_name = cast(str, handler_config.class_name)
            logger.debug("Processing handler {}".format(handler_class_name))
            assert handler_id.isidentifier(), "'{}' is not a valid identifier.".format(handler_id)
            handler_class = name_to_class.get(handler_class_name, None)
            if handler_class is None:
                logger.warning("Handler '{}' cannot be found.".format(handler_class_name))
            else:
                args = handler_config.args
                assert 'skill_context' not in args.keys(), "'skill_context' is a reserved key. Please rename your arguments!"
                args['skill_context'] = skill_context
                handler = handler_class(**args)
                handlers[handler_id] = handler

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
        self.completed = False

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
    def setup(self) -> None:
        """
        Implement the behaviour setup.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Teardown the task.

        :return: None
        """

    @classmethod
    def parse_module(cls, path: str, tasks_configs: Dict[str, TaskConfig], skill_context: SkillContext) -> Dict[str, 'Task']:
        """
        Parse the tasks module.

        :param path: path to the Python module containing the Task classes.
        :param tasks_configs: a list of tasks configurations.
        :param skill_context: the skill context
        :return: a list of Tasks.
        """
        tasks = {}
        task_module = load_module("tasks", Path(path))
        classes = inspect.getmembers(task_module, inspect.isclass)
        tasks_classes = list(filter(lambda x: re.match("\\w+Task", x[0]), classes))

        name_to_class = dict(tasks_classes)
        for task_id, task_config in tasks_configs.items():
            task_class_name = task_config.class_name
            logger.debug("Processing task {}".format(task_class_name))
            assert task_id.isidentifier(), "'{}' is not a valid identifier.".format(task_id)
            task_class = name_to_class.get(task_class_name, None)
            if task_class is None:
                logger.warning("Task '{}' cannot be found.".format(task_class_name))
            else:
                args = task_config.args
                assert 'skill_context' not in args.keys(), "'skill_context' is a reserved key. Please rename your arguments!"
                args['skill_context'] = skill_context
                task = task_class(**args)
                tasks[task_id] = task

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
    def parse_module(cls, path: str, shared_classes_configs: Dict[str, SharedClassConfig], skill_context: SkillContext) -> Dict[str, 'SharedClass']:
        """
        Parse the tasks module.

        :param path: path to the Python skill module.
        :param shared_classes_configs: a list of shared class configurations.
        :param skill_context: the skill context
        :return: a list of SharedClass.
        """
        instances = {}
        shared_classes = []

        shared_classes_names = set(config.class_name for _, config in shared_classes_configs.items())

        # get all Python modules except the standard ones
        ignore_regex = "|".join(["handlers.py", "behaviours.py", "tasks.py", "__.*"])
        all_python_modules = Path(path).glob("*.py")
        module_paths = set(map(str, filter(lambda x: not re.match(ignore_regex, x.name), all_python_modules)))

        for module_path in module_paths:
            logger.debug("Trying to load module {}".format(module_path))
            module_name = module_path.replace(".py", "")
            shared_class_module = load_module(module_name, Path(module_path))
            classes = inspect.getmembers(shared_class_module, inspect.isclass)
            filtered_classes = list(
                filter(
                    lambda x:
                        any(re.match(shared, x[0]) for shared in shared_classes_names) and SharedClass in inspect.getmro(x[1]),
                    classes)
            )
            shared_classes.extend(filtered_classes)

        name_to_class = dict(shared_classes)
        for shared_class_id, shared_class_config in shared_classes_configs.items():
            shared_class_name = shared_class_config.class_name
            logger.debug("Processing shared class id={}, class={}".format(shared_class_id, shared_class_name))
            assert shared_class_id.isidentifier(), "'{}' is not a valid identifier.".format(shared_class_id)
            shared_class = name_to_class.get(shared_class_name, None)
            if shared_class is None:
                logger.warning("Shared class '{}' cannot be found.".format(shared_class_name))
            else:
                args = shared_class_config.args
                assert 'skill_context' not in args.keys(), "'skill_context' is a reserved key. Please rename your arguments!"
                args['skill_context'] = skill_context
                shared_class_instance = shared_class(**args)
                instances[shared_class_id] = shared_class_instance
                setattr(skill_context, shared_class_id, shared_class_instance)
        return instances


class Skill:
    """This class implements a skill."""

    def __init__(self, config: SkillConfig,
                 skill_context: SkillContext,
                 handlers: Optional[Dict[str, Handler]],
                 behaviours: Optional[Dict[str, Behaviour]],
                 tasks: Optional[Dict[str, Task]],
                 shared_classes: Optional[Dict[str, SharedClass]]):
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
        self.handlers = handlers if handlers is not None else {}
        self.behaviours = behaviours if behaviours is not None else {}
        self.tasks = tasks if tasks is not None else {}
        self.shared_classes = shared_classes if shared_classes is not None else {}

    @classmethod
    def from_dir(cls, directory: str, agent_context: AgentContext) -> 'Skill':
        """
        Load a skill from a directory.

        :param directory: the skill directory.
        :param agent_context: the agent's context
        :return: the Skill object.
        :raises Exception: if the parsing failed.
        """
        # check if there is the config file. If not, then return None.
        skill_loader = ConfigLoader("skill-config_schema.json", SkillConfig)
        skill_config = skill_loader.load(open(os.path.join(directory, DEFAULT_SKILL_CONFIG_FILE)))
        skill_module = load_agent_component_package("skill", skill_config.name, skill_config.author, Path(directory))
        add_agent_component_module_to_sys_modules("skill", skill_config.name, skill_config.author, skill_module)
        loader_contents = [path.name for path in Path(directory).iterdir()]
        skills_packages = list(filter(lambda x: not x.startswith("__"), loader_contents))  # type: ignore
        logger.debug("Processing the following skill package: {}".format(skills_packages))

        skill_context = SkillContext(agent_context)

        handlers_by_id = dict(skill_config.handlers.read_all())
        if len(handlers_by_id) > 0:
            handlers = Handler.parse_module(os.path.join(directory, "handlers.py"), handlers_by_id, skill_context)
        else:
            handlers = {}

        behaviours_by_id = dict(skill_config.behaviours.read_all())
        if len(behaviours_by_id) > 0:
            behaviours = Behaviour.parse_module(os.path.join(directory, "behaviours.py"), behaviours_by_id, skill_context)
        else:
            behaviours = {}

        tasks_by_id = dict(skill_config.tasks.read_all())
        if len(tasks_by_id) > 0:
            tasks = Task.parse_module(os.path.join(directory, "tasks.py"), tasks_by_id, skill_context)
        else:
            tasks = {}

        shared_classes_by_id = dict(skill_config.shared_classes.read_all())
        if len(shared_classes_by_id) > 0:
            shared_classes_instances = SharedClass.parse_module(directory, shared_classes_by_id, skill_context)
        else:
            shared_classes_instances = {}

        skill = Skill(skill_config, skill_context, handlers, behaviours, tasks, shared_classes_instances)
        skill_context._skill = skill

        return skill
