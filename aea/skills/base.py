# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
from copy import copy
from logging import Logger
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, cast

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

        :param agent_context: the agent context.
        :param skill: the skill.
        """
        self._agent_context = agent_context  # type: Optional[AgentContext]
        self._in_queue = Queue()  # type: Queue
        self._skill = skill  # type: Optional[Skill]

        self._is_active = True  # type: bool
        self._new_behaviours_queue = queue.Queue()  # type: Queue
        self._new_handlers_queue = queue.Queue()  # type: Queue
        self._logger: Optional[Logger] = None

    @property
    def is_abstract_component(self) -> bool:
        """Get if the skill is abstract."""
        if self._skill is None:
            raise ValueError("Skill not set yet.")  # pragma: nocover
        return self._skill.configuration.is_abstract_component

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

    @property
    def data_dir(self) -> str:
        """Get the agent's data directory"""
        return self._get_agent_context().data_dir

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

        :return: the queue of new behaviours.
        """
        return self._new_behaviours_queue

    @property
    def new_handlers(self) -> "Queue[Handler]":
        """
        Queue for the new handlers.

        This queue can be used to send messages to the framework
        to request the registration of a handler.

        :return: the queue of new handlers.
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
    def public_key(self) -> str:
        """Get public key."""
        return self._get_agent_context().public_key

    @property
    def public_keys(self) -> Dict[str, str]:
        """Get public keys."""
        return self._get_agent_context().public_keys

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

        If message passed it will be wrapped into envelope with optional envelope context.

        :param message_or_envelope: envelope to send to another skill.
        :param context: the optional envelope context
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
        :param kwargs: the keyword arguments.
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
        """Implement the setup."""
        super_obj = super()
        if hasattr(super_obj, "setup"):
            super_obj.setup()  # type: ignore  # pylint: disable=no-member

    @abstractmethod
    def teardown(self) -> None:
        """Implement the teardown."""
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
    """
    This class implements an abstract behaviour.

    In a subclass of Behaviour, the flag 'is_programmatically_defined'
     can be used by the developer to signal to the framework that the class
     is meant to be used programmatically; hence, in case the class is
     not declared in the configuration file but it is present in a skill
     module, the framework will just ignore this class instead of printing
     a warning message.
    """

    is_programmatically_defined: bool = False

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
                f"An error occurred during act of behaviour {self.context.skill_id}/{type(self).__name__}:\n{e_str}"
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
    """
    This class implements an abstract behaviour.

    In a subclass of Handler, the flag 'is_programmatically_defined'
     can be used by the developer to signal to the framework that the component
     is meant to be used programmatically; hence, in case the class is
     not declared in the configuration file but it is present in a skill
     module, the framework will just ignore this class instead of printing
     a warning message.

    SUPPORTED_PROTOCOL is read by the framework when the handlers are loaded
     to register them as 'listeners' to the protocol identified by the specified
     public id. Whenever a message of protocol 'SUPPORTED_PROTOCOL' is sent
     to the agent, the framework will call the 'handle' method.
    """

    SUPPORTED_PROTOCOL: Optional[PublicId] = None
    is_programmatically_defined: bool = False

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
                f"An error occurred during handle of handler {self.context.skill_id}/{type(self).__name__}:\n{e_str}"
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

    def protocol_dialogues(self, attribute: Optional[str] = None):  # type: ignore
        """Protocol dialogues"""
        if self.SUPPORTED_PROTOCOL is None:
            raise ValueError(f"SUPPORTED_PROTOCOL not set on {self}")
        attribute = (
            (cast(PublicId, self.SUPPORTED_PROTOCOL).name + "_dialogues")
            if attribute is None
            else attribute
        )
        return getattr(self.context, attribute)


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
        :param kwargs: the keyword arguments.
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
        return _parse_module(path, model_configs, skill_context, Model)


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
        :param kwargs: the keyword arguments.
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
        :param agent_context: the skill context.
        :param kwargs: the keyword arguments.
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

        :return: the logger
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
        :param kwargs: the keyword arguments.
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
                    f"An error occurred during instantiation of component {skill_context.skill_id}/{component_config.class_name}:\n{e_str}"
                )
            components[component_id] = component

    return components


def _print_warning_message_for_non_declared_skill_components(
    skill_context: SkillContext,
    classes: Set[str],
    config_components: Set[str],
    item_type: str,
    module_path: str,
) -> None:
    """Print a warning message if a skill component is not declared in the config files."""
    for class_name in classes.difference(config_components):
        skill_context.logger.warning(
            "Class {} of type {} found in skill module {} but not declared in the configuration file.".format(
                class_name, item_type, module_path
            )
        )


_SKILL_COMPONENT_TYPES = Type[Union[Handler, Behaviour, Model]]

_ComponentsHelperIndex = Dict[_SKILL_COMPONENT_TYPES, Dict[str, SkillComponent]]
"""
Helper index to store component instances.
"""


class _SkillComponentLoadingItem:  # pylint: disable=too-few-public-methods
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

        self.skill = Skill(self.configuration, self.skill_context, **self.kwargs)
        self.skill_dotted_path = f"packages.{self.configuration.public_id.author}.skills.{self.configuration.public_id.name}"

    def load_skill(self) -> Skill:
        """Load the skill."""
        load_aea_package(self.configuration)
        python_modules: Set[Path] = self._get_python_modules()
        declared_component_classes: Dict[
            _SKILL_COMPONENT_TYPES, Dict[str, SkillComponentConfiguration]
        ] = self._get_declared_skill_component_configurations()
        component_classes_by_path: Dict[
            Path, Set[Tuple[str, Type[SkillComponent]]]
        ] = self._load_component_classes(python_modules)
        component_loading_items = self._match_class_and_configurations(
            component_classes_by_path, declared_component_classes
        )
        components = self._get_component_instances(component_loading_items)
        self._update_skill(components)
        return self.skill

    def _update_skill(self, components: _ComponentsHelperIndex) -> None:
        self.skill.handlers.update(
            cast(Dict[str, Handler], components.get(Handler, {}))
        )
        self.skill.behaviours.update(
            cast(Dict[str, Behaviour], components.get(Behaviour, {}))
        )
        self.skill.models.update(cast(Dict[str, Model], components.get(Model, {})))
        self.skill._set_models_on_context()  # pylint: disable=protected-access

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

    @classmethod
    def _compute_module_dotted_path(cls, module_path: Path) -> str:
        """Compute the dotted path for a skill module."""
        suffix = ".".join(module_path.with_name(module_path.stem).parts)
        return suffix

    def _filter_classes(
        self, classes: List[Tuple[str, Type]]
    ) -> List[Tuple[str, Type[SkillComponent]]]:
        """
        Filter classes of skill components.

        The following filters are applied:
        - the class must be a subclass of "SkillComponent";
        - its __module__ attribute must not start with 'aea.' (we exclude classes provided by the framework)
        - its __module__ attribute starts with the expected dotted path of this skill.
            In particular, it should not be imported from another skill.

        :param classes: a list of pairs (class name, class object)
        :return: a list of the same kind, but filtered with only skill component classes.
        """
        filtered_classes = filter(
            lambda name_and_class: issubclass(name_and_class[1], SkillComponent)
            # the following condition filters out classes imported from 'aea'
            and not str.startswith(name_and_class[1].__module__, "aea.")
            # the following condition filters out classes imported
            # from other skills
            and not str.startswith(
                name_and_class[1].__module__, self.skill_dotted_path + "."
            ),
            classes,
        )
        classes = list(filtered_classes)
        return cast(List[Tuple[str, Type[SkillComponent]]], classes)

    def _load_component_classes(
        self, module_paths: Set[Path]
    ) -> Dict[Path, Set[Tuple[str, Type[SkillComponent]]]]:
        """
        Load component classes from Python modules.

        :param module_paths: a set of paths to Python modules.
        :return: a mapping from path to skill component classes in that module (containing potential duplicates). Skill components in one path are
        """
        module_to_classes: Dict[Path, Set[Tuple[str, Type[SkillComponent]]]] = {}
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
            module_to_classes[module_path] = set(filtered_classes)
        return module_to_classes

    def _get_declared_skill_component_configurations(
        self,
    ) -> Dict[_SKILL_COMPONENT_TYPES, Dict[str, SkillComponentConfiguration]]:
        """
        Get all the declared skill component configurations.

        :return: dictionary of declared skill component configurations
        """
        handlers_by_id = dict(self.configuration.handlers.read_all())
        behaviours_by_id = dict(self.configuration.behaviours.read_all())
        models_by_id = dict(self.configuration.models.read_all())

        result: Dict[
            _SKILL_COMPONENT_TYPES, Dict[str, SkillComponentConfiguration]
        ] = {}
        for component_type, components_by_id in [
            (Handler, handlers_by_id),
            (Behaviour, behaviours_by_id),
            (Model, models_by_id),
        ]:
            for component_id, component_config in components_by_id.items():
                result.setdefault(component_type, {})[component_id] = component_config  # type: ignore
        return result

    def _get_component_instances(
        self,
        component_loading_items: List[_SkillComponentLoadingItem],
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

    @classmethod
    def _get_skill_component_type(
        cls,
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

    def _match_class_and_configurations(
        self,
        component_classes_by_path: Dict[Path, Set[Tuple[str, Type[SkillComponent]]]],
        declared_component_classes: Dict[
            _SKILL_COMPONENT_TYPES, Dict[str, SkillComponentConfiguration]
        ],
    ) -> List[_SkillComponentLoadingItem]:
        """
        Match skill component classes to their configurations.

        Given a class of a skill component, we can disambiguate it in three ways:
        - by its name
        - by its type (one of 'Handler', 'Behaviour', 'Model')
        - whether the user has set the 'file_path' field.
        If one of the skill component cannot be disambiguated, we raise error.

        In this function, the above criteria are applied in that order.

        :param component_classes_by_path: the component classes by path
        :param declared_component_classes: the declared component classes
        :return: list of skill component loading items
        """
        result: List[_SkillComponentLoadingItem] = []

        class_index: Dict[
            str, Dict[_SKILL_COMPONENT_TYPES, Set[Type[SkillComponent]]]
        ] = {}
        used_classes: Set[Type[SkillComponent]] = set()
        not_resolved_configurations: Dict[
            Tuple[_SKILL_COMPONENT_TYPES, str], SkillComponentConfiguration
        ] = {}

        # populate indexes
        for _path, component_classes in component_classes_by_path.items():
            for (component_classname, _component_class) in component_classes:
                type_ = self._get_skill_component_type(_component_class)
                class_index.setdefault(component_classname, {}).setdefault(
                    type_, set()
                ).add(_component_class)

        for component_type, by_id in declared_component_classes.items():
            for component_id, component_config in by_id.items():
                path = component_config.file_path
                class_name = component_config.class_name
                if path is not None:
                    classes_in_path = component_classes_by_path[path]
                    component_class_or_none: Optional[Type[SkillComponent]] = next(
                        (
                            actual_class
                            for actual_class_name, actual_class in classes_in_path
                            if actual_class_name == class_name
                        ),
                        None,
                    )
                    enforce(
                        component_class_or_none is not None,
                        self._get_error_message_prefix()
                        + f"Cannot find class '{class_name}' for component '{component_id}' of type '{self._type_to_str(component_type)}' of skill '{self.configuration.public_id}' in module {path}",
                    )
                    component_class = cast(
                        Type[SkillComponent], component_class_or_none
                    )
                    actual_component_type = self._get_skill_component_type(
                        component_class
                    )
                    enforce(
                        actual_component_type == component_type,
                        self._get_error_message_prefix()
                        + f"Found class '{class_name}' for component '{component_id}' of type '{self._type_to_str(component_type)}' of skill '{self.configuration.public_id}' in module {path}, but the expected type was {self._type_to_str(component_type)}, found {self._type_to_str(actual_component_type)} ",
                    )
                    used_classes.add(component_class)
                    result.append(
                        _SkillComponentLoadingItem(
                            component_id,
                            component_config,
                            component_class,
                            component_type,
                        )
                    )
                else:
                    # process the configuration at the end of the loop
                    not_resolved_configurations[
                        (component_type, component_id)
                    ] = component_config

        for (component_type, component_id), component_config in copy(
            not_resolved_configurations
        ).items():
            class_name = component_config.class_name
            classes_by_type = class_index.get(class_name, {})
            enforce(
                class_name in class_index and component_type in classes_by_type,
                self._get_error_message_prefix()
                + f"Cannot find class '{class_name}' for skill component '{component_id}' of type '{self._type_to_str(component_type)}'",
            )
            classes = classes_by_type[component_type]
            not_used_classes = classes.difference(used_classes)
            enforce(
                not_used_classes != 0,
                f"Cannot find class of skill '{self.configuration.public_id}' for component configuration '{component_id}' of type '{self._type_to_str(component_type)}'.",
            )
            enforce(
                len(not_used_classes) == 1,
                self._get_error_message_ambiguous_classes(
                    class_name, not_used_classes, component_type, component_id
                ),
            )
            not_used_class = list(not_used_classes)[0]
            result.append(
                _SkillComponentLoadingItem(
                    component_id, component_config, not_used_class, component_type
                )
            )
            used_classes.add(not_used_class)

        self._print_warning_message_for_unused_classes(
            component_classes_by_path, used_classes
        )
        return result

    def _print_warning_message_for_unused_classes(
        self,
        component_classes_by_path: Dict[Path, Set[Tuple[str, Type[SkillComponent]]]],
        used_classes: Set[Type[SkillComponent]],
    ) -> None:
        """
        Print warning message for every unused class.

        :param component_classes_by_path: the component classes by path.
        :param used_classes: the classes used.
        """
        for path, set_of_class_name_pairs in component_classes_by_path.items():
            # take only classes, not class names
            set_of_classes = {pair[1] for pair in set_of_class_name_pairs}
            set_of_unused_classes = set(
                filter(lambda x: x not in used_classes, set_of_classes)
            )
            # filter out classes that are from other packages
            set_of_unused_classes = set(
                filter(
                    lambda x: not str.startswith(x.__module__, "packages."),
                    set_of_unused_classes,
                )
            )

            if len(set_of_unused_classes) == 0:
                # all classes in the module are used!
                continue

            # for each unused class, print a warning message. However,
            # if it is a Handler or a Behaviour, print the message
            # only if 'is_programmatically_defined' is not True
            for unused_class in set_of_unused_classes:
                component_type_class = self._get_skill_component_type(unused_class)
                if (
                    issubclass(unused_class, (Handler, Behaviour))
                    and cast(
                        Union[Handler, Behaviour], unused_class
                    ).is_programmatically_defined
                ):
                    continue
                _print_warning_message_for_non_declared_skill_components(
                    self.skill_context,
                    {unused_class.__name__},
                    set(),
                    self._type_to_str(component_type_class),
                    str(path),
                )

    @classmethod
    def _type_to_str(cls, component_type: _SKILL_COMPONENT_TYPES) -> str:
        """Get the string of a component type."""
        return component_type.__name__.lower()

    def _get_error_message_prefix(self) -> str:
        """Get error message prefix."""
        return f"Error while loading skill '{self.configuration.public_id}': "

    def _get_error_message_ambiguous_classes(
        self,
        class_name: str,
        not_used_classes: Set,
        component_type: _SKILL_COMPONENT_TYPES,
        component_id: str,
    ) -> str:
        return f"{self._get_error_message_prefix()}found many classes with name '{class_name}' for component '{component_id}' of type '{self._type_to_str(component_type)}' in the following modules: {', '.join([c.__module__ for c in not_used_classes])}"
