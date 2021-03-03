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
import types
from abc import ABC, abstractmethod
from collections import defaultdict
from logging import Logger
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Type, Union, cast

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
    enforce,
    parse_exception,
)
from aea.helpers.base import _get_aea_logger_name_prefix, load_module
from aea.helpers.logging import AgentLoggerAdapter
from aea.helpers.storage.generic_storage import Storage
from aea.mail.base import Envelope, EnvelopeContext
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
    ) -> None:
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

    def __getattr__(self, item: Any) -> Any:
        """Get attribute."""
        return super().__getattribute__(item)  # pragma: no cover

    def send_to_skill(
        self,
        message_or_envelope: Union[Message, Envelope],
        context: Optional[EnvelopeContext] = None,
    ) -> None:
        """
        Send message or envelope to another skill.

        :param message_or_envelope: envelope to send to another skill.
        if message passed it will be wrapped into envelope with optional envelope context.

        :return: None
        """
        if self._agent_context is None:  # pragma: nocover
            raise ValueError("agent context was not set!")
        self._agent_context.send_to_skill(message_or_envelope, context)


class SkillComponent(ABC):
    """This class defines an abstract interface for skill component classes."""

    def __init__(
        self,
        name: str,
        skill_context: SkillContext,
        configuration: Optional[SkillComponentConfiguration] = None,
        **kwargs: Any,
    ) -> None:
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
    ) -> dict:
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
        return _parse_module(path, behaviour_configs, skill_context, Behaviour)


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
        return _parse_module(path, handler_configs, skill_context, Handler)


class Model(SkillComponent, ABC):
    """This class implements an abstract model."""

    def __init__(
        self,
        name: str,
        skill_context: SkillContext,
        configuration: Optional[SkillComponentConfiguration] = None,
        keep_terminal_state_dialogues: Optional[bool] = None,
        **kwargs: Any,
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
        Parse the model module.

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


def _check_duplicate_classes(name_class_pairs: Sequence[Tuple[str, Type]]) -> None:
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

    __slots__ = ("_skill_context", "_handlers", "_behaviours", "_models")

    def __init__(
        self,
        configuration: SkillConfig,
        skill_context: Optional[SkillContext] = None,
        handlers: Optional[Dict[str, Handler]] = None,
        behaviours: Optional[Dict[str, Behaviour]] = None,
        models: Optional[Dict[str, Model]] = None,
        **kwargs: Any,
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
    def from_dir(
        cls, directory: str, agent_context: AgentContext, **kwargs: Any
    ) -> "Skill":
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
    def logger(self, *args: str) -> None:
        """Set the logger."""
        raise ValueError("Cannot set logger to a skill component.")

    @classmethod
    def from_config(
        cls, configuration: SkillConfig, agent_context: AgentContext, **kwargs: Any
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

        skill_component_loader = _SkillComponentLoader(
            configuration, skill_context, **kwargs
        )
        skill = skill_component_loader.load_skill()
        return skill


def _parse_module(
    path: str,
    component_configs: Dict[str, SkillComponentConfiguration],
    skill_context: SkillContext,
    component_class: Type,
) -> Dict[str, Any]:
    """
    Parse a module to find skill component classes, and instantiate them.

    This is a private framework function,
     used in SkillComponentClass.parse_module.

    :param path: path to the Python module.
    :param component_configs: the component configurations.
    :param skill_context: the skill context.
    :param component_class: the class of the skill components to be loaded.
    :return: A mapping from skill component name to the skill component instance.
    """
    components: Dict[str, Any] = {}
    component_type_name = component_class.__name__.lower()
    component_type_name_plural = component_type_name + "s"
    if component_configs == {}:
        return components
    component_names = set(config.class_name for _, config in component_configs.items())
    component_module = load_module(component_type_name_plural, Path(path))
    classes = inspect.getmembers(component_module, inspect.isclass)
    component_classes = list(
        filter(
            lambda x: any(re.match(component, x[0]) for component in component_names)
            and issubclass(x[1], component_class)
            and not str.startswith(x[1].__module__, "aea.")
            and not str.startswith(
                x[1].__module__,
                f"packages.{skill_context.skill_id.author}.skills.{skill_context.skill_id.name}",
            ),
            classes,
        )
    )

    name_to_class = dict(component_classes)
    _print_warning_message_for_non_declared_skill_components(
        skill_context,
        set(name_to_class.keys()),
        {
            component_config.class_name
            for component_config in component_configs.values()
        },
        component_type_name_plural,
        path,
    )
    for component_id, component_config in component_configs.items():
        component_class_name = cast(str, component_config.class_name)
        skill_context.logger.debug(
            f"Processing {component_type_name} {component_class_name}"
        )
        if not component_id.isidentifier():
            raise AEAComponentLoadException(  # pragma: nocover
                f"'{component_id}' is not a valid identifier."
            )
        component_class = name_to_class.get(component_class_name, None)
        if component_class is None:
            skill_context.logger.warning(
                f"{component_type_name.capitalize()} '{component_class_name}' cannot be found."
            )
        else:
            try:
                component = component_class(
                    name=component_id,
                    configuration=component_config,
                    skill_context=skill_context,
                    **dict(component_config.args),
                )
            except Exception as e:  # pylint: disable=broad-except # pragma: nocover
                e_str = parse_exception(e)
                raise AEAInstantiationException(
                    f"An error occured during instantiation of component {skill_context.skill_id}/{component_config.class_name}:\n{e_str}"
                )
            components[component_id] = component

    return components


def _print_warning_message_for_non_declared_skill_components(
    skill_context: SkillContext,
    classes: Set[str],
    config_components: Set[str],
    item_type: str,
    skill_path: str,
) -> None:
    """Print a warning message if a skill component is not declared in the config files."""
    for class_name in classes.difference(config_components):
        skill_context.logger.warning(
            "Class {} of type {} found but not declared in the configuration file {}.".format(
                class_name, item_type, skill_path
            )
        )


_SKILL_COMPONENT_TYPES = Type[Union[Handler, Behaviour, Model]]

_ConfigurationsHelperIndex = Dict[
    str,
    Dict[
        _SKILL_COMPONENT_TYPES,
        Dict[Optional[Path], Tuple[str, SkillComponentConfiguration]],
    ],
]
"""
The first level indexes by name. The second level by skill component
type: Handler, Behaviour and Model. The third level by path.
The values are the pairs (skill_component_id, configuration).
"""

_ComponentsHelperIndex = Dict[_SKILL_COMPONENT_TYPES, Dict[str, SkillComponent]]
"""
Helper index to store component instances.
"""


class _SkillComponentLoadingItem:
    """Class to represent a triple (component name, component configuration, component class)."""

    def __init__(
        self,
        name: str,
        config: SkillComponentConfiguration,
        class_: Type[SkillComponent],
        type_: _SKILL_COMPONENT_TYPES,
    ):
        """Initialize the item."""
        self.name = name
        self.config = config
        self.class_ = class_
        self.type_ = type_


class _SkillComponentLoader:
    """This class implements the loading policy for skill components."""

    def __init__(
        self, configuration: SkillConfig, skill_context: SkillContext, **kwargs: Any
    ):
        """Initialize the helper class."""
        enforce(
            configuration.directory is not None,
            "Configuration not associated to directory.",
        )
        self.configuration = configuration
        self.skill_directory = cast(Path, configuration.directory)
        self.skill_context = skill_context
        self.kwargs = kwargs

        self.skill_dotted_path = f"packages.{self.configuration.public_id.author}.skills.{self.configuration.public_id.name}"

    def load_skill(self) -> Skill:
        load_aea_package(self.configuration)
        python_modules: Set[Path] = self._get_python_modules()
        declared_component_classes: _ConfigurationsHelperIndex = self._get_declared_skill_component_configurations()
        component_classes_by_path: Dict[
            Path, Set[Type[SkillComponent]]
        ] = self._load_component_classes(python_modules)
        component_loading_items = self._match_class_and_configurations(
            component_classes_by_path, declared_component_classes
        )
        components = self._get_component_instances(component_loading_items)
        return self._instantiate_skill(components)

    def _instantiate_skill(self, components: _ComponentsHelperIndex) -> Skill:
        skill = Skill(self.configuration, self.skill_context, **self.kwargs)
        skill.handlers.update(cast(Dict[str, Handler], components.get(Handler, {})))
        skill.behaviours.update(
            cast(Dict[str, Behaviour], components.get(Behaviour, {}))
        )
        skill.models.update(cast(Dict[str, Model], components.get(Model, {})))
        return skill

    def _get_python_modules(self) -> Set[Path]:
        """
        Get all the Python modules of the skill package.

        We ignore '__pycache__' Python modules as they are not relevant.

        :return: a set of paths pointing to all the Python modules in the skill.
        """
        ignore_regex = "__pycache__*"
        all_python_modules = self.skill_directory.rglob("*.py")
        module_paths: Set[Path] = set(
            map(
                lambda p: Path(p).relative_to(self.skill_directory),
                filter(
                    lambda x: not re.match(ignore_regex, x.name), all_python_modules
                ),
            )
        )
        return module_paths

    def _compute_module_dotted_path(self, module_path: Path) -> str:
        """Compute the dotted path for a skill module."""
        suffix = ".".join(module_path.with_name(module_path.stem).parts)
        prefix = self.skill_dotted_path
        return prefix + "." + suffix

    def _filter_classes(
        self, classes: List[Tuple[str, Type]]
    ) -> List[Tuple[str, Type[SkillComponent]]]:
        """
        Filter classes of skill components.

        :param classes: a list of pairs (class name, class object)
        :return: a list of the same kind, but filtered with only skill component classes.
        """
        filtered_classes = filter(
            lambda name_and_class: issubclass(name_and_class[1], SkillComponent)
            and not str.startswith(name_and_class[1].__module__, "aea.")
            and str.startswith(name_and_class[1].__module__, self.skill_dotted_path),
            classes,
        )
        return cast(List[Tuple[str, Type[SkillComponent]]], list(filtered_classes))

    def _load_component_classes(
        self, module_paths: Set[Path]
    ) -> Dict[Path, Set[Type[SkillComponent]]]:
        """
        Load component classes from Python modules.

        :param module_paths: a set of paths to Python modules.
        :return: a mapping from path to skill component classes in that module
          (containing potential duplicates). Skill components in one path
          are
        """
        module_to_classes: Dict[Path, Set[Type[SkillComponent]]] = {}
        for module_path in module_paths:
            self.skill_context.logger.debug(f"Trying to load module {module_path}")
            module_dotted_path: str = self._compute_module_dotted_path(module_path)
            component_module: types.ModuleType = load_module(
                module_dotted_path, self.skill_directory / module_path
            )
            classes: List[Tuple[str, Type]] = inspect.getmembers(
                component_module, inspect.isclass
            )
            filtered_classes: List[
                Tuple[str, Type[SkillComponent]]
            ] = self._filter_classes(classes)
            module_to_classes[module_path] = {x[1] for x in filtered_classes}
        return module_to_classes

    def _get_declared_skill_component_configurations(
        self,
    ) -> _ConfigurationsHelperIndex:
        """
        Get all the declared skill component configurations.

        Do also consistency checks: If two skill component configurations have
          the same class_name and skill component type:
          - they must not have both file_path=None
          - they must not have the same file_path.

        :return:
        """
        handlers_by_id = dict(self.configuration.handlers.read_all())
        behaviours_by_id = dict(self.configuration.behaviours.read_all())
        models_by_id = dict(self.configuration.models.read_all())

        result: _ConfigurationsHelperIndex = {}
        for component_type, components_by_id in [
            (Handler, handlers_by_id),
            (Behaviour, behaviours_by_id),
            (Model, models_by_id),
        ]:
            for component_id, component_config in components_by_id.items():
                last_level_dict = result.setdefault(
                    component_config.class_name, {}
                ).setdefault(component_type, {})  # type: ignore
                # note: the following works also when file_path is None (unspecified).
                if component_config.file_path in last_level_dict:
                    existing_component_id = last_level_dict[component_config.file_path][
                        0
                    ]
                    enforce(
                        False,
                        self._get_same_name_same_path_error_message(
                            component_id,
                            existing_component_id,
                            component_config.class_name,
                            str(component_config.file_path),
                        ),
                    )
                last_level_dict[component_config.file_path] = (
                    component_id,
                    component_config,
                )
        return result

    def _get_same_name_same_path_error_message(
        self, component_id_1: str, component_id_2: str, name: str, path: str
    ) -> str:
        """
        Get error message for when two components have the same class names and the same file paths.

        Only used by '_get_declared_skill_component_configurations'.
        """
        return f"Skill component configurations for skill {self.configuration.public_id} is not correct. The components {component_id_1} and {component_id_2} have the same class name '{name}' and file path '{path}'. Please change either class name, or move one of the two component in another module."

    def _get_component_instances(
        self, component_loading_items: List[_SkillComponentLoadingItem],
    ) -> _ComponentsHelperIndex:
        """
        Instantiate classes declared in configuration files.

        :param component_loading_items: a list of loading items.
        :return: the instances of the skill components.
        """
        result: _ComponentsHelperIndex = {}
        for item in component_loading_items:
            instance = item.class_(
                name=item.name,
                configuration=item.config,
                skill_context=self.skill_context,
                **item.config.args,
            )
            result.setdefault(item.type_, {})[item.name] = instance
        return result

    @staticmethod
    def _get_skill_component_type(
        skill_component_type: Type[SkillComponent],
    ) -> Type[Union[Handler, Behaviour, Model]]:
        """Get the concrete skill component type."""
        parent_skill_component_types = list(
            filter(
                lambda class_: class_ in (Handler, Behaviour, Model),
                skill_component_type.__mro__,
            )
        )
        enforce(
            len(parent_skill_component_types) == 1,
            f"Class {skill_component_type.__name__} in module {skill_component_type.__module__} is not allowed to inherit from more than one skill component type. Found: {parent_skill_component_types}.",
        )
        return cast(
            Type[Union[Handler, Behaviour, Model]], parent_skill_component_types[0]
        )

    def _get_skill_component_classes_by_type(
        self, classes: Set[Type[SkillComponent]]
    ) -> Dict[_SKILL_COMPONENT_TYPES, Set[Type[SkillComponent]]]:
        """Get a mapping from types to sets of classes."""
        result: Dict[_SKILL_COMPONENT_TYPES, Set[Type[SkillComponent]]] = defaultdict(set)
        for class_ in classes:
            type_ = self._get_skill_component_type(class_)
            result[type_].add(class_)
        return dict(result)

    def _match_class_and_configurations(
        self,
        component_classes_by_path: Dict[Path, Set[Type[SkillComponent]]],
        declared_component_classes: _ConfigurationsHelperIndex,
    ) -> List[_SkillComponentLoadingItem]:
        """
        Match skill component type to its configuration.

        Given a class of a skill component, we can disambiguate it in these ways:
        - by its name
        - by its type (one of 'Handler', 'Behaviour', 'Model')
        - whether the user has set the 'file_path' field.
        If one of the skill component cannot be disambiguated, we raise error.

        In this function, the above criteria are applied in that order.

        :param component_classes_by_path:
        :return: None
        """
        result: List[_SkillComponentLoadingItem] = []
        component_classes_by_name_and_path: Dict[
            str, Dict[Path, Type[SkillComponent]]
        ] = {}
        component_classnames_to_classes: Dict[
            str, Set[Type[SkillComponent]]
        ] = defaultdict(set)
        component_classnames_to_paths: Dict[str, Set[Path]] = defaultdict(set)
        component_classnames_and_types_to_paths: Dict[
            str, Dict[_SKILL_COMPONENT_TYPES, Set[Path]]
        ] = {}

        # populate indexes
        for path, component_classes in component_classes_by_path.items():
            for component_class in component_classes:
                component_classname = component_class.__name__

                component_classes_by_name_and_path.setdefault(component_classname, {})[
                    path
                ] = component_class

                component_classnames_to_paths[component_classname].add(path)

                component_classnames_to_classes[component_classname].add(
                    component_class
                )

                type_ = self._get_skill_component_type(component_class)
                component_classnames_and_types_to_paths.setdefault(
                    component_classname, {}
                ).setdefault(type_, set()).add(path)

        # star matching class names with their configuration.
        loaded_classnames = set(component_classnames_to_paths.keys())
        for classname in loaded_classnames:

            if classname not in declared_component_classes:
                # we don't care about classes whose class name
                # does not appear in the configuration,
                # as it won't be loaded and can't be in conflict
                # with any other.
                continue

            paths = component_classnames_to_paths[classname]
            if len(paths) == 1:
                # done - this classname is present in only one module.
                path = list(paths)[0]
                skill_component_class = component_classes_by_name_and_path[classname][
                    path
                ]
                type_ = list(component_classnames_and_types_to_paths[classname].keys())[
                    0
                ]
                component_by_path = declared_component_classes[classname][type_]
                (
                    skill_component_id,
                    skill_component_configuration,
                ) = component_by_path.get(path, component_by_path[None])
                result.append(
                    _SkillComponentLoadingItem(
                        skill_component_id,
                        skill_component_configuration,
                        skill_component_class,
                        type_,
                    )
                )
                continue

            # if here, it means we found two components with the same class name,
            # in different modules. we need to check if we can disambiguate by type.

            classes = component_classnames_to_classes[classname]
            # a mapping from {Handler, Behaviour, Model} to the actual class.
            classes_by_type = self._get_skill_component_classes_by_type(classes)

            paths_by_types = component_classnames_and_types_to_paths[classname]
            ambiguous_types: Dict[_SKILL_COMPONENT_TYPES, Set[Path]] = {}

            for type_, paths in paths_by_types.items():
                if len(paths) > 1:
                    # ambiguous, cannot resolve
                    ambiguous_types[type_] = paths
                    continue
                else:
                    # done - we can disambiguate the classes by type.
                    # the following instructions are legal because of the previous ambiguity checks
                    skill_component_class = list(classes_by_type[type_])[0]
                    path = list(paths_by_types[type_])[0]
                    component_by_path = declared_component_classes[classname][type_]
                    (
                        skill_component_id,
                        skill_component_configuration,
                    ) = component_by_path.get(path, component_by_path[None])
                    result.append(
                        _SkillComponentLoadingItem(
                            skill_component_id,
                            skill_component_configuration,
                            skill_component_class,
                            type_,
                        )
                    )
                continue

            # If here, it means there are classes with the same name
            # and the same type, but in different modules.
            # Read the configurations to see if we can disambiguate them.
            for class_type, _ in ambiguous_types.items():
                classes_to_be_matched: Set[Type[SkillComponent]] = classes_by_type[
                    class_type
                ]

                enforce(classname in declared_component_classes.keys(), "")
                enforce(class_type in declared_component_classes[classname].keys(), "")
                configurations_by_path = declared_component_classes[classname][
                    class_type
                ]

                resolved_classes: Set[Type[SkillComponent]] = set()
                resolved_configurations: Set[
                    Tuple[str, SkillComponentConfiguration]
                ] = set()

                for (
                    declared_path,
                    (skill_component_id, skill_component_configuration),
                ) in configurations_by_path.items():
                    if declared_path is None:
                        # this will be resolved by exclusion, if possible
                        continue

                    matched_class = component_classes_by_name_and_path[classname][
                        declared_path
                    ]
                    resolved_classes.add(matched_class)
                    resolved_configurations.add(
                        (skill_component_id, skill_component_configuration)
                    )
                    result.append(
                        _SkillComponentLoadingItem(
                            skill_component_id,
                            skill_component_configuration,
                            matched_class,
                            class_type,
                        )
                    )

                unresolved_configurations = set(
                    configurations_by_path.values()
                ).difference(resolved_configurations)
                unresolved_classes = classes_to_be_matched.difference(resolved_classes)
                if len(unresolved_configurations) == 0:
                    continue

                enforce(
                    len(unresolved_configurations) == 1,
                    f"Got more than one unresolved configuration with same class name and type: {' '.join([id_ for id_, _ in unresolved_configurations])}",
                )
                unresolved_configuration_id, unresolved_configuration = list(
                    unresolved_configurations
                )[0]

                enforce(
                    len(unresolved_classes) != 0,
                    f"Cannot find class for configuration {unresolved_configuration_id}",
                )
                enforce(
                    len(unresolved_classes) == 1,
                    f"Cannot resolve ambiguity of the following classes for component '{unresolved_configuration_id}': {' '.join([c.__name__ for c in unresolved_classes])}",
                )
                unresolved_class = list(unresolved_classes)[0]

                result.append(
                    _SkillComponentLoadingItem(
                        unresolved_configuration_id,
                        unresolved_configuration,
                        unresolved_class,
                        class_type,
                    )
                )

        return result
