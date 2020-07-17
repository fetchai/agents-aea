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

import datetime
import inspect
import logging
import queue
import re
from abc import ABC, abstractmethod
from logging import Logger, LoggerAdapter
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, Optional, Sequence, Set, Tuple, Type, Union, cast

from aea.components.base import Component
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentType,
    ProtocolId,
    PublicId,
    SkillComponentConfiguration,
    SkillConfig,
)
from aea.connections.base import ConnectionStatus
from aea.context.base import AgentContext
from aea.contracts.base import Contract
from aea.exceptions import AEAException
from aea.helpers.base import load_aea_package, load_module
from aea.helpers.logging import AgentLoggerAdapter
from aea.mail.base import Address
from aea.multiplexer import OutBox
from aea.protocols.base import Message
from aea.skills.tasks import TaskManager

logger = logging.getLogger(__name__)


class SkillContext:
    """This class implements the context of a skill."""

    def __init__(
        self,
        agent_context: Optional[AgentContext] = None,
        skill: Optional["Skill"] = None,
    ):
        """
        Initialize a skill context.

        :agent_context: the agent context.
        :skill: the skill.
        """
        self._agent_context = agent_context  # type: Optional[AgentContext]
        self._in_queue = Queue()  # type: Queue
        self._skill = skill  # type: Optional[Skill]

        self._is_active = True  # type: bool
        self._new_behaviours_queue = queue.Queue()  # type: Queue
        self._logger: Optional[Union[Logger, LoggerAdapter]] = None

    @property
    def logger(self) -> Union[Logger, LoggerAdapter]:
        """Get the logger."""
        if self._logger is None:
            return logging.getLogger("aea")
        return self._logger

    @logger.setter
    def logger(self, logger_: Union[Logger, AgentLoggerAdapter]) -> None:
        assert self._logger is None, "Logger already set."
        self._logger = logger_

    def _get_agent_context(self) -> AgentContext:
        """Get the agent context."""
        assert self._agent_context is not None, "Agent context not set yet."
        return self._agent_context

    def set_agent_context(self, agent_context: AgentContext) -> None:
        """Set the agent context."""
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
    def skill_id(self) -> PublicId:
        """Get the skill id of the skill context."""
        assert self._skill is not None, "Skill not set yet."
        return self._skill.configuration.public_id

    @property
    def is_active(self) -> bool:
        """Get the status of the skill (active/not active)."""
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
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
        Queue for the new behaviours.

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
    def decision_maker_handler_context(self) -> SimpleNamespace:
        """Get decision maker handler context."""
        return cast(
            SimpleNamespace, self._get_agent_context().decision_maker_handler_context
        )

    @property
    def task_manager(self) -> TaskManager:
        """Get behaviours of the skill."""
        assert self._skill is not None, "Skill not initialized."
        return self._get_agent_context().task_manager

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
    def contracts(self) -> SimpleNamespace:
        """Get contracts the skill has access to."""
        assert self._skill is not None, "Skill not initialized."
        return SimpleNamespace(**self._skill.contracts)

    @property
    def namespace(self) -> SimpleNamespace:
        """Get the agent context namespace."""
        return self._get_agent_context().namespace

    def __getattr__(self, item) -> Any:
        """Get attribute."""
        return super().__getattribute__(item)  # pragma: no cover


class SkillComponent(ABC):
    """This class defines an abstract interface for skill component classes."""

    def __init__(
        self,
        name: str,
        skill_context: SkillContext,
        configuration: Optional[SkillComponentConfiguration] = None,
        **kwargs,
    ):
        """
        Initialize a skill component.

        :param name: the name of the component.
        :param configuration: the configuration for the component.
        :param skill_context: the skill context.
        """
        assert name is not None, "SkillComponent name is not provided."
        assert skill_context is not None, "SkillConext is not provided"
        if configuration is None:
            class_name = type(self).__name__
            configuration = SkillComponentConfiguration(class_name=class_name, **kwargs)
        self._configuration = configuration
        self._name = name
        self._context = skill_context
        if len(kwargs) != 0:
            logger.warning(
                "The kwargs={} passed to {} have not been set!".format(kwargs, name)
            )

    @property
    def name(self) -> str:
        """Get the name of the skill component."""
        return self._name

    @property
    def context(self) -> SkillContext:
        """Get the context of the skill component."""
        assert self._context is not None, "Skill context not set yet."
        return self._context

    @property
    def skill_id(self) -> PublicId:
        """Get the skill id of the skill component."""
        return self.context.skill_id

    @property
    def configuration(self) -> SkillComponentConfiguration:
        """Get the skill component configuration."""
        assert self._configuration is not None, "Configuration not set."
        return self._configuration

    # TODO consider rename this property
    @property
    def config(self) -> Dict[Any, Any]:
        """Get the config of the skill component."""
        return self.configuration.args

    @abstractmethod
    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Implement the teardown.

        :return: None
        """

    @classmethod
    @abstractmethod
    def parse_module(
        cls,
        path: str,
        configs: Dict[str, SkillComponentConfiguration],
        skill_context: SkillContext,
    ):
        """Parse the component module."""


class AbstractBehaviour(SkillComponent, ABC):
    """
    Abstract behaviour for periodical calls.

    tick_interval: float, interval to call behaviour's act.
    start_at: optional datetime, when to start periodical calls.
    """

    _tick_interval: float = 0.001
    _start_at: Optional[datetime.datetime] = None

    @property
    def tick_interval(self) -> float:
        """Get the tick_interval in seconds."""
        return self._tick_interval

    @property
    def start_at(self) -> Optional[datetime.datetime]:
        """Get the start time of the behaviour."""
        return self._start_at


class Behaviour(AbstractBehaviour, ABC):
    """This class implements an abstract behaviour."""

    @abstractmethod
    def act(self) -> None:
        """
        Implement the behaviour.

        :return: None
        """

    def is_done(self) -> bool:  # pylint: disable=no-self-use
        """Return True if the behaviour is terminated, False otherwise."""
        return False

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
        self.act()

    @classmethod
    def parse_module(
        cls,
        path: str,
        behaviour_configs: Dict[str, SkillComponentConfiguration],
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
        behaviour_names = set(
            config.class_name for _, config in behaviour_configs.items()
        )
        behaviour_module = load_module("behaviours", Path(path))
        classes = inspect.getmembers(behaviour_module, inspect.isclass)
        behaviours_classes = list(
            filter(
                lambda x: any(
                    re.match(behaviour, x[0]) for behaviour in behaviour_names
                )
                and not str.startswith(x[1].__module__, "aea.")
                and not str.startswith(
                    x[1].__module__,
                    f"packages.{skill_context.skill_id.author}.skills.{skill_context.skill_id.name}",
                ),
                classes,
            )
        )

        name_to_class = dict(behaviours_classes)
        _print_warning_message_for_non_declared_skill_components(
            set(name_to_class.keys()),
            {
                behaviour_config.class_name
                for behaviour_config in behaviour_configs.values()
            },
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
                behaviour = behaviour_class(
                    name=behaviour_id,
                    configuration=behaviour_config,
                    skill_context=skill_context,
                    **dict(behaviour_config.args),
                )
                behaviours[behaviour_id] = behaviour

        return behaviours


class Handler(SkillComponent, ABC):
    """This class implements an abstract behaviour."""

    SUPPORTED_PROTOCOL = None  # type: Optional[ProtocolId]

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
        handler_configs: Dict[str, SkillComponentConfiguration],
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
        handler_names = set(config.class_name for _, config in handler_configs.items())
        handler_module = load_module("handlers", Path(path))
        classes = inspect.getmembers(handler_module, inspect.isclass)
        handler_classes = list(
            filter(
                lambda x: any(re.match(handler, x[0]) for handler in handler_names)
                and not str.startswith(x[1].__module__, "aea.")
                and not str.startswith(
                    x[1].__module__,
                    f"packages.{skill_context.skill_id.author}.skills.{skill_context.skill_id.name}",
                ),
                classes,
            )
        )

        name_to_class = dict(handler_classes)
        _print_warning_message_for_non_declared_skill_components(
            set(name_to_class.keys()),
            {handler_config.class_name for handler_config in handler_configs.values()},
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
                handler = handler_class(
                    name=handler_id,
                    configuration=handler_config,
                    skill_context=skill_context,
                    **dict(handler_config.args),
                )
                handlers[handler_id] = handler

        return handlers


class Model(SkillComponent, ABC):
    """This class implements an abstract model."""

    def setup(self) -> None:
        """Set the class up."""

    def teardown(self) -> None:
        """Tear the class down."""

    @classmethod
    def parse_module(
        cls,
        path: str,
        model_configs: Dict[str, SkillComponentConfiguration],
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
                    lambda x: any(re.match(model, x[0]) for model in model_names)
                    and issubclass(x[1], Model)
                    and not str.startswith(x[1].__module__, "aea.")
                    and not str.startswith(
                        x[1].__module__,
                        f"packages.{skill_context.skill_id.author}.skills.{skill_context.skill_id.name}",
                    ),
                    classes,
                )
            )
            models.extend(filtered_classes)

        _check_duplicate_classes(models)
        name_to_class = dict(models)
        _print_warning_message_for_non_declared_skill_components(
            set(name_to_class.keys()),
            {model_config.class_name for model_config in model_configs.values()},
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
                model_instance = model(
                    name=model_id,
                    skill_context=skill_context,
                    configuration=model_config,
                    **dict(model_config.args),
                )
                instances[model_id] = model_instance
                setattr(skill_context, model_id, model_instance)
        return instances


def _check_duplicate_classes(name_class_pairs: Sequence[Tuple[str, Type]]):
    """
    Given a sequence of pairs (class_name, class_obj), check
    whether there are duplicates in the class names.

    :param name_class_pairs: the sequence of pairs (class_name, class_obj)
    :return: None
    :raises AEAException: if there are more than one definition of the same class.
    """
    names_to_path: Dict[str, str] = {}
    for class_name, class_obj in name_class_pairs:
        module_path = class_obj.__module__
        if class_name in names_to_path:
            raise AEAException(
                f"Model '{class_name}' present both in {names_to_path[class_name]} and {module_path}. Remove one of them."
            )
        names_to_path[class_name] = module_path


class Skill(Component):
    """This class implements a skill."""

    def __init__(
        self,
        configuration: SkillConfig,
        skill_context: Optional[SkillContext] = None,
        handlers: Optional[Dict[str, Handler]] = None,
        behaviours: Optional[Dict[str, Behaviour]] = None,
        models: Optional[Dict[str, Model]] = None,
    ):
        """
        Initialize a skill.

        :param configuration: the skill configuration.
        :param skill_context: the skill context.
        :param handlers: dictionary of handlers.
        :param behaviours: dictionary of behaviours.
        :param models: dictionary of models.
        """
        super().__init__(configuration)
        self.config = configuration
        self._skill_context = (
            skill_context if skill_context is not None else SkillContext()
        )
        self._handlers = (
            {} if handlers is None else handlers
        )  # type: Dict[str, Handler]
        self._behaviours = (
            {} if behaviours is None else behaviours
        )  # type: Dict[str, Behaviour]
        self._models = {} if models is None else models  # type: Dict[str, Model]

        self._contracts = {}  # type: Dict[str, Contract]

        self._skill_context._skill = self

    @property
    def contracts(self) -> Dict[str, Contract]:
        """Get the contracts associated with the skill."""
        return self._contracts

    def inject_contracts(self, contracts: Dict[str, Contract]) -> None:
        """Add the contracts to the skill."""
        self._contracts = contracts

    @property
    def skill_context(self) -> SkillContext:
        """Get the skill context."""
        assert self._skill_context is not None, "Skill context not set."
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
        Load the skill from a directory.

        :param directory: the directory to the skill package.
        :param agent_context: the skill context
        :return: the skill object.
        """
        configuration = cast(
            SkillConfig,
            ComponentConfiguration.load(ComponentType.SKILL, Path(directory)),
        )
        configuration.directory = Path(directory)
        return Skill.from_config(configuration, agent_context)

    @property
    def logger(self) -> Union[Logger, LoggerAdapter]:
        """
        Get the logger.

        In the case of a skill, return the
        logger provided by the skill context.
        """
        return self.skill_context.logger

    @logger.setter
    def logger(self, *args) -> None:
        """Set the logger."""
        raise ValueError("Cannot set logger to a skill component..")

    @classmethod
    def from_config(
        cls, configuration: SkillConfig, agent_context: AgentContext
    ) -> "Skill":
        """
        Load the skill from configuration.

        :param configuration: a skill configuration. Must be associated with a directory.
        :param agent_context: the agent context.
        :return: the skill.
        """
        assert (
            configuration.directory is not None
        ), "Configuration must be associated with a directory."

        # we put the initialization here because some skill components
        # might need some info from the skill
        # (e.g. see https://github.com/fetchai/agents-aea/issues/1095)
        skill_context = SkillContext()
        skill_context.set_agent_context(agent_context)
        logger_name = f"aea.packages.{configuration.author}.skills.{configuration.name}"
        logger = AgentLoggerAdapter(
            logging.getLogger(logger_name), agent_context.agent_name
        )
        skill_context.logger = logger

        skill = Skill(configuration, skill_context)

        directory = configuration.directory
        load_aea_package(configuration)
        handlers_by_id = dict(configuration.handlers.read_all())
        handlers = Handler.parse_module(
            str(directory / "handlers.py"), handlers_by_id, skill_context
        )

        behaviours_by_id = dict(configuration.behaviours.read_all())
        behaviours = Behaviour.parse_module(
            str(directory / "behaviours.py"), behaviours_by_id, skill_context,
        )

        models_by_id = dict(configuration.models.read_all())
        model_instances = Model.parse_module(
            str(directory), models_by_id, skill_context
        )

        skill.handlers.update(handlers)
        skill.behaviours.update(behaviours)
        skill.models.update(model_instances)

        return skill


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
