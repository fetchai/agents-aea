# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Base manager class."""


import json
import logging
import shutil
from abc import ABC, abstractmethod
from collections import OrderedDict
from enum import Enum
from pathlib import Path
from typing import Callable, Iterator, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Tuple, cast

from aea.configurations.base import PackageConfiguration
from aea.configurations.constants import AGENT, PACKAGE_TYPE_TO_CONFIG_FILE
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.configurations.loader import load_configuration_object
from aea.helpers.dependency_tree import DependencyTree, dump_yaml, load_yaml
from aea.helpers.io import open_file
from aea.helpers.ipfs.base import IPFSHashOnly


try:
    from aea_cli_ipfs.registry import fetch_ipfs  # type: ignore

    IS_IPFS_PLUGIN_INSTALLED = True
except (ImportError, ModuleNotFoundError):
    IS_IPFS_PLUGIN_INSTALLED = False

PACKAGES_FILE = "packages.json"

PackageIdToHashMapping = OrderedDictType[PackageId, str]


def load_configuration(
    package_type: PackageType, package_path: Path
) -> PackageConfiguration:
    """
    Load a configuration, knowing the type and the path to the package root.

    :param package_type: the package type.
    :param package_path: the path to the package root.
    :return: the configuration object.
    """
    configuration_obj = load_configuration_object(package_type, package_path)
    configuration_obj._directory = package_path  # pylint: disable=protected-access
    return cast(PackageConfiguration, configuration_obj)


class DepedencyMismatchErrors(Enum):
    """Dependency mismatch errors."""

    HASH_NOT_FOUND: int = 1
    HASH_DOES_NOT_MATCH: int = 2


class BasePackageManager(ABC):
    """AEA package manager"""

    path: Path

    def __init__(
        self,
        path: Path,
    ) -> None:
        """Initialize object."""

        self.path = path
        self._packages_file = path / PACKAGES_FILE

        self._logger = logging.getLogger(name="PackageManager")
        self._logger.setLevel(logging.INFO)

    def _sync(
        self,
        packages: PackageIdToHashMapping,
        update_packages: bool = False,
        update_hashes: bool = False,
    ) -> Tuple[bool, PackageIdToHashMapping, PackageIdToHashMapping]:
        """
        Sync local packages to the remote registry.

        :param packages: Packages to sync
        :param update_packages: Update packages if the calculated hash for a
                                package does not match the one in the packages.json.
        :param update_hashes: Update hashes in the packages.json if the calculated
                              hash for a package does not match the one in the
                              packages.json.
        :return: flag specifying if sync is needes, updates hashes, list of packages needs to be updates
        """

        sync_needed = False
        hash_updates = packages.copy()
        package_updates = OrderedDict()

        for package_id in packages:
            package_path = self.package_path_from_package_id(package_id)

            if package_path.exists():
                package_hash = IPFSHashOnly.get(str(package_path))
                expected_hash = packages[package_id]

                if package_hash == expected_hash:
                    continue

                if update_hashes:
                    hash_updates[package_id] = package_hash
                    continue

                if update_packages:
                    sync_needed = True
                    package_updates[package_id.with_hash(expected_hash)] = expected_hash
                    self._logger.info(
                        f"Hash does not match for {package_id}, downloading package again..."
                    )
                    continue

                raise PackageHashDoesNotMatch(
                    f"Hashes for {package_id} does not match; Calculated hash: {package_hash}; Expected hash: {expected_hash}"
                )

            sync_needed = True
            self._logger.info(f"{package_id} not found locally, downloading...")
            package_id_with_hash = package_id.with_hash(packages[package_id])
            self.add_package(package_id=package_id_with_hash)

        return sync_needed, hash_updates, package_updates

    def iter_dependency_tree(
        self,
    ) -> Iterator[PackageId]:
        """Iterate dependency tree."""
        for level in DependencyTree.generate(packages_dir=self.path):
            for package_id in level:
                yield package_id

    def check_dependencies(
        self,
        configuration: PackageConfiguration,
    ) -> List[Tuple[PackageId, DepedencyMismatchErrors]]:
        """Verify hashes for package dependecies againts the available hashes."""

        mismatches = []
        for component_id in configuration.package_dependencies:
            package_id = PackageId(
                package_type=str(component_id.component_type),
                public_id=component_id.public_id,
            )
            exppected_hash = self.get_package_hash(package_id)
            if exppected_hash is None:
                mismatches.append((package_id, DepedencyMismatchErrors.HASH_NOT_FOUND))
                continue

            if exppected_hash != package_id.package_hash:
                mismatches.append(
                    (package_id, DepedencyMismatchErrors.HASH_DOES_NOT_MATCH)
                )
        return mismatches

    def update_public_id_hash(
        self,
        public_id_str: str,
        package_type: str,
    ) -> str:
        """Update public id hash from the latest available hashes."""

        public_id_old = PublicId.from_str(public_id_str).without_hash()
        package_id = PackageId(package_type=package_type, public_id=public_id_old)
        package_hash = self.get_package_hash(package_id=package_id)
        return str(
            PublicId.from_json(
                {
                    **public_id_old.json,
                    "package_hash": package_hash,
                }
            )
        )

    def update_dependencies(
        self,
        package_id: PackageId,
    ) -> None:
        """Update dependency hashes to latest for a package."""

        package_path = self.package_path_from_package_id(
            package_id=package_id,
        )
        config_file = (
            package_path / PACKAGE_TYPE_TO_CONFIG_FILE[package_id.package_type.value]
        )
        package_config, extra = load_yaml(file_path=config_file)
        for component_type in PACKAGE_TYPE_TO_CONFIG_FILE:
            if component_type == AGENT:
                continue

            components = PackageType(component_type).to_plural()
            if components in package_config:
                package_config[components] = [
                    self.update_public_id_hash(
                        public_id_str=dependency, package_type=component_type
                    )
                    for dependency in package_config.get(components, [])
                ]

        dump_yaml(
            file_path=config_file,
            data=package_config,
            extra_data=extra,
        )

    def add_package(self, package_id: PackageId) -> "BasePackageManager":
        """Add packages."""

        author_repo = self.path / package_id.author
        if not author_repo.exists():
            author_repo.mkdir()
            (author_repo / "__init__.py").touch()

        package_type_collection = author_repo / package_id.package_type.to_plural()
        if not package_type_collection.exists():
            package_type_collection.mkdir()
            (package_type_collection / "__init__.py").touch()

        download_path = package_type_collection / package_id.name
        fetch_ipfs(
            str(package_id.package_type), package_id.public_id, dest=str(download_path)
        )

        return self

    def package_path_from_package_id(self, package_id: PackageId) -> Path:
        """Get package path from the package id."""
        return (
            self.path
            / package_id.author
            / package_id.package_type.to_plural()
            / package_id.name
        )

    def calculate_hash_from_package_id(self, package_id: PackageId) -> str:
        """Calculate package hash from package id."""

        package_path = self.package_path_from_package_id(package_id=package_id)
        return IPFSHashOnly.get(file_path=str(package_path))

    def update_package(
        self,
        package_id: PackageId,
    ) -> "BasePackageManager":
        """Update package."""

        package_path = self.package_path_from_package_id(package_id=package_id)
        try:
            shutil.rmtree(str(package_path))
        except (OSError, PermissionError) as e:
            raise PackageUpdateError(f"Cannot update {package_id}") from e

        self.add_package(package_id)
        return self

    @abstractmethod
    def get_package_hash(self, package_id: PackageId) -> Optional[str]:
        """Return hash for the given package id."""

    @abstractmethod
    def sync(
        self,
        dev: bool = False,
        third_party: bool = True,
        update_packages: bool = False,
        update_hashes: bool = False,
    ) -> "BasePackageManager":
        """Sync local packages to the remote registry."""

    @abstractmethod
    def update_package_hashes(self) -> "BasePackageManager":
        """Update package.json file."""

    @abstractmethod
    def verify(
        self,
        config_loader: Callable[
            [PackageType, Path], PackageConfiguration
        ] = load_configuration,
    ) -> int:
        """Verify fingerprints and outer hash of all available packages."""

    @property
    @abstractmethod
    def json(
        self,
    ) -> OrderedDictType:
        """Json representation"""

    def dump(self, file: Optional[Path] = None) -> None:
        """Dump package data to file."""
        file = file or self._packages_file
        with open_file(file, "w+") as fp:
            json.dump(self.json, fp, indent=4)

    @classmethod
    @abstractmethod
    def from_dir(cls, packages_dir: Path) -> "BasePackageManager":
        """Initialize from packages directory."""


class PackageHashDoesNotMatch(Exception):
    """Package hash does not match error."""


class PackageUpdateError(Exception):
    """Package update error."""


class PackageNotValid(Exception):
    """Package not valid."""


class PackageFileNotValid(Exception):
    """Package file not valid."""