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
import types
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type

from aea.configurations.base import ComponentType, ComponentConfiguration, ComponentId


class Component(ABC):

    def __init__(
        self,
        component_configuration: ComponentConfiguration,
    ):
        """
        Initialize a package.

        :param component_configuration: the package configuration.
        """
        self._configuration = component_configuration

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
    def public_id(self):
        """Get the public id."""
        return self._configuration.public_id

    @classmethod
    @abstractmethod
    def load_from_directory(cls, directory: Path) -> "Component":
        """Load a component from the directory."""
