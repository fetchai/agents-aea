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
import os
import types
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type, cast, Optional

from aea.configurations.base import ComponentType, ComponentConfiguration, ComponentId, ProtocolConfig, PublicId
from aea.helpers.base import load_module, _SysModules, load_init_modules


class Component(ABC):

    def __init__(
        self,
        component_configuration: ComponentConfiguration
    ):
        """
        Initialize a package.

        :param component_configuration: the package configuration.
        """
        self._configuration = component_configuration
        self._directory = None  # type: Optional[Path]

        # mapping from import path to module object
        self.importpath_to_module = {}  # type: Dict[str, types.ModuleType]

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return self._configuration.component_type

    @property
    def component_id(self) -> ComponentId:
        """Ge the package id."""
        return self._configuration.component_id

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return self._configuration.public_id

    @property
    def configuration(self):
        """Get the component configuration."""
        return self._configuration

    @property
    def directory(self) -> Optional[Path]:
        """Get the directory, or None if the component is not associated with any directory."""
        return self._directory

    def _load_component_modules(self):
        """
        Load component modules. This method is called in _load_from_directory.

        Please check the implementation of the concrete component classes.
        """

    @classmethod
    def load_from_directory(cls, component_type: ComponentType, directory: Path) -> "Component":
        """Load a component from the directory."""
        configuration = ComponentConfiguration.load(component_type, directory)
        component_object = cls(configuration)
        component_object._directory = directory
        init_modules = load_init_modules(directory)
        component_object.importpath_to_module.update(init_modules)
        with _SysModules.load_modules(list(init_modules.items())):
            component_object._load_component_modules()
        return component_object

