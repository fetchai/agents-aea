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

import inspect
import logging
import os
import queue
import re
from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, Optional, Set, cast

from aea.configurations.base import (
    BehaviourConfig,
    DEFAULT_SKILL_CONFIG_FILE,
    HandlerConfig,
    ModelConfig,
    ProtocolId,
    PublicId,
    SkillConfig,
)
from aea.configurations.components import Component
from aea.configurations.loader import ConfigLoader
from aea.connections.base import ConnectionStatus
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import LedgerApis
from aea.decision_maker.base import GoalPursuitReadiness, OwnershipState, Preferences
from aea.helpers.base import (
    add_agent_component_module_to_sys_modules,
    load_agent_component_package,
    load_module,
)
from aea.mail.base import Address, OutBox
from aea.protocols.base import Message
from aea.skills.tasks import TaskManager

logger = logging.getLogger(__name__)


class SkillContext:
    """This class implements the context of a skill."""

    def __init__(self):
        """
        Initialize a skill context.
        """
        self._agent_context = None  # type: Optional[AgentContext]
        self._in_queue = Queue()  # type: Queue
        self._skill = None  # type: Optional[Skill]

        self._is_active = True  # type: bool
        self._new_behaviours_queue = queue.Queue()  # type: Queue
        self._logger = None  # type: Optional[Logger]

    @property
    def logger(self) -> Logger:
        """Get the logger."""
        assert self._logger is not None, "Logger not set yet."
        return self._logger

    @logger.setter
    def logger(self, logger_: Logger) -> None:
        assert self._logger is None, "Logger already set."
        self._logger = logger_

    def _get_agent_context(self) -> AgentContext:
        """Get the agent context."""
        assert self._agent_context is not None, "Agent context not set yet."
        return self._agent_context

    def set_agent_context(self, agent_context: AgentContext) -> None:
        """Set the agent context."""
        assert self._agent_context is None, "Agent context already set."
        self._agent_context = agent_context

    @property
    def shared_state(self) -> Dict[str, Any]:
        """Get the shared state dictionary."""
        return self._get_agent_context().shared_state

    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self._get_agent_context().agent_name

    @property
    def skill_id(self):
        """Get the skill id of the skill context."""
        return self._skill.config.public_id

    @property
    def is_active(self):
        """Get the status of the skill (active/not active)."""
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        """Set the status of the skill (active/not active)."""
        self._is_active = value
        logger.debug(
            "New status of skill {}: is_active={}".format(
                self.skill_id, self._is_active
            )
        )

    @property
    def new_behaviours(self) -> Queue:
        """
        The queue for the new behaviours.

        This queue can be used to send messages to the framework
        to request the registration of a behaviour.

        :return the queue of new behaviours.
        """
        return self._new_behaviours_queue

    @property
    def agent_addresses(self) -> Dict[str, str]:
        """Get addresses."""
        return self._get_agent_context().addresses

    @property
    def agent_address(self) -> str:
        """Get address."""
        return self._get_agent_context().address

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get connection status."""
        return self._get_agent_context().connection_status

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._get_agent_context().outbox

    @property
    def message_in_queue(self) -> Queue:
        """Get message in queue."""
        return self._in_queue

    @property
    def decision_maker_message_queue(self) -> Queue:
        """Get message queue of decision maker."""
        return self._get_agent_context().decision_maker_message_queue

    @property
    def agent_ownership_state(self) -> OwnershipState:
        """Get ownership state."""
        return self._get_agent_context().ownership_state

    @property
    def agent_preferences(self) -> Preferences:
        """Get preferences."""
        return self._get_agent_context().preferences

    @property
    def agent_goal_pursuit_readiness(self) -> GoalPursuitReadiness:
        """Get the goal pursuit readiness."""
        return self._get_agent_context().goal_pursuit_readiness

    @property
    def task_manager(self) -> TaskManager:
        """Get behaviours of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return self._get_agent_context().task_manager

    @property
    def ledger_apis(self) -> LedgerApis:
        """Get ledger APIs."""
        return self._get_agent_context().ledger_apis

    @property
    def search_service_address(self) -> Address:
        """Get the address of the search service."""
        return self._get_agent_context().search_service_address

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
    def logger(self) -> Logger:
        """Get the logger."""
        assert self._logger is not None, "Logger not set."
        return self._logger

    def __getattr__(self, item) -> Any:
        """Get attribute."""
        return super().__getattribute__(item)  # pragma: no cover


class SkillComponent(ABC):
    """This class defines an abstract interface for skill component classes."""

    def __init__(self, **kwargs):
        """
        Initialize a behaviour.

        :param skill_context: the skill context
        :param kwargs: keyword arguments
        """
        try:
            self._context = kwargs.pop("skill_context")  # type: SkillContext
            assert self._context is not None
        except Exception:
            raise ValueError("Skill context not provided.")

        try:
            self._name = kwargs.pop("name")
            assert self._name is not None
        except Exception:
            raise ValueError("Missing name of skill component.")

        self._config = kwargs

    @property
    def name(self) -> str:
        """Get the name of the skill component."""
        return self._name

    @property
    def context(self) -> SkillContext:
        """Get the context of the behaviour."""
        return self._context

    @property
    def skill_id(self) -> PublicId:
        """Get the skill id of the skill component."""
        return self.context.skill_id

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
    def teardown(self) -> None:
        """
        Implement the behaviour teardown.

        :return: None
        """

    @classmethod
    @abstractmethod
    def parse_module(
        cls, path: str, configs: Dict[str, Any], skill_context: SkillContext
    ):
        """Parse the component module."""


class Behaviour(SkillComponent):
    """This class implements an abstract behaviour."""

    def __init__(self, **kwargs):
        """Initialize a behaviour."""
        super().__init__(**kwargs)

    @abstractmethod
    def act(self) -> None:
        """
        Implement the behaviour.

        :return: None
        """

    def is_done(self) -> bool:
        """Return True if the behaviour is terminated, False otherwise."""
        return False

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
        self.act()

    @classmethod
    def parse_module(
        cls,
        path: str,
        behaviour_configs: Dict[str, BehaviourConfig],
        skill_context: SkillContext,
    ) -> Dict[str, "Behaviour"]:
        """
        Parse the behaviours module.

        :param path: path to the Python module containing the Behaviour classes.
        :param behaviour_configs: a list of behaviour configurations.
        :param skill_context: the skill context
        :return: a list of Behaviour.
        """
        behaviours = {}  # type: Dict[str, "Behaviour"]
        if behaviour_configs == {}:
            return behaviours
        behaviour_module = load_module("behaviours", Path(path))
        classes = inspect.getmembers(behaviour_module, inspect.isclass)
        behaviours_classes = list(
            filter(
                lambda x: re.match("\\w+Behaviour", x[0])
                and not str.startswith(x[1].__module__, "aea."),
                classes,
            )
        )

        name_to_class = dict(behaviours_classes)
        _print_warning_message_for_non_declared_skill_components(
            set(name_to_class.keys()),
            set(
                [
                    behaviour_config.class_name
                    for behaviour_config in behaviour_configs.values()
                ]
            ),
            "behaviours",
            path,
        )

        for behaviour_id, behaviour_config in behaviour_configs.items():
            behaviour_class_name = cast(str, behaviour_config.class_name)
            logger.debug("Processing behaviour {}".format(behaviour_class_name))
            assert (
                behaviour_id.isidentifier()
            ), "'{}' is not a valid identifier.".format(behaviour_id)
            behaviour_class = name_to_class.get(behaviour_class_name, None)
            if behaviour_class is None:
                logger.warning(
                    "Behaviour '{}' cannot be found.".format(behaviour_class_name)
                )
            else:
                args = behaviour_config.args
                assert (
                    "skill_context" not in args.keys()
                ), "'skill_context' is a reserved key. Please rename your arguments!"
                args["skill_context"] = skill_context
                args["name"] = behaviour_id
                behaviour = behaviour_class(**args)
                behaviours[behaviour_id] = behaviour

        return behaviours


class Handler(SkillComponent):
    """This class implements an abstract behaviour."""

    SUPPORTED_PROTOCOL = None  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize a handler object."""
        super().__init__(**kwargs)

    @abstractmethod
    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """

    @classmethod
    def parse_module(
        cls,
        path: str,
        handler_configs: Dict[str, HandlerConfig],
        skill_context: SkillContext,
    ) -> Dict[str, "Handler"]:
        """
        Parse the handler module.

        :param path: path to the Python module containing the Handler class.
        :param handler_configs: the list of handler configurations.
        :param skill_context: the skill context
        :return: an handler, or None if the parsing fails.
        """
        handlers = {}  # type: Dict[str, "Handler"]
        if handler_configs == {}:
            return handlers
        handler_module = load_module("handlers", Path(path))
        classes = inspect.getmembers(handler_module, inspect.isclass)
        handler_classes = list(
            filter(
                lambda x: re.match("\\w+Handler", x[0])
                and not str.startswith(x[1].__module__, "aea."),
                classes,
            )
        )

        name_to_class = dict(handler_classes)
        _print_warning_message_for_non_declared_skill_components(
            set(name_to_class.keys()),
            set(
                [
                    handler_config.class_name
                    for handler_config in handler_configs.values()
                ]
            ),
            "handlers",
            path,
        )
        for handler_id, handler_config in handler_configs.items():
            handler_class_name = cast(str, handler_config.class_name)
            logger.debug("Processing handler {}".format(handler_class_name))
            assert handler_id.isidentifier(), "'{}' is not a valid identifier.".format(
                handler_id
            )
            handler_class = name_to_class.get(handler_class_name, None)
            if handler_class is None:
                logger.warning(
                    "Handler '{}' cannot be found.".format(handler_class_name)
                )
            else:
                args = handler_config.args
                assert (
                    "skill_context" not in args.keys()
                ), "'skill_context' is a reserved key. Please rename your arguments!"
                args["skill_context"] = skill_context
                args["name"] = handler_id
                handler = handler_class(**args)
                handlers[handler_id] = handler

        return handlers


class Model(SkillComponent):
    """This class implements an abstract model."""

    def __init__(self, **kwargs):
        """
        Initialize a model.

        :param kwargs: keyword arguments.
        """
        super().__init__(**kwargs)

    def setup(self) -> None:
        """Set the class up."""

    def teardown(self) -> None:
        """Tear the class down."""

    @classmethod
    def parse_module(
        cls,
        path: str,
        model_configs: Dict[str, ModelConfig],
        skill_context: SkillContext,
    ) -> Dict[str, "Model"]:
        """
        Parse the tasks module.

        :param path: path to the Python skill module.
        :param model_configs: a list of model configurations.
        :param skill_context: the skill context
        :return: a list of Model.
        """
        instances = {}  # type: Dict[str, "Model"]
        if model_configs == {}:
            return instances
        models = []

        model_names = set(config.class_name for _, config in model_configs.items())

        # get all Python modules except the standard ones
        ignore_regex = "|".join(["handlers.py", "behaviours.py", "tasks.py", "__.*"])
        all_python_modules = Path(path).glob("*.py")
        module_paths = set(
            map(
                str,
                filter(
                    lambda x: not re.match(ignore_regex, x.name), all_python_modules
                ),
            )
        )

        for module_path in module_paths:
            logger.debug("Trying to load module {}".format(module_path))
            module_name = module_path.replace(".py", "")
            model_module = load_module(module_name, Path(module_path))
            classes = inspect.getmembers(model_module, inspect.isclass)
            filtered_classes = list(
                filter(
                    lambda x: any(re.match(shared, x[0]) for shared in model_names)
                    and Model in inspect.getmro(x[1])
                    and not str.startswith(x[1].__module__, "aea."),
                    classes,
                )
            )
            models.extend(filtered_classes)

        name_to_class = dict(models)
        _print_warning_message_for_non_declared_skill_components(
            set(name_to_class.keys()),
            set([model_config.class_name for model_config in model_configs.values()]),
            "models",
            path,
        )
        for model_id, model_config in model_configs.items():
            model_class_name = model_config.class_name
            logger.debug(
                "Processing model id={}, class={}".format(model_id, model_class_name)
            )
            assert model_id.isidentifier(), "'{}' is not a valid identifier.".format(
                model_id
            )
            model = name_to_class.get(model_class_name, None)
            if model is None:
                logger.warning("Model '{}' cannot be found.".format(model_class_name))
            else:
                args = model_config.args
                assert (
                    "skill_context" not in args.keys()
                ), "'skill_context' is a reserved key. Please rename your arguments!"
                args["skill_context"] = skill_context
                args["name"] = model_id
                model_instance = model(**args)
                instances[model_id] = model_instance
                setattr(skill_context, model_id, model_instance)
        return instances


class Skill(Component):
    """This class implements a skill."""

    def __init__(
        self,
        configuration: SkillConfig,
    ):
        """
        Initialize a skill.

        :param configuration: the skill configuration.
        """
        super().__init__(configuration)
        self.config = configuration
        self._skill_context = None  # type: Optional[SkillContext]
        self._handlers = {}  # type: Optional[Dict[str, Handler]]
        self._behaviours = {}    # type: Optional[Dict[str, Handler]]
        self._models = {}   # type: Optional[Dict[str, Handler]]

    @property
    def skill_context(self) -> SkillContext:
        """Get the skill context."""
        return self._skill_context

    @property
    def handlers(self) -> Dict[str, Handler]:
        """Get the handlers."""
        return self._handlers

    @property
    def behaviours(self) -> Dict[str, Behaviour]:
        """Get the handlers."""
        return self._behaviours

    @property
    def models(self) -> Dict[str, Model]:
        """Get the handlers."""
        return self._models

    @classmethod
    def from_dir(cls, directory: str, agent_context: AgentContext) -> "Skill":
        """
        Load a skill from a directory.

        :param directory: the skill directory.
        :param agent_context: the agent's context
        :return: the Skill object.
        :raises Exception: if the parsing failed.
        """
        # check if there is the config file. If not, then return None.
        skill_loader = ConfigLoader("skill-config_schema.json", SkillConfig)
        skill_config = skill_loader.load(
            open(os.path.join(directory, DEFAULT_SKILL_CONFIG_FILE))
        )
        skill_module = load_agent_component_package(
            "skill", skill_config.name, skill_config.author, Path(directory)
        )
        add_agent_component_module_to_sys_modules(
            "skill", skill_config.name, skill_config.author, skill_module
        )
        loader_contents = [path.name for path in Path(directory).iterdir()]
        skills_packages = list(filter(lambda x: not x.startswith("__"), loader_contents))  # type: ignore
        logger.debug(
            "Processing the following skill package: {}".format(skills_packages)
        )

        skill_context = SkillContext(agent_context)
        # set the logger of the skill context.
        logger_name = "aea.{}.skills.{}.{}".format(
            agent_context.agent_name, skill_config.author, skill_config.name
        )
        skill_context._logger = logging.getLogger(logger_name)

        handlers_by_id = dict(skill_config.handlers.read_all())
        handlers = Handler.parse_module(
            os.path.join(directory, "handlers.py"), handlers_by_id, skill_context
        )

        behaviours_by_id = dict(skill_config.behaviours.read_all())
        behaviours = Behaviour.parse_module(
            os.path.join(directory, "behaviours.py"), behaviours_by_id, skill_context,
        )

        models_by_id = dict(skill_config.models.read_all())
        model_instances = Model.parse_module(directory, models_by_id, skill_context)

        skill = Skill(skill_config)
        skill.handlers.update(handlers)
        skill.behaviours.update(behaviours)
        skill.models.update(model_instances)
        skill_context._skill = skill

        return skill

    def load(self, *args, **kwargs):
        """
        Set the component up.

        In the case of a skill, we load the 'serialization.py' module
        to instantiate an instance of the Serializer.
        """
        skill_context = SkillContext()
        skill_context._logger = logging.getLogger()
        skill_configuration = cast(SkillConfig, self.configuration)
        handlers_by_id = dict(skill_configuration.handlers.read_all())
        handlers = Handler.parse_module(
            str(self.directory / "handlers.py"), handlers_by_id, skill_context
        )

        behaviours_by_id = dict(skill_configuration.behaviours.read_all())
        behaviours = Behaviour.parse_module(
            str(self.directory / "behaviours.py"), behaviours_by_id, skill_context,
        )

        models_by_id = dict(skill_configuration.models.read_all())
        model_instances = Model.parse_module(
            str(self.directory), models_by_id, skill_context
        )

        # update skill attributes
        self._handlers = handlers
        self._behaviours = behaviours
        self._models = model_instances
        self._skill_context = skill_context
        skill_context._skill = self


def _print_warning_message_for_non_declared_skill_components(
    classes: Set[str], config_components: Set[str], item_type, skill_path
):
    """Print a warning message if a skill component is not declared in the config files."""
    for class_name in classes.difference(config_components):
        logger.warning(
            "Class {} of type {} found but not declared in the configuration file {}.".format(
                class_name, item_type, skill_path
            )
        )
