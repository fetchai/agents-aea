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

"""Package manager V1"""

import json
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Callable, Optional
from typing import OrderedDict as OrderedDictType

from aea.configurations.base import PackageConfiguration
from aea.configurations.data_types import PackageId, PackageType
from aea.helpers.fingerprint import check_fingerprint
from aea.helpers.io import open_file
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.package_manager.base import (
    BasePackageManager,
    PACKAGES_FILE,
    PackageFileNotValid,
    PackageIdToHashMapping,
    PackageNotValid,
    load_configuration,
)


class PackageManagerV1(BasePackageManager):
    """Package manager V1"""

    _third_party_packages: PackageIdToHashMapping
    _dev_packages: PackageIdToHashMapping

    def __init__(
        self,
        path: Path,
        dev_packages: Optional[PackageIdToHashMapping] = None,
        third_party_packages: Optional[PackageIdToHashMapping] = None,
    ) -> None:
        """Initialize object."""

        super().__init__(path)

        self._dev_packages = dev_packages or OrderedDict()
        self._third_party_packages = third_party_packages or OrderedDict()

    @property
    def dev_packages(
        self,
    ) -> PackageIdToHashMapping:
        """Returns mappings of package ids -> package hash"""

        return self._dev_packages

    @property
    def third_party_packages(
        self,
    ) -> PackageIdToHashMapping:
        """Returns mappings of package ids -> package hash"""

        return self._third_party_packages

    def sync(
        self,
        dev: bool = False,
        third_party: bool = True,
        update_packages: bool = False,
        update_hashes: bool = False,
    ) -> "PackageManagerV1":
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
                _sync_needed,
                hash_updates_third_party,
                package_updates_third_party,
            ) = self._sync(
                packages=self.third_party_packages,
                update_hashes=update_hashes,
                update_packages=update_packages,
            )
            sync_needed = sync_needed or _sync_needed

            if update_hashes and hash_updates_third_party:
                third_party_package_id = "\n\t- ".join(
                    map(str, hash_updates_third_party)
                )
                self._logger.warning(
                    f"Hashes for follwing third party module has changed.\n\t- {third_party_package_id}"
                )

            if update_packages and package_updates_third_party:
                self._logger.info("Updating third party packages.")
                for package_id, _ in package_updates_third_party.items():
                    self._logger.info(f"Updating {package_id}")
                    self.update_package(package_id=package_id)

        if dev:
            self._logger.info("Checking dev packages.")
            _sync_needed, hash_updates_dev, package_updates_dev = self._sync(
                packages=self.dev_packages,
                update_hashes=update_hashes,
                update_packages=update_packages,
            )
            sync_needed = sync_needed or _sync_needed

            if update_hashes:
                self._dev_packages = hash_updates_dev

            if update_packages and package_updates_dev:
                self._logger.info("Updating dev packages.")
                for package_id, _ in package_updates_dev.items():
                    self._logger.info(f"Updating {package_id}")
                    self.update_package(package_id=package_id)

        if update_hashes:
            self._logger.info("Updating hashes")
            self.dump()

        if sync_needed:
            self._logger.info("Sync complete")
        else:
            self._logger.info("No package was updated.")

        return self

    def update_package_hashes(self) -> "PackageManagerV1":
        """Update package.json file."""
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

                expected_hash = self.dev_packages.get(
                    package_id, self.third_party_packages.get(package_id)
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

    @property
    def json(
        self,
    ) -> OrderedDictType:
        """Json representation"""

        data: OrderedDictType[str, OrderedDictType[str, str]] = OrderedDict()
        data["dev"] = OrderedDict()
        data["third_party"] = OrderedDict()

        for package_id, package_hash in self._dev_packages.items():
            data["dev"][package_id.to_uri_path] = package_hash

        for package_id, package_hash in self._third_party_packages.items():
            data["third_party"][package_id.to_uri_path] = package_hash

        return data

    @classmethod
    def from_dir(cls, packages_dir: Path) -> "PackageManagerV1":
        """Initialize from packages directory."""

        packages_file = packages_dir / PACKAGES_FILE
        with open_file(packages_file, "r") as fp:
            _packages = json.load(fp)

        if "dev" not in _packages or "third_party" not in _packages:
            raise PackageFileNotValid("Package file not valid.")

        dev_packages = OrderedDict()
        for package_id, package_hash in _packages["dev"].items():
            dev_packages[PackageId.from_uri_path(package_id)] = package_hash

        third_party_packages = OrderedDict()
        for package_id, package_hash in _packages["third_party"].items():
            third_party_packages[PackageId.from_uri_path(package_id)] = package_hash

        return cls(packages_dir, dev_packages, third_party_packages)
