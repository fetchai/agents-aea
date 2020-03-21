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

"""This module contains definitions of agent components."""
import inspect
import logging
import re
import types
from abc import ABC
from pathlib import Path
from typing import Dict, Optional, Type, cast

from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    PublicId,
)
from aea.helpers.base import _SysModules, load_init_modules, load_module

logger = logging.getLogger(__name__)


def component_class_from_type(component_type: ComponentType) -> Type["Component"]:
    """Get component class from component type."""
    from aea.protocols.base import Protocol
    from aea.connections.base import Connection
    from aea.skills.base import Skill

    if component_type == ComponentType.PROTOCOL:
        return Protocol
    elif component_type == ComponentType.CONNECTION:
        return Connection
    elif component_type == ComponentType.SKILL:
        return Skill
    elif component_type == ComponentType.CONTRACT:
        # TODO
        raise NotImplementedError
    else:
        raise ValueError


class Component(ABC):
    """Abstract class for an agent component."""

    def __init__(self, configuration: ComponentConfiguration, is_vendor: bool = False):
        """
        Initialize a package.

        :param configuration: the package configuration.
        :param is_vendor: whether the package is vendorized.
        """
        self._configuration = configuration
        self._directory = None  # type: Optional[Path]
        self._is_vendor = is_vendor

        # mapping from import path to module object
        # the keys are dotted paths of Python modules.
        self.importpath_to_module = {}  # type: Dict[str, types.ModuleType]

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return self._configuration.component_type

    @property
    def is_vendor(self) -> bool:
        """Get whether the component is vendorized or not."""
        return self._is_vendor

    @property
    def prefix_import_path(self):
        """Get the prefix import path for this component."""
        if self.is_vendor:
            return "packages.{}.{}.{}".format(
                self.public_id.author,
                self.component_type.to_plural(),
                self.public_id.name,
            )
        else:
            return "packages.{}.{}".format(
                self.component_type.to_plural(), self.public_id.name
            )

    @property
    def component_id(self) -> ComponentId:
        """Ge the package id."""
        return self._configuration.component_id

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return self._configuration.public_id

    @property
    def configuration(self) -> ComponentConfiguration:
        """Get the component configuration."""
        return self._configuration

    @property
    def directory(self) -> Optional[Path]:
        """Get the directory, or None if the component is not associated with any directory."""
        return self._directory

    def setup(self, *args, **kwargs):
        """
        Set the component up.

        This method is called by the framework before running the agent.
        The implementation varies depending on the type of component.
        Please check the concrete component classes.
        """

    @classmethod
    def _load_connection(cls, configuration: ConnectionConfig, directory: Path):
        """Load a connection object from a directory."""
        connection_module = load_module(
            "connection_module", directory / "connection.py"
        )
        classes = inspect.getmembers(connection_module, inspect.isclass)
        connection_classes = list(
            filter(lambda x: re.match("\\w+Connection", x[0]), classes)
        )
        name_to_class = dict(connection_classes)
        connection_class_name = cast(str, configuration.class_name)
        logger.debug("Processing connection {}".format(connection_class_name))
        connection_class = name_to_class.get(connection_class_name, None)
        if connection_class is None:
            raise ValueError(
                "Connection class '{}' not found.".format(connection_class_name)
            )

        # TODO address?
        connection = connection_class.from_config(
            "address", connection_configuration=configuration
        )
        connection._configuration = configuration
        return connection

    @classmethod
    def load_from_directory(
        cls, component_type: ComponentType, directory: Path
    ) -> "Component":
        """Load a component from the directory."""
        configuration = ComponentConfiguration.load(component_type, directory)
        if component_type == ComponentType.CONNECTION:
            # the connection case is an exception,
            # because developers define custom initializers
            # for connections, so we can't use the constructor (see below "cls(configuration)")
            # TODO that suggests a design smell. Solve it.
            configuration = cast(ConnectionConfig, configuration)
            component_object = cls._load_connection(configuration, directory)
        else:
            component_class = component_class_from_type(component_type)
            component_object = component_class(configuration=configuration)
        component_object._directory = directory
        init_modules = load_init_modules(directory)
        component_object.importpath_to_module.update(init_modules)
        with _SysModules.load_modules(list(init_modules.items())):
            component_object.setup()
        return component_object
