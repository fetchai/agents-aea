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
import queue
import re
from abc import ABC, abstractmethod
from logging import Logger
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, Optional, cast

from aea.configurations.base import (
    BehaviourConfig,
    DEFAULT_SKILL_CONFIG_FILE,
    HandlerConfig,
    ModelConfig,
    ProtocolId,
    PublicId,
    SkillConfig,
)
from aea.configurations.loader import ConfigLoader
from aea.connections.base import ConnectionStatus
from aea.context.base import AgentContext
from aea.contracts.base import Contract
from aea.crypto.ledger_apis import LedgerApis
from aea.decision_maker.base import GoalPursuitReadiness, OwnershipState, Preferences
from aea.helpers.base import (
    add_agent_component_module_to_sys_modules,
    load_agent_component_package,
    load_module,
)
from aea.mail.base import OutBox
from aea.protocols.base import Message
from aea.skills.tasks import TaskManager

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

        self._is_active = True  # type: bool
        self._new_behaviours_queue = queue.Queue()  # type: Queue
        self._logger = None  # type: Optional[Logger]

    @property
    def shared_state(self) -> Dict[str, Any]:
        """Get the shared state dictionary."""
        return self._agent_context.shared_state

    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self._agent_context.agent_name

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
    def task_manager(self) -> TaskManager:
        """Get behaviours of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return self._agent_context.task_manager

    @property
    def ledger_apis(self) -> LedgerApis:
        """Get ledger APIs."""
        return self._agent_context.ledger_apis

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
    def contracts(self) -> SimpleNamespace:
        """Get contracts the skill has access to."""
        assert self._skill is not None, "Skill not initialized."
        return SimpleNamespace(**self._skill.contracts)

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
        behaviours_configs: Dict[str, BehaviourConfig],
        skill_context: SkillContext,
    ) -> Dict[str, "Behaviour"]:
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
        behaviours_classes = list(
            filter(lambda x: re.match("\\w+Behaviour", x[0]), classes)
        )

        name_to_class = dict(behaviours_classes)
        for behaviour_id, behaviour_config in behaviours_configs.items():
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

    def __init__(self, *args, **kwargs):
        """
        Initialize a model.

        :param skill_context: the skill context
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
        instances = {}
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
                    and Model in inspect.getmro(x[1]),
                    classes,
                )
            )
            models.extend(filtered_classes)

        name_to_class = dict(models)
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


class Skill:
    """This class implements a skill."""

    def __init__(
        self,
        config: SkillConfig,
        skill_context: SkillContext,
        handlers: Optional[Dict[str, Handler]],
        behaviours: Optional[Dict[str, Behaviour]],
        models: Optional[Dict[str, Model]],
    ):
        """
        Initialize a skill.

        :param config: the skill configuration.
        :param handlers: the list of handlers to handle incoming envelopes.
        :param behaviours: the list of behaviours that defines the proactive component of the agent.
        :param models: the list of models shared across tasks, behaviours and
        """
        self.config = config
        self.skill_context = skill_context
        self.handlers = handlers if handlers is not None else {}
        self.behaviours = behaviours if behaviours is not None else {}
        self.models = models if models is not None else {}
        self.contracts = {}  # type: Dict[str, Contract]

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
        if len(handlers_by_id) > 0:
            handlers = Handler.parse_module(
                os.path.join(directory, "handlers.py"), handlers_by_id, skill_context
            )
        else:
            handlers = {}  # pragma: no cover

        behaviours_by_id = dict(skill_config.behaviours.read_all())
        if len(behaviours_by_id) > 0:
            behaviours = Behaviour.parse_module(
                os.path.join(directory, "behaviours.py"),
                behaviours_by_id,
                skill_context,
            )
        else:
            behaviours = {}

        models_by_id = dict(skill_config.models.read_all())
        if len(models_by_id) > 0:
            model_instances = Model.parse_module(directory, models_by_id, skill_context)
        else:
            model_instances = {}

        skill = Skill(
            skill_config, skill_context, handlers, behaviours, model_instances
        )
        skill_context._skill = skill

        return skill
