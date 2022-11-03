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
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Callable, Optional, cast, Tuple
from typing import OrderedDict as OrderedDictType


from aea.configurations.base import PackageConfiguration
from aea.configurations.data_types import PackageId, PackageType
from aea.helpers.dependency_tree import DependencyTree
from aea.helpers.fingerprint import check_fingerprint
from aea.helpers.io import open_file
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.configurations.loader import load_configuration_object

try:
    from aea_cli_ipfs.registry import fetch_ipfs  # type: ignore

    IS_IPFS_PLUGIN_INSTALLED = True
except (ImportError, ModuleNotFoundError):
    IS_IPFS_PLUGIN_INSTALLED = False

PACKAGES_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "additionalProperties": False,
    "type": "object",
    "required": [
        "dev",
        "third_party",
    ],
    "properties": {
        "dev": {"type": "object"},
        "third_party": {"type": "object"},
    },
}

PACKAGES_FILE = "packages.json"


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


# TODO: utilise `WithLogger` class for logging
class PackageManager:
    """AEA package manager"""

    path: Path

    _third_party_packages: OrderedDictType[PackageId, str]
    _dev_packages: OrderedDictType[PackageId, str]

    def __init__(
        self,
        path: Path,
        dev_packages: Optional[OrderedDictType[PackageId, str]] = None,
        third_party_packages: Optional[OrderedDictType[PackageId, str]] = None,
    ) -> None:
        """Initialize object."""

        self.path = path
        self._packages_file = path / PACKAGES_FILE

        self._dev_packages = dev_packages or OrderedDict()
        self._third_party_packages = third_party_packages or OrderedDict()

        self._logger = logging.getLogger(name="PackageManager")
        self._logger.setLevel(logging.INFO)

    @property
    def dev_packages(
        self,
    ) -> OrderedDictType[PackageId, str]:
        """Returns mappings of package ids -> package hash"""

        return self._dev_packages

    @property
    def third_party_packages(
        self,
    ) -> OrderedDictType[PackageId, str]:
        """Returns mappings of package ids -> package hash"""

        return self._third_party_packages

    def _sync(
        self,
        packages: OrderedDictType[PackageId, str],
        update_packages: bool = False,
        update_hashes: bool = False,
    ) -> Tuple[bool, OrderedDictType[PackageId, str], OrderedDictType[PackageId, str]]:
        """
        Sync local packages to the remote registry.

        :param update_packages: Update packages if the calculated hash for a
                                package does not match the one in the packages.json.
        :param update_hashes: Update hashes in the packages.json if the calculated
                              hash for a package does not match the one in the
                              packages.json.
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

    def sync(
        self,
        dev: bool = False,
        third_party: bool = True,
        update_packages: bool = False,
        update_hashes: bool = False,
    ) -> "PackageManager":
        """Sync local packages to the remote registry."""

        if update_packages and update_hashes:
            raise ValueError(
                "Both `update_packages` and `update_hashes` cannot be set to `True`."
            )

        self._logger.info(f"Performing sync @ {self.path}")

        sync_needed = False

        if third_party:
            self._logger.info("Checking third party packages.")
            (
                sync_needed,
                hash_updates_third_party,
                package_updates_third_party,
            ) = self._sync(
                packages=self.third_party_packages,
                update_hashes=update_hashes,
                update_packages=update_packages,
            )

        if dev:
            self._logger.info("Checking dev packages.")
            sync_needed, hash_updates_dev, package_updates_dev = self._sync(
                packages=self.dev_packages,
                update_hashes=update_hashes,
                update_packages=update_packages,
            )

        if update_hashes:
            self._logger.info("Updating hashes")
            self._dev_packages = hash_updates_dev
            self._third_party_packages = hash_updates_third_party
            self.dump()

        if update_packages:
            self._logger.info("Updating packages.")
            for package_id, _ in package_updates_third_party.items():
                self._logger.info(f"Updating {package_id}")
                self.update_package(package_id=package_id)

        if sync_needed:
            self._logger.info("Sync complete")
        else:
            self._logger.info("No package was updated.")

        return self

    def add_package(self, package_id: PackageId) -> "PackageManager":
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

    def update_package(
        self,
        package_id: PackageId,
    ) -> "PackageManager":
        """Update package."""

        package_path = self.package_path_from_package_id(package_id=package_id)
        try:
            shutil.rmtree(str(package_path))
        except (OSError, PermissionError) as e:
            raise PackageUpdateError(f"Cannot update {package_id}") from e

        self.add_package(package_id)
        return self

    def get_available_package_hashes(
        self,
    ) -> OrderedDictType[PackageId, str]:
        """Returns a mapping object between available packages and their hashes"""

        _packages = OrderedDict()
        available_packages = DependencyTree.generate(self.path)
        for _level in available_packages:
            for package in _level:
                path = self.package_path_from_package_id(package)
                package_hash = IPFSHashOnly.get(str(path))
                _packages[package] = package_hash

        return _packages

    def update_package_hashes(self) -> "PackageManager":
        """Initialize package.json file."""
        for package_id, package_hash in self.get_available_package_hashes().items():
            is_dev_package = package_id in self._dev_packages
            is_third_party_package = package_id in self._third_party_packages
            if not is_dev_package and not is_third_party_package:
                raise PackageNotValid(
                    f"Found a package which is not listed in the `packages.json` with package id {package_id}"
                )

            if is_dev_package:
                if self._dev_packages[package_id] == package_hash:
                    continue

                self._logger.info(f"Updating hash for {package_id}")
                self._dev_packages[package_id] = package_hash

        return self

    def package_path_from_package_id(self, package_id: PackageId) -> Path:
        """Get package path from the package id."""
        return (
            self.path
            / package_id.author
            / package_id.package_type.to_plural()
            / package_id.name
        )

    def verify(
        self,
        config_loader: Callable[
            [PackageType, Path], PackageConfiguration
        ] = load_configuration,
    ) -> int:
        """Verify fingerprints and outer hash of all available packages."""

        failed = False
        try:
            available_packages = self.get_available_package_hashes()
            for package_id in available_packages:
                self._logger.info(f"Verifying {package_id}")
                package_path = self.package_path_from_package_id(package_id)
                configuration_obj = config_loader(
                    package_id.package_type,
                    package_path,
                )

                fingerprint_check = check_fingerprint(configuration_obj)
                if not fingerprint_check:
                    failed = True
                    self._logger.info(
                        f"Fingerprints does not match for {package_id} @ {package_path}"
                    )
                    continue

                expected_hash = self._dev_packages.get(
                    package_id, self._third_party_packages.get(package_id)
                )

                if expected_hash is None:
                    failed = True
                    self._logger.info(f"Cannot find hash for {package_id}")
                    continue

                calculated_hash = IPFSHashOnly.get(str(package_path))
                if calculated_hash != expected_hash:
                    failed = True
                    self._logger.info(f"Hash does not match for {package_id}")
                    self._logger.info(f"\tCalculated hash: {calculated_hash}")
                    self._logger.info(f"\tExpected hash: {expected_hash}")

        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()
            failed = True

        return int(failed)

    def dump(self, file: Optional[Path] = None) -> None:
        """Dump package data to file."""
        file = file or self._packages_file
        with open_file(file, "w+") as fp:
            json.dump(self.json, fp, indent=4)

    @property
    def json(
        self,
    ) -> OrderedDictType:
        """Json representation"""
        data = OrderedDict()
        data["dev"] = OrderedDict()
        data["third_party"] = OrderedDict()

        for package_id, package_hash in self._dev_packages.items():
            data["dev"][package_id.to_uri_path] = package_hash

        for package_id, package_hash in self._third_party_packages.items():
            data["third_party"][package_id.to_uri_path] = package_hash

        return data

    @classmethod
    def from_dir(cls, packages_dir: Path) -> "PackageManager":
        """Initialize from packages directory."""

        packages_file = packages_dir / PACKAGES_FILE
        with open_file(packages_file, "r") as fp:
            _packages = json.load(fp)

        packages = OrderedDict()

        dev_packages = OrderedDict()
        for package_id, package_hash in _packages["dev"].items():
            packages[PackageId.from_uri_path(package_id)] = package_hash

        third_party_packages = OrderedDict()
        for package_id, package_hash in _packages["third_party"].items():
            packages[PackageId.from_uri_path(package_id)] = package_hash

        return cls(packages_dir, packages)


class PackageHashDoesNotMatch(Exception):
    """Package hash does not match error."""


class PackageUpdateError(Exception):
    """Package update error."""


class PackageNotValid(Exception):
    """Package not valid."""
