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


import json
import logging
import os
import shutil
import tempfile
from collections import OrderedDict
from pathlib import Path
from unittest import mock

from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PackageId
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.package_manager.v0 import PackageManagerV0
from aea.protocols.generator.common import INIT_FILE_NAME
from aea.test_tools.test_cases import BaseAEATestCase

from tests.conftest import ROOT_DIR
from tests.test_package_manager.test_base import (
    DUMMY_PACKAGE_HASH,
    DUMMY_PACKAGE_ID,
    EXAMPLE_PACKAGE_HASH,
    EXAMPLE_PACKAGE_ID,
    PACKAGE_JSON_FILE,
)


class TestPackageManagerV0(BaseAEATestCase):
    """Test aea package manager."""

    use_packages_dir: bool = True
    packages_json_file: Path

    def setup(
        self,
    ) -> None:
        """Setup test."""

        # the current `packages.json` in `packages/` directory follows the v1
        # format so we will have to load it and convert it to v0 format
        packages_v1 = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))

        self.packages_json_file = self.packages_dir_path / "packages.json"
        self.packages_json_file.write_text(
            json.dumps({**packages_v1["dev"], **packages_v1["third_party"]})
        )

    def test_initialization(
        self,
    ) -> None:
        """Test object initialization."""

        pm = PackageManagerV0.from_dir(self.packages_dir_path)

        assert len(pm.packages) == len(json.loads(self.packages_json_file.read_text()))
        assert pm.path == self.packages_dir_path
        assert pm.get_package_hash(package_id=EXAMPLE_PACKAGE_ID) is not None
        assert pm.get_package_hash(package_id=DUMMY_PACKAGE_ID) is None

    def test_sync(
        self,
    ) -> None:
        """Test sync."""

        pm = PackageManagerV0(
            path=self.packages_dir_path,
            packages=OrderedDict({DUMMY_PACKAGE_ID: DUMMY_PACKAGE_HASH}),
        )

        with mock.patch.object(pm, "add_package") as update_patch:
            pm.sync()
            update_patch.assert_called_with(package_id=DUMMY_PACKAGE_ID)

    def test_update_fingerprints(self, caplog) -> None:
        """Test update fingerprints."""

        package_id = PackageId.from_uri_path("protocol/open_aea/signing/1.0.0")
        package_dir_rel = Path(
            PACKAGES,
            package_id.author,
            package_id.package_type.to_plural(),
            package_id.name,
        )
        original_package = ROOT_DIR / package_dir_rel
        package_hash = IPFSHashOnly.get(original_package)

        with tempfile.TemporaryDirectory() as temp_dir:
            packages_dir = Path(temp_dir, PACKAGES)
            temp_package = Path(temp_dir, *package_dir_rel.parts)

            os.makedirs(temp_package.parent)

            shutil.copytree(original_package, temp_package)
            pm = PackageManagerV0(
                path=packages_dir, packages={package_id: package_hash}
            )

            (temp_package / "__init__.py").write_text("")

            with caplog.at_level(logging.ERROR):
                assert pm.verify() == 1
                assert (
                    "Fingerprints does not match for (protocol, open_aea/signing:1.0.0)"
                    in caplog.text
                )

            pm.update_package_hashes()
            assert pm.verify() == 0


class TestHashUpdate(BaseAEATestCase):
    """Test hash update."""

    use_packages_dir: bool = True

    def test_update_package_hashes(
        self,
    ) -> None:
        """Test update package hash method."""

        packages_v1 = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))
        packages = {**packages_v1["dev"], **packages_v1["third_party"]}

        original_hash = packages[EXAMPLE_PACKAGE_ID.to_uri_path]
        packages[EXAMPLE_PACKAGE_ID.to_uri_path] = DUMMY_PACKAGE_HASH

        packages_json_file = self.packages_dir_path / "packages.json"
        packages_json_file.write_text(json.dumps(obj=packages))
        pm = PackageManagerV0.from_dir(self.packages_dir_path)

        pm.update_package_hashes().dump()

        packages_v1_updated = json.loads(packages_json_file.read_text(encoding="utf-8"))

        assert pm.get_package_hash(EXAMPLE_PACKAGE_ID) == original_hash
        assert packages_v1_updated[EXAMPLE_PACKAGE_ID.to_uri_path] == original_hash


class TestVerifyFailure(BaseAEATestCase):
    """Test verify method."""

    use_packages_dir: bool = True

    def test_verify_method(self, caplog) -> None:
        """Test update package hash method."""

        packages_v1 = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))
        packages = {**packages_v1["dev"], **packages_v1["third_party"]}

        packages_json_file = self.packages_dir_path / "packages.json"
        packages_json_file.write_text(json.dumps(obj=packages))

        pm = PackageManagerV0.from_dir(self.packages_dir_path)
        assert pm.verify() == 0

        # updating the `packages/open_aea/protocols/signing/__init__.py` file
        init_file = (
            pm.package_path_from_package_id(package_id=EXAMPLE_PACKAGE_ID)
            / INIT_FILE_NAME
        )
        init_file.write_text("")

        with caplog.at_level(logging.ERROR), mock.patch(
            "aea.package_manager.v0.check_fingerprint",
            return_value=True,
        ):
            pm = PackageManagerV0.from_dir(self.packages_dir_path)

            assert pm.verify() == 1
            assert f"Hash does not match for {EXAMPLE_PACKAGE_ID}" in caplog.text
            assert (
                f"Dependency check failed\nHash does not match for {EXAMPLE_PACKAGE_ID}"
                in caplog.text
            )

    def test_fingerprint_failure(self, caplog) -> None:
        """Test update package hash method."""

        pm = PackageManagerV0(
            path=self.packages_dir_path,
            packages=OrderedDict(
                {
                    EXAMPLE_PACKAGE_ID: EXAMPLE_PACKAGE_HASH,
                }
            ),
        )

        with caplog.at_level(logging.ERROR), mock.patch(
            "aea.package_manager.v0.check_fingerprint",
            return_value=False,
        ), mock.patch.object(
            pm,
            "iter_dependency_tree",
            return_value=[
                EXAMPLE_PACKAGE_ID,
            ],
        ):

            assert pm.verify() == 1
            assert (
                f"Fingerprints does not match for {EXAMPLE_PACKAGE_ID}" in caplog.text
            )

    def test_missing_hash(self, caplog) -> None:
        """Test update package hash method."""

        pm = PackageManagerV0(path=self.packages_dir_path, packages=OrderedDict())

        with caplog.at_level(logging.ERROR), mock.patch(
            "aea.package_manager.v0.check_fingerprint",
            return_value=True,
        ), mock.patch.object(
            pm,
            "iter_dependency_tree",
            return_value=[
                EXAMPLE_PACKAGE_ID,
            ],
        ):

            assert pm.verify() == 1
            assert f"Cannot find hash for {EXAMPLE_PACKAGE_ID}" in caplog.text
