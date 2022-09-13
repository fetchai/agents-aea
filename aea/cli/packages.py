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
from collections import OrderedDict
from pathlib import Path
from typing import Optional
from typing import OrderedDict as OrderedDictType

import click

from aea.cli.utils.click_utils import component_flag
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.data_types import PackageId, PublicId
from aea.helpers.dependency_tree import DependencyTree
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
def sync(ctx: Context) -> None:
    """Sync local packages."""

    if not IS_IPFS_PLUGIN_INSTALLED:
        raise click.ClickException(
            "Please install ipfs plugin using `pip3 install open-aea-cli-ipfs`"
        )

    packages_dir = Path(ctx.registry_path)
    manager = PackageManager.from_dir(packages_dir)
    manager.sync()


@package_manager.command()
@pass_ctx
def init(ctx: Context) -> None:
    """Initialize packages.json"""

    packages_dir = Path(ctx.registry_path)
    PackageManager(packages_dir).init()


@package_manager.command()
@pass_ctx
@component_flag(wrap_public_id=True)
def add(ctx: Context, public_id: PublicId, component_type: str) -> None:
    """Add a package."""

    packages_dir = Path(ctx.registry_path)
    PackageManager.from_dir(packages_dir)
    click.echo((component_type, public_id))


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

    def sync(
        self,
    ) -> None:
        """Sync local packages to the remote registry."""

        for package_id in self._packages:
            package_path = (
                self.path
                / package_id.author
                / package_id.package_type.to_plural()
                / package_id.name
            )

            if package_path.exists():
                continue

            print(f"{package_id} not found locally, downloading...")
            package_id_with_hash = package_id.with_hash(self._packages[package_id])
            self.add(package_id=package_id_with_hash)
        print("Sync complete.")

        print("Updating packages.json")
        self.init()

    def add(self, package_id: PackageId) -> None:
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

    def init(self, download_missing: bool = False) -> None:
        """Initialize package.json file."""

        available_packages = DependencyTree.generate(self.path)
        self._packages = OrderedDict()
        for _level in available_packages:
            for package in _level:
                path = (
                    self.path
                    / package.author
                    / package.package_type.to_plural()
                    / package.name
                )
                if not path.exists() and not download_missing:
                    raise DependencyNotFound(f"Missing dependency; {package}")
                package_hash = IPFSHashOnly.get(str(path))
                self._packages[package] = package_hash

        self.dump()

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


class DependencyNotFound(Exception):
    """Dependency not found error."""
