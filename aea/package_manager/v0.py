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

"""Package manager V0"""

import json
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Callable
from typing import OrderedDict as OrderedDictType

from aea.configurations.base import PackageConfiguration
from aea.configurations.data_types import PackageId, PackageType
from aea.helpers.fingerprint import check_fingerprint
from aea.helpers.io import open_file
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.package_manager.base import (
    BasePackageManager,
    PACKAGES_FILE,
    PackageIdToHashMapping,
    load_configuration,
)


class PackageManagerV0(BasePackageManager):
    """Package manager v0."""

    _packages: OrderedDictType[PackageId, str]

    def __init__(self, path: Path, packages: PackageIdToHashMapping) -> None:
        """Initialize object."""

        super().__init__(path)

        self._packages = packages or OrderedDict()

    @property
    def packages(
        self,
    ) -> OrderedDictType[PackageId, str]:
        """Returns mappings of package ids -> package hash"""

        return self._packages

    def sync(
        self,
        dev: bool = False,
        third_party: bool = True,
        update_packages: bool = False,
        update_hashes: bool = False,
    ) -> "PackageManagerV0":
        """Sync local packages to the remote registry."""

        if update_packages and update_hashes:
            raise ValueError(
                "Both `update_packages` and `update_hashes` cannot be set to `True`."
            )

        self._logger.info(f"Performing sync @ {self.path}")
        sync_needed, hash_updates, package_updates = self._sync(
            packages=self.packages,
            update_hashes=update_hashes,
            update_packages=update_packages,
        )

        if update_hashes:
            self._packages = hash_updates

        if update_packages and package_updates:
            self._logger.info("Updating dev packages.")
            for package_id, _ in package_updates.items():
                self._logger.info(f"Updating {package_id}")
                self.update_package(package_id=package_id)

        if sync_needed:
            self._logger.info("Sync complete")
        else:
            self._logger.info("No package was updated.")

        return self

    def update_package_hashes(self) -> "PackageManagerV0":
        """Update packages.json file."""
        self._packages.update(self.get_available_package_hashes())
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

                expected_hash = self.packages.get(package_id)
                if expected_hash is None:
                    failed = True
                    self._logger.info(f"Cannot find hash for {package_id}")
                    continue

                calculated_hash = IPFSHashOnly.get(str(package_path))
                if calculated_hash != expected_hash:
                    failed = True
                    self._logger.info(
                        f"\nHash does not match for {package_id}\n\tCalculated hash: {calculated_hash}\n\tExpected hash: {expected_hash}"
                    )

        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()
            failed = True

        return int(failed)

    @property
    def json(
        self,
    ) -> OrderedDictType:
        """Json representation."""
        data = OrderedDict()
        for package_id, package_hash in self._packages.items():
            data[package_id.to_uri_path] = package_hash
        return data

    @classmethod
    def from_dir(cls, packages_dir: Path) -> "PackageManagerV0":
        """Initialize from packages directory."""

        packages_file = packages_dir / PACKAGES_FILE
        with open_file(packages_file, "r") as fp:
            _packages = json.load(fp)

        packages = OrderedDict()
        for package_id, package_hash in _packages.items():
            packages[PackageId.from_uri_path(package_id)] = package_hash

        return cls(packages_dir, packages)
