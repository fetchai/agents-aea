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
from logging import Logger
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, Optional, Sequence, Set, Tuple, Type, cast

from aea.common import Address
from aea.components.base import Component, load_aea_package
from aea.configurations.base import (
    ComponentType,
    PublicId,
    SkillComponentConfiguration,
    SkillConfig,
)
from aea.configurations.loader import load_component_configuration
from aea.context.base import AgentContext
from aea.exceptions import (
    AEAActException,
    AEAComponentLoadException,
    AEAException,
    AEAHandleException,
    AEAInstantiationException,
    _StopRuntime,
    parse_exception,
)
from aea.helpers.base import _get_aea_logger_name_prefix, load_module
from aea.helpers.logging import AgentLoggerAdapter
from aea.helpers.storage.generic_storage import Storage
from aea.multiplexer import MultiplexerStatus, OutBox
from aea.protocols.base import Message
from aea.skills.tasks import TaskManager


_default_logger = logging.getLogger(__name__)


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
        self._new_handlers_queue = queue.Queue()  # type: Queue
        self._logger: Optional[Logger] = None

    @property
    def logger(self) -> Logger:
        """Get the logger."""
        if self._logger is None:
            return _default_logger
        return self._logger

    @logger.setter
    def logger(self, logger_: Logger) -> None:
        """Set the logger."""
        self._logger = logger_

    def _get_agent_context(self) -> AgentContext:
        """Get the agent context."""
        if self._agent_context is None:  # pragma: nocover
            raise ValueError("Agent context not set yet.")
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
        if self._skill is None:
            raise ValueError("Skill not set yet.")  # pragma: nocover
        return self._skill.configuration.public_id

    @property
    def is_active(self) -> bool:
        """Get the status of the skill (active/not active)."""
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        """Set the status of the skill (active/not active)."""
        self._is_active = value
        self.logger.debug(
            "New status of skill {}: is_active={}".format(
                self.skill_id, self._is_active
            )
        )

    @property
    def new_behaviours(self) -> "Queue[Behaviour]":
        """
        Queue for the new behaviours.

        This queue can be used to send messages to the framework
        to request the registration of a behaviour.

        :return the queue of new behaviours.
        """
        return self._new_behaviours_queue

    @property
    def new_handlers(self) -> "Queue[Handler]":
        """
        Queue for the new handlers.

        This queue can be used to send messages to the framework
        to request the registration of a handler.

        :return the queue of new handlers.
        """
        return self._new_handlers_queue

    @property
    def agent_addresses(self) -> Dict[str, str]:
        """Get addresses."""
        return self._get_agent_context().addresses

    @property
    def agent_address(self) -> str:
        """Get address."""
        return self._get_agent_context().address

    @property
    def connection_status(self) -> MultiplexerStatus:
        """Get connection status."""
        return self._get_agent_context().connection_status

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._get_agent_context().outbox

    @property
    def storage(self) -> Optional[Storage]:
        """Get optional storage for agent."""
        return self._get_agent_context().storage

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
        if self._skill is None:
            raise ValueError("Skill not initialized.")
        return self._get_agent_context().task_manager

    @property
    def default_ledger_id(self) -> str:
        """Get the default ledger id."""
        return self._get_agent_context().default_ledger_id

    @property
    def currency_denominations(self) -> Dict[str, str]:
        """Get a dictionary mapping ledger ids to currency denominations."""
        return self._get_agent_context().currency_denominations

    @property
    def search_service_address(self) -> Address:
        """Get the address of the search service."""
        return self._get_agent_context().search_service_address

    @property
    def decision_maker_address(self) -> Address:
        """Get the address of the decision maker."""
        return self._get_agent_context().decision_maker_address

    @property
    def handlers(self) -> SimpleNamespace:
        """Get handlers of the skill."""
        if self._skill is None:
            raise ValueError("Skill not initialized.")
        return SimpleNamespace(**self._skill.handlers)

    @property
    def behaviours(self) -> SimpleNamespace:
        """Get behaviours of the skill."""
        if self._skill is None:
            raise ValueError("Skill not initialized.")
        return SimpleNamespace(**self._skill.behaviours)

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
        if name is None:
            raise ValueError("SkillComponent name is not provided.")
        if skill_context is None:
            raise ValueError("SkillConext is not provided")
        if configuration is None:
            class_name = type(self).__name__
            configuration = SkillComponentConfiguration(class_name=class_name, **kwargs)
        self._configuration = configuration
        self._name = name
        self._context = skill_context
        if len(kwargs) != 0:
            self.context.logger.warning(
                "The kwargs={} passed to {} have not been set!".format(kwargs, name)
            )

    @property
    def name(self) -> str:
        """Get the name of the skill component."""
        return self._name

    @property
    def context(self) -> SkillContext:
        """Get the context of the skill component."""
        return self._context

    @property
    def skill_id(self) -> PublicId:
        """Get the skill id of the skill component."""
        return self.context.skill_id

    @property
    def configuration(self) -> SkillComponentConfiguration:
        """Get the skill component configuration."""
        if self._configuration is None:
            raise ValueError("Configuration not set.")  # pragma: nocover
        return self._configuration

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
        super_obj = super()
        if hasattr(super_obj, "setup"):
            super_obj.setup()  # type: ignore  # pylint: disable=no-member

    @abstractmethod
    def teardown(self) -> None:
        """
        Implement the teardown.

        :return: None
        """
        super_obj = super()
        if hasattr(super_obj, "teardown"):
            super_obj.teardown()  # type: ignore  # pylint: disable=no-member

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
        try:
            self.act()
        except _StopRuntime:
            raise
        except Exception as e:  # pylint: disable=broad-except
            e_str = parse_exception(e)
            raise AEAActException(
                f"An error occured during act of behaviour {self.context.skill_id}/{type(self).__name__}:\n{e_str}"
            )

    @classmethod
    def parse_module(  # pylint: disable=arguments-differ
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
            skill_context,
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
            skill_context.logger.debug(
                "Processing behaviour {}".format(behaviour_class_name)
            )
            if not behaviour_id.isidentifier():
                raise AEAComponentLoadException(  # pragma: nocover
                    f"'{behaviour_id}' is not a valid identifier."
                )
            behaviour_class = name_to_class.get(behaviour_class_name, None)
            if behaviour_class is None:
                skill_context.logger.warning(
                    "Behaviour '{}' cannot be found.".format(behaviour_class_name)
                )
            else:
                try:
                    behaviour = behaviour_class(
                        name=behaviour_id,
                        configuration=behaviour_config,
                        skill_context=skill_context,
                        **dict(behaviour_config.args),
                    )
                except Exception as e:  # pylint: disable=broad-except # pragma: nocover
                    e_str = parse_exception(e)
                    raise AEAInstantiationException(
                        f"An error occured during instantiation of behaviour {skill_context.skill_id}/{behaviour_config.class_name}:\n{e_str}"
                    )
                behaviours[behaviour_id] = behaviour

        return behaviours


class Handler(SkillComponent, ABC):
    """This class implements an abstract behaviour."""

    SUPPORTED_PROTOCOL = None  # type: Optional[PublicId]

    @abstractmethod
    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """

    def handle_wrapper(self, message: Message) -> None:
        """Wrap the call of the handler. This method must be called only by the framework."""
        try:
            self.handle(message)
        except _StopRuntime:
            raise
        except Exception as e:  # pylint: disable=broad-except
            e_str = parse_exception(e)
            raise AEAHandleException(
                f"An error occured during handle of handler {self.context.skill_id}/{type(self).__name__}:\n{e_str}"
            )

    @classmethod
    def parse_module(  # pylint: disable=arguments-differ
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
            skill_context,
            set(name_to_class.keys()),
            {handler_config.class_name for handler_config in handler_configs.values()},
            "handlers",
            path,
        )
        for handler_id, handler_config in handler_configs.items():
            handler_class_name = cast(str, handler_config.class_name)
            skill_context.logger.debug(
                "Processing handler {}".format(handler_class_name)
            )
            if not handler_id.isidentifier():
                raise AEAComponentLoadException(  # pragma: nocover
                    f"'{handler_id}' is not a valid identifier."
                )
            handler_class = name_to_class.get(handler_class_name, None)
            if handler_class is None:
                skill_context.logger.warning(
                    "Handler '{}' cannot be found.".format(handler_class_name)
                )
            else:
                try:
                    handler = handler_class(
                        name=handler_id,
                        configuration=handler_config,
                        skill_context=skill_context,
                        **dict(handler_config.args),
                    )
                except Exception as e:  # pylint: disable=broad-except # pragma: nocover
                    e_str = parse_exception(e)
                    raise AEAInstantiationException(
                        f"An error occured during instantiation of handler {skill_context.skill_id}/{handler_config.class_name}:\n{e_str}"
                    )
                handlers[handler_id] = handler

        return handlers


class Model(SkillComponent, ABC):
    """This class implements an abstract model."""

    def __init__(
        self,
        name: str,
        skill_context: SkillContext,
        configuration: Optional[SkillComponentConfiguration] = None,
        keep_terminal_state_dialogues: Optional[bool] = None,
        **kwargs,
    ) -> None:
        """
        Initialize a model.

        :param name: the name of the component.
        :param configuration: the configuration for the component.
        :param skill_context: the skill context.
        :param keep_terminal_state_dialogues: specify do dialogues in terminal state should stay or not

        :return: None
        """
        super().__init__(name, skill_context, configuration=configuration, **kwargs)

        # used by dialogues if mixed with the Model
        if keep_terminal_state_dialogues is not None:
            self._keep_terminal_state_dialogues = keep_terminal_state_dialogues

    def setup(self) -> None:
        """Set the class up."""
        super_obj = super()
        if hasattr(super_obj, "setup"):
            super_obj.setup()  # type: ignore  # pylint: disable=no-member

    def teardown(self) -> None:
        """Tear the class down."""
        super_obj = super()
        if hasattr(super_obj, "teardown"):
            super_obj.teardown()  # type: ignore  # pylint: disable=no-member

    @classmethod
    def parse_module(  # pylint: disable=arguments-differ
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
            skill_context.logger.debug("Trying to load module {}".format(module_path))
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
            skill_context,
            set(name_to_class.keys()),
            {model_config.class_name for model_config in model_configs.values()},
            "models",
            path,
        )
        for model_id, model_config in model_configs.items():
            model_class_name = model_config.class_name
            skill_context.logger.debug(
                "Processing model id={}, class={}".format(model_id, model_class_name)
            )
            if not model_id.isidentifier():
                raise AEAComponentLoadException(  # pragma: nocover
                    f"'{model_id}' is not a valid identifier."
                )
            model = name_to_class.get(model_class_name, None)
            if model is None:
                skill_context.logger.warning(
                    "Model '{}' cannot be found.".format(model_class_name)
                )
            else:
                try:
                    model_instance = model(
                        name=model_id,
                        skill_context=skill_context,
                        configuration=model_config,
                        **dict(model_config.args),
                    )
                except Exception as e:  # pylint: disable=broad-except # pragma: nocover
                    e_str = parse_exception(e)
                    raise AEAInstantiationException(
                        f"An error occured during instantiation of model {skill_context.skill_id}/{model_config.class_name}:\n{e_str}"
                    )
                instances[model_id] = model_instance
                setattr(skill_context, model_id, model_instance)
        return instances


def _check_duplicate_classes(name_class_pairs: Sequence[Tuple[str, Type]]):
    """
    Given a sequence of pairs (class_name, class_obj), check whether there are duplicates in the class names.

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
        **kwargs,
    ):
        """
        Initialize a skill.

        :param configuration: the skill configuration.
        :param skill_context: the skill context.
        :param handlers: dictionary of handlers.
        :param behaviours: dictionary of behaviours.
        :param models: dictionary of models.
        """
        if kwargs is not None:
            pass
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

        self._skill_context._skill = self
        self._set_models_on_context()

    def _set_models_on_context(self) -> None:
        """Set the models on the skill context."""
        if self._models != {}:
            for model_id, model_instance in self._models.items():
                if getattr(self._skill_context, model_id, None) is None:
                    setattr(self._skill_context, model_id, model_instance)

    @property
    def skill_context(self) -> SkillContext:
        """Get the skill context."""
        if self._skill_context is None:
            raise ValueError("Skill context not set.")  # pragma: nocover
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
    def from_dir(cls, directory: str, agent_context: AgentContext, **kwargs) -> "Skill":
        """
        Load the skill from a directory.

        :param directory: the directory to the skill package.
        :param agent_context: the skill context
        :return: the skill object.
        """
        configuration = cast(
            SkillConfig,
            load_component_configuration(ComponentType.SKILL, Path(directory)),
        )
        configuration.directory = Path(directory)
        return Skill.from_config(configuration, agent_context, **kwargs)

    @property
    def logger(self) -> Logger:
        """
        Get the logger.

        In the case of a skill, return the
        logger provided by the skill context.
        """
        return self.skill_context.logger

    @logger.setter
    def logger(self, *args) -> None:
        """Set the logger."""
        raise ValueError("Cannot set logger to a skill component.")

    @classmethod
    def from_config(
        cls, configuration: SkillConfig, agent_context: AgentContext, **kwargs
    ) -> "Skill":
        """
        Load the skill from configuration.

        :param configuration: a skill configuration. Must be associated with a directory.
        :param agent_context: the agent context.
        :return: the skill.
        """
        if configuration.directory is None:  # pragma: nocover
            raise ValueError("Configuration must be associated with a directory.")

        # we put the initialization here because some skill components
        # might need some info from the skill
        # (e.g. see https://github.com/fetchai/agents-aea/issues/1095)
        skill_context = SkillContext()
        skill_context.set_agent_context(agent_context)
        logger_name = f"aea.packages.{configuration.author}.skills.{configuration.name}"
        logger_name = _get_aea_logger_name_prefix(logger_name, agent_context.agent_name)
        _logger = AgentLoggerAdapter(
            logging.getLogger(logger_name), agent_context.agent_name
        )
        skill_context.logger = cast(Logger, _logger)

        skill = Skill(configuration, skill_context, **kwargs)

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
    skill_context: SkillContext,
    classes: Set[str],
    config_components: Set[str],
    item_type,
    skill_path,
):
    """Print a warning message if a skill component is not declared in the config files."""
    for class_name in classes.difference(config_components):
        skill_context.logger.warning(
            "Class {} of type {} found but not declared in the configuration file {}.".format(
                class_name, item_type, skill_path
            )
        )
