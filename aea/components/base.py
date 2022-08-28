# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
import re
import sys
import types
from abc import ABC
from collections import defaultdict
from importlib.machinery import ModuleSpec
from pathlib import Path
from textwrap import indent
from typing import Any, Dict, Optional, Set, cast

from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    PublicId,
)
from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PackageIdPrefix, PackageType
from aea.exceptions import AEAEnforceError, AEAPackageLoadingError, enforce
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
    _CheckUsedDependencies(configuration).run_check()
    perform_load_aea_package(dir_, author, package_type_plural, package_name)


class _CheckUsedDependencies:
    """Auxiliary class to keep track of used packages in import statements of package modules."""

    package_type_plural_regex = (
        rf"({PackageType.AGENT.to_plural()}|"
        rf"{PackageType.PROTOCOL.to_plural()}|"
        rf"{PackageType.SKILL.to_plural()}|"
        rf"{PackageType.CONNECTION.to_plural()}|"
        rf"{PackageType.CONTRACT.to_plural()}|"
        rf"{PackageType.SERVICE.to_plural()})"
    )

    def __init__(self, configuration: ComponentConfiguration) -> None:
        """Initialize the instance."""
        self.configuration = configuration
        enforce(
            configuration.directory is not None,
            "input configuration must be associated to a directory",
            exception_class=ValueError,
        )
        self.directory = configuration.directory

    @classmethod
    def _extract_imported_packages_as_ids(
        cls, module_content: str
    ) -> Set[PackageIdPrefix]:
        """
        Given a Python module file in form of string, extract all packages being imported.

        E.g. consider an AEA package Python module:

            import packages.open_aea.protocols.signing
            from packages.fetchai.connections.ledger.connection import LedgerConnection

        This function should return the set of package id prefixes:

            {('protocol', 'open_aea', 'signing'), ('connection', 'fetchai', 'ledger')}

        :param module_content: the content of the Python module to analyze.
        :return: the package ids corresponding to the import statements of AEA package modules
        """
        # find all import statements of the form:
        #
        #   from packages.{author}.{type_plural}.{name}
        #   import packages.{author}.{type_plural}.{name}
        #
        import_statements = re.findall(
            rf"^(    from|from|    import|import) ({PACKAGES}\.[A-Za-z0-9_]+\.{cls.package_type_plural_regex}\.[A-Za-z0-9_]+)",
            module_content,
            flags=re.MULTILINE,
        )

        # get all AEA package modules in form of import dotted path, excluding the prefix 'packages.'
        imported_packages_parts = set(
            tuple(package_dotted_path.split(".")[1:])
            for _from_or_import, package_dotted_path, _package_type in import_statements
        )

        # get the list of package ids extracted from the import dotted path
        # for part[0], need to remove the trailing 's' of component type plural, e.g. protocols -> protocol
        package_ids = set(
            (ComponentType(parts[1][:-1]), parts[0], parts[2])
            for parts in imported_packages_parts
        )

        return package_ids

    @classmethod
    def _find_all_used_packages(
        cls, configuration: ComponentConfiguration
    ) -> Dict[PackageIdPrefix, Set[Path]]:
        """
        Find all AEA packages used by some AEA package Python module.

        :param configuration: the configuration object of the AEA package
        :return: a dictionary from component id to a set of paths where some modules
                 of the component with that id are imported.
        """
        aea_package_root_dir = cast(Path, configuration.directory)
        package_id_prefix = (
            configuration.component_type,
            configuration.author,
            configuration.name,
        )

        used_packages: Dict[PackageIdPrefix, Set[Path]] = defaultdict(set)
        for python_module in aea_package_root_dir.rglob("*.py"):
            module_content = python_module.read_text()
            module_package_id_prefixes = cls._extract_imported_packages_as_ids(
                module_content
            )
            for module_package_id_prefix in module_package_id_prefixes:
                # only add to the result packages different from current package
                if module_package_id_prefix != package_id_prefix:
                    used_packages[module_package_id_prefix].add(python_module)
        return used_packages

    def run_check(self) -> None:
        """Run the check."""
        used_packages_to_module_paths = self._find_all_used_packages(self.configuration)
        dependencies = set(
            d.component_prefix for d in self.configuration.package_dependencies
        )
        used_packages = set(used_packages_to_module_paths.keys())

        used_packages_not_dependencies = used_packages - dependencies
        dependencies_not_used_packages = dependencies - used_packages

        if len(used_packages_not_dependencies) > 0:
            self._raise_used_packages_not_dependencies(
                used_packages_not_dependencies,
                used_packages_to_module_paths,
                self.configuration,
            )
        if len(dependencies_not_used_packages) > 0:
            self._raise_dependency_not_used_package(
                dependencies_not_used_packages, self.configuration
            )

    @classmethod
    def _raise_used_packages_not_dependencies(
        cls,
        used_packages_not_dependencies: Set[PackageIdPrefix],
        used_packages_to_module_paths: Dict[PackageIdPrefix, Set[Path]],
        configuration: ComponentConfiguration,
    ) -> None:
        """Raise AEAPackageLoadingError when some used package is not declared as dependency."""
        config_dir = cast(Path, configuration.directory)
        error_message = (
            f"found the following packages that are imported by some module but not declared as "
            f"dependencies of package {configuration.package_id}:\n\n"
        )
        for package_id_prefix in sorted(
            used_packages_not_dependencies, key=cls.package_id_prefix_to_str
        ):
            paths = used_packages_to_module_paths[package_id_prefix]
            paths_error_message = "\n".join(
                [indent(f"- {path.relative_to(config_dir)}", " " * 4) for path in paths]
            )
            prefix_to_str = cls.package_id_prefix_to_str(package_id_prefix)
            single_package_error_message = (
                f"- {prefix_to_str} used in:\n{paths_error_message}\n"
            )
            error_message += single_package_error_message
        raise AEAPackageLoadingError(error_message)

    @classmethod
    def _raise_dependency_not_used_package(
        cls,
        dependencies_not_used_packages: Set[PackageIdPrefix],
        configuration: ComponentConfiguration,
    ) -> None:
        """Raise AEAPackageLoadingError when some dependency is not used in any AEA package Python module."""
        raise AEAPackageLoadingError(
            f"The following dependencies are not used in any Python module of the package {configuration.package_id}:\n"
            + "\n".join(
                [
                    f"- {cls.package_id_prefix_to_str(package_id)}"
                    for package_id in sorted(
                        dependencies_not_used_packages, key=cls.package_id_prefix_to_str
                    )
                ]
            )
        )

    @classmethod
    def package_id_prefix_to_str(cls, package_id_prefix: PackageIdPrefix) -> str:
        """Get string from package id prefix."""
        component_type = str(package_id_prefix[0])
        author = package_id_prefix[1]
        name = package_id_prefix[2]
        return f"{component_type} {author}/{name}"


def perform_load_aea_package(
    dir_: Path, author: str, package_type_plural: str, package_name: str
) -> None:
    """
    Load the AEA package from values provided.

    It adds all the __init__.py modules into `sys.modules`.

    This function also checks that:
     - all packages declared as dependencies are used in package modules;
     - all imports correspond to a package declared as dependency.

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
        module = importlib.util.module_from_spec(cast(ModuleSpec, spec))
        sys.modules[import_path] = module
        _default_logger.debug(f"loading {import_path}: {module}")
        spec.loader.exec_module(module)  # type: ignore
