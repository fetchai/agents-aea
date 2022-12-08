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

"""Test package manager base."""


import re
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Optional
from typing import OrderedDict as OrderedDictType
from unittest import mock

import pytest

from aea.configurations.base import PackageConfiguration
from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import ComponentId, PackageId, PackageType, PublicId
from aea.package_manager.base import (
    BasePackageManager,
    ConfigLoaderCallableType,
    DepedencyMismatchErrors,
    PackageUpdateError,
    load_configuration,
)
from aea.test_tools.test_cases import BaseAEATestCase

from tests.conftest import ROOT_DIR


EXAMPLE_PACKAGE_ID = PackageId(
    package_type=PackageType.PROTOCOL,
    public_id=PublicId(author="open_aea", name="signing", version="1.0.0"),
)
DUMMY_PACKAGE_ID = PackageId(
    package_type=PackageType.SKILL,
    public_id=PublicId(author="dummy", name="name"),
)
EXAMPLE_PACKAGE_HASH = "bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo44"
DUMMY_PACKAGE_HASH = "bafybei0000000000000000000000000000000000000000000000000000"
PACKAGE_JSON_FILE = Path(ROOT_DIR, PACKAGES, "packages.json")


def _dummy_loader(
    package_type: PackageType, package_path: Path
) -> PackageConfiguration:
    """Dummy loader"""

    class _DummyPackageConfig(PackageConfiguration):
        """Dummy class."""

        @property
        def json(self) -> Dict:
            """JSON"""

            return {}

    return _DummyPackageConfig(name="name", author="author")


def _fetch_ipfs_mock(_, __, dest: str) -> None:
    """fetch_ipfs method mock."""
    Path(dest).mkdir()


class DummyPackageManager(BasePackageManager):
    """Dummy package manager."""

    def __init__(
        self,
        path: Path,
        packages: Dict[PackageId, str],
        config_loader: ConfigLoaderCallableType = load_configuration,
    ) -> None:
        """Package hashes."""

        self.path = path
        self.packages = packages
        self.config_loader = config_loader

    @classmethod
    def from_dir(
        cls,
        packages_dir: Path,
        config_loader: ConfigLoaderCallableType = load_configuration,
    ) -> "BasePackageManager":
        """Load from dir."""

        return cls(path=packages_dir, packages={}, config_loader=config_loader)

    def get_package_hash(self, package_id: PackageId) -> Optional[str]:
        """Return package hash."""

        return self.packages.get(package_id)

    @property
    def json(self) -> OrderedDictType:
        """Return json rep"""
        return OrderedDict(self.packages)

    def sync(
        self,
        dev: bool = False,
        third_party: bool = True,
        update_packages: bool = False,
        update_hashes: bool = False,
    ) -> "BasePackageManager":
        """Perorm sync."""

    def update_package_hashes(self) -> "BasePackageManager":
        """Update package hashes."""

    def verify(
        self,
    ) -> int:
        """Verify hashes."""


class TestBaseManager(BaseAEATestCase):
    """Test base implementation."""

    use_packages_dir: bool = True

    def test_initialization(
        self,
    ) -> None:
        """Test manager initialization."""
        packages = {EXAMPLE_PACKAGE_ID: EXAMPLE_PACKAGE_HASH}
        package_manager = DummyPackageManager(
            path=self.packages_dir_path,
            packages=packages,
        )

        assert len(package_manager.packages) == len(packages)
        assert package_manager.path == self.packages_dir_path

    def test_package_id_to_path(
        self,
    ) -> None:
        """Test package id to path method."""

        package_manager = DummyPackageManager(
            path=self.packages_dir_path,
            packages={},
        )

        assert package_manager.package_path_from_package_id(EXAMPLE_PACKAGE_ID) == Path(
            self.packages_dir_path,
            EXAMPLE_PACKAGE_ID.author,
            EXAMPLE_PACKAGE_ID.package_type.to_plural(),
            EXAMPLE_PACKAGE_ID.name,
        )

    def test_add_package(
        self,
    ) -> None:
        """Test add package method."""

        package_manager = DummyPackageManager(
            path=self.packages_dir_path,
            packages={},
        )
        dummy_package = PackageId(
            package_type=PackageType.SKILL,
            public_id=PublicId(author="dummy", name="skill"),
        )

        with mock.patch("aea.package_manager.base.fetch_ipfs", new=_fetch_ipfs_mock):
            package_manager.add_package(
                package_id=dummy_package,
            )

            assert (self.packages_dir_path / dummy_package.author).exists()
            assert (
                self.packages_dir_path
                / dummy_package.author
                / dummy_package.package_type.to_plural()
            ).exists()
            assert (
                self.packages_dir_path
                / dummy_package.author
                / dummy_package.package_type.to_plural()
                / dummy_package.name
            ).exists()

    def test_update_package_failure(
        self,
    ) -> None:
        """Test update package method."""

        package_manager = DummyPackageManager(
            path=self.packages_dir_path,
            packages={},
        )

        with mock.patch("shutil.rmtree", side_effect=OSError):
            with pytest.raises(
                PackageUpdateError,
                match=re.escape("Cannot update (protocol, open_aea/signing:1.0.0)"),
            ):
                package_manager.update_package(package_id=EXAMPLE_PACKAGE_ID)

    @pytest.mark.parametrize(
        argnames=("packages", "error_check"),
        argvalues=[
            ({}, DepedencyMismatchErrors.HASH_NOT_FOUND),
            (
                {EXAMPLE_PACKAGE_ID: "fake_hash"},
                DepedencyMismatchErrors.HASH_DOES_NOT_MATCH,
            ),
        ],
    )
    def test_check_dependencies_errors(
        self, packages: Dict, error_check: DepedencyMismatchErrors
    ) -> None:
        """Test check dependencies method."""

        package_manager = DummyPackageManager(
            path=self.packages_dir_path,
            packages=packages,
        )

        failed_checks = package_manager.check_dependencies(
            configuration=mock.MagicMock(
                package_dependencies=[
                    ComponentId(
                        component_type=str(PackageType.PROTOCOL),
                        public_id=PublicId(
                            author="open_aea",
                            name="signing",
                            version="1.0.0",
                            package_hash=EXAMPLE_PACKAGE_HASH,
                        ),
                    )
                ]
            )
        )

        assert len(failed_checks) == 1, failed_checks
        ((package_id, error_found),) = failed_checks

        assert package_id == EXAMPLE_PACKAGE_ID
        assert error_check == error_found

    def test_update_public_id_hash(
        self,
    ) -> None:
        """Test update public id hash method."""

        package_manager = DummyPackageManager(
            path=self.packages_dir_path,
            packages={EXAMPLE_PACKAGE_ID: DUMMY_PACKAGE_HASH},
        )

        updated_public_id = package_manager.update_public_id_hash(
            public_id_str=str(EXAMPLE_PACKAGE_ID.public_id),
            package_type=PackageType.PROTOCOL.value,
        )

        assert PublicId.from_str(updated_public_id).hash == DUMMY_PACKAGE_HASH

    def test_update_dependencies(
        self,
    ) -> None:
        """Test update public id hash method."""

        package_to_update = PackageId(
            package_type=PackageType.SKILL,
            public_id=PublicId.from_str("valory/some_skill"),
        )

        package_manager = DummyPackageManager(
            path=self.packages_dir_path,
            packages={
                EXAMPLE_PACKAGE_ID: DUMMY_PACKAGE_HASH,
                package_to_update: EXAMPLE_PACKAGE_HASH,
            },
        )

        with mock.patch(
            "aea.package_manager.base.load_yaml",
            return_value=[
                {
                    "skills": [
                        "valory/some_skill",
                    ]
                },
                None,
            ],
        ), mock.patch(
            "aea.package_manager.base.dump_yaml",
        ) as dump_patch:
            package_manager.update_dependencies(
                package_id=package_to_update,
            )

            dump_patch.assert_called_once_with(
                file_path=(
                    self.packages_dir_path
                    / package_to_update.author
                    / package_to_update.package_type.to_plural()
                    / package_to_update.name
                    / "skill.yaml"
                ),
                data={
                    "skills": [
                        str(package_to_update.public_id.with_hash(EXAMPLE_PACKAGE_HASH))
                    ]
                },
                extra_data=None,
            )
