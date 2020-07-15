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
import logging
import types
from abc import ABC
from pathlib import Path
from typing import Dict, Optional

from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    PublicId,
)
from aea.helpers.logging import WithLogger

logger = logging.getLogger(__name__)


class Component(ABC, WithLogger):
    """Abstract class for an agent component."""

    def __init__(
        self,
        configuration: Optional[ComponentConfiguration] = None,
        is_vendor: bool = False,
    ):
        """
        Initialize a package.

        :param configuration: the package configuration.
        :param is_vendor: whether the package is vendorized.
        """
        WithLogger.__init__(self)
        self._configuration = configuration
        self._directory = None  # type: Optional[Path]
        self._is_vendor = is_vendor

        # mapping from import path to module object
        # the keys are dotted paths of Python modules.
        self.importpath_to_module = {}  # type: Dict[str, types.ModuleType]

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return self.configuration.component_type

    @property
    def is_vendor(self) -> bool:
        """Get whether the component is vendorized or not."""
        return self._is_vendor

    @property
    def prefix_import_path(self):
        """Get the prefix import path for this component."""
        return self.configuration.prefix_import_path

    @property
    def component_id(self) -> ComponentId:
        """Ge the package id."""
        return self.configuration.component_id

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return self.configuration.public_id

    @property
    def configuration(self) -> ComponentConfiguration:
        """Get the component configuration."""
        assert (
            self._configuration is not None
        ), "The component is not associated with a configuration."
        return self._configuration

    @property
    def directory(self) -> Path:
        """Get the directory. Raise error if it has not been set yet."""
        assert self._directory is not None, "Directory not set yet."
        return self._directory

    @directory.setter
    def directory(self, path: Path) -> None:
        """Set the directory. Raise error if already set."""
        assert self._directory is None, "Directory already set."
        self._directory = path
