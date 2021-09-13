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
import importlib.util
import logging
import sys
import types
from abc import ABC
from pathlib import Path
from typing import Any, Optional

from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    PublicId,
)
from aea.configurations.constants import PACKAGES
from aea.exceptions import AEAEnforceError
from aea.helpers.logging import WithLogger


_default_logger = logging.getLogger(__name__)


class Component(ABC, WithLogger):
    """Abstract class for an agent component."""

    __slots__ = ("_configuration", "_directory", "_is_vendor")

    def __init__(
        self,
        configuration: Optional[ComponentConfiguration] = None,
        is_vendor: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a package.

        :param configuration: the package configuration.
        :param is_vendor: whether the package is vendorized.
        :param kwargs: the keyword arguments for the logger.
        """
        WithLogger.__init__(self, **kwargs)
        self._configuration = configuration
        self._directory = None  # type: Optional[Path]
        self._is_vendor = is_vendor

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return self.configuration.component_type

    @property
    def is_vendor(self) -> bool:
        """Get whether the component is vendorized or not."""
        return self._is_vendor

    @property
    def prefix_import_path(self) -> str:
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
        if self._configuration is None:  # pragma: nocover
            raise ValueError("The component is not associated with a configuration.")
        return self._configuration

    @property
    def directory(self) -> Path:
        """Get the directory. Raise error if it has not been set yet."""
        if self._directory is None:
            raise ValueError("Directory not set yet.")
        return self._directory

    @directory.setter
    def directory(self, path: Path) -> None:
        """Set the directory. Raise error if already set."""
        if self._directory is not None:  # pragma: nocover
            raise ValueError("Directory already set.")
        self._directory = path

    @property
    def build_directory(self) -> Optional[str]:
        """Get build directory for the component."""
        return self.configuration.build_directory


def load_aea_package(configuration: ComponentConfiguration) -> None:
    """
    Load the AEA package from configuration.

    It adds all the __init__.py modules into `sys.modules`.

    :param configuration: the configuration object.
    """
    dir_ = configuration.directory
    if dir_ is None:  # pragma: nocover
        raise ValueError("configuration's directory is None.")
    author = configuration.author
    package_type_plural = configuration.component_type.to_plural()
    package_name = configuration.name
    perform_load_aea_package(dir_, author, package_type_plural, package_name)


def perform_load_aea_package(
    dir_: Path, author: str, package_type_plural: str, package_name: str
) -> None:
    """
    Load the AEA package from values provided.

    It adds all the __init__.py modules into `sys.modules`.

    :param dir_: path of the component.
    :param author: str
    :param package_type_plural: str
    :param package_name: str
    """

    if dir_ is None or not dir_.exists():  # pragma: nocover
        raise AEAEnforceError(f"configuration directory `{dir_}` does not exists.")

    prefix_root = PACKAGES
    prefix_author = prefix_root + f".{author}"
    prefix_pkg_type = prefix_author + f".{package_type_plural}"

    prefix_root_module = types.ModuleType(prefix_root)
    prefix_root_module.__path__ = None  # type: ignore
    sys.modules[prefix_root] = sys.modules.get(prefix_root, prefix_root_module)
    author_module = types.ModuleType(prefix_author)
    author_module.__path__ = None  # type: ignore
    sys.modules[prefix_author] = sys.modules.get(prefix_author, author_module)
    prefix_pkg_type_module = types.ModuleType(prefix_pkg_type)
    prefix_pkg_type_module.__path__ = None  # type: ignore
    sys.modules[prefix_pkg_type] = sys.modules.get(
        prefix_pkg_type, prefix_pkg_type_module
    )

    prefix_pkg = prefix_pkg_type + f".{package_name}"

    for subpackage_init_file in dir_.rglob("__init__.py"):
        parent_dir = subpackage_init_file.parent
        relative_parent_dir = parent_dir.relative_to(dir_)
        if relative_parent_dir == Path("."):
            # this handles the case when 'subpackage_init_file'
            # is path/to/package/__init__.py
            import_path = prefix_pkg
        else:  # pragma: nocover
            import_path = prefix_pkg + "." + ".".join(relative_parent_dir.parts)

        spec = importlib.util.spec_from_file_location(import_path, subpackage_init_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[import_path] = module
        _default_logger.debug(f"loading {import_path}: {module}")
        spec.loader.exec_module(module)  # type: ignore
