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

"""Package manager."""


import json
import logging
import shutil
import sys
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Callable, Optional
from typing import OrderedDict as OrderedDictType

import click

from aea.cli.ipfs_hash import load_configuration
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.base import PackageConfiguration
from aea.configurations.data_types import PackageId, PackageType
from aea.helpers.dependency_tree import DependencyTree
from aea.helpers.fingerprint import check_fingerprint
from aea.helpers.io import open_file
from aea.helpers.ipfs.base import IPFSHashOnly


try:
    from aea_cli_ipfs.registry import fetch_ipfs  # type: ignore

    IS_IPFS_PLUGIN_INSTALLED = True
except (ImportError, ModuleNotFoundError):
    IS_IPFS_PLUGIN_INSTALLED = False

PACKAGES_FILE = "packages.json"


@click.group("packages")
@click.pass_context
def package_manager(
    click_context: click.Context,  # pylint: disable=unused-argument
) -> None:
    """Local package manager."""


@package_manager.command()
@pass_ctx
@click.option(
    "--update-packages",
    is_flag=True,
    help="Update packages if the calculated hash for a package does not match the one in the packages.json.",
)
@click.option(
    "--update-hashes",
    is_flag=True,
    help="Update hashes in the packages.json if the calculated hash for a package does not match the one in the packages.json",
)
def sync(ctx: Context, update_packages: bool, update_hashes: bool) -> None:
    """Sync local packages."""

    if not IS_IPFS_PLUGIN_INSTALLED:
        raise click.ClickException(
            "Please install ipfs plugin using `pip3 install open-aea-cli-ipfs`"
        )

    if update_hashes and update_packages:
        raise click.ClickException(
            "You cannot use both `--update-hashes` and `--update-packages` at the same time."
        )

    packages_dir = Path(ctx.registry_path)
    try:
        PackageManager.from_dir(packages_dir).sync(
            update_packages=update_packages,
            update_hashes=update_hashes,
        ).update_package_hashes().dump()
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@package_manager.command(name="lock")
@click.option(
    "--check",
    is_flag=True,
    help="Check packages.json",
)
@pass_ctx
def lock_packages(ctx: Context, check: bool) -> None:
    """Lock packages"""

    packages_dir = Path(ctx.registry_path)

    try:
        if check:
            packages_dir = Path(ctx.registry_path)
            click.echo("Verifying packages.json")
            return_code = PackageManager.from_dir(packages_dir).verify()

            if return_code:
                click.echo("Verification failed.")
            else:
                click.echo("Verification successful")

            sys.exit(return_code)

        PackageManager(packages_dir).update_package_hashes().dump()
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


class PackageManager:
    """AEA package manager"""

    path: Path
    _packages: OrderedDictType[PackageId, str]

    def __init__(
        self, path: Path, packages: Optional[OrderedDictType[PackageId, str]] = None
    ) -> None:
        """Initialize object."""

        self.path = path
        self._packages_file = path / PACKAGES_FILE
        self._packages = packages or OrderedDict()

        self._logger = logging.getLogger(name="PackageManager")
        self._logger.setLevel(logging.INFO)

    @property
    def packages(
        self,
    ) -> OrderedDictType[PackageId, str]:
        """Returns mappings of package ids -> package hash"""

        return self._packages

    def sync(
        self,
        update_packages: bool = False,
        update_hashes: bool = False,
    ) -> "PackageManager":
        """
        Sync local packages to the remote registry.

        :param update_packages: Update packages if the calculated hash for a
                                package does not match the one in the packages.json.
        :param update_hashes: Update hashes in the packages.json if the calculated
                              hash for a package does not match the one in the
                              packages.json.
        :return: PackageManager object
        """

        if update_packages and update_hashes:
            raise ValueError(
                "Both `update_packages` and `update_hashes` cannot be set to `True`."
            )

        self._logger.info(f"Performing sync @ {self.path}")
        sync_needed = False

        for package_id in self.packages:
            package_path = self.package_path_from_package_id(package_id)

            if package_path.exists():
                package_hash = IPFSHashOnly.get(str(package_path))
                expected_hash = self.packages[package_id]

                if package_hash == expected_hash:
                    continue

                if update_hashes:
                    self._logger.info(f"Updating hash for {package_id}")
                    self._packages[package_id] = package_hash
                    continue

                if update_packages:
                    sync_needed = True
                    self._logger.info(
                        f"Hash does not match for {package_id}, downloading package again..."
                    )
                    self.update_package(
                        package_path, package_id.with_hash(expected_hash)
                    )
                    continue

                raise PackageHashDoesNotMatch(
                    f"Hashes for {package_id} does not match; Calculated hash: {package_hash}; Expected hash: {expected_hash}"
                )

            sync_needed = True
            self._logger.info(f"{package_id} not found locally, downloading...")
            package_id_with_hash = package_id.with_hash(self.packages[package_id])
            self.add_package(package_id=package_id_with_hash)

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
        package_path: Path,
        package_id: PackageId,
    ) -> "PackageManager":
        """Update package."""

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
        self._logger.info("Updating hashes")
        self._packages.update(self.get_available_package_hashes())
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
                        f"\nHash does not match for {package_id}\n\tCalculated hash: {calculated_hash}\n\tExpected hash:{expected_hash}"
                    )

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
        for package_id, package_hash in self._packages.items():
            data[package_id.to_uri_path] = package_hash
        return data

    @classmethod
    def from_dir(cls, packages_dir: Path) -> "PackageManager":
        """Initialize from packages directory."""

        packages_file = packages_dir / PACKAGES_FILE
        with open_file(packages_file, "r") as fp:
            _packages = json.load(fp)

        packages = OrderedDict()
        for package_id, package_hash in _packages.items():
            packages[PackageId.from_uri_path(package_id)] = package_hash

        return cls(packages_dir, packages)


class PackageHashDoesNotMatch(Exception):
    """Package hash does not match error."""


class PackageUpdateError(Exception):
    """Package update error."""
