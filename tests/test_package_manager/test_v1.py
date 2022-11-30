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
import re
from collections import OrderedDict
from pathlib import Path
from unittest import mock

import pytest

from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.package_manager.v1 import PackageManagerV1
from aea.test_tools.test_cases import BaseAEATestCase

from tests.conftest import ROOT_DIR


SENTINAL = object()
EXAMPLE_PACKAGE_ID = PackageId(
    package_type=PackageType.PROTOCOL,
    public_id=PublicId(author="open_aea", name="signing", version="1.0.0"),
)
DUMMY_PACKAGE_ID = PackageId(
    package_type=PackageType.SKILL,
    public_id=PublicId(author="dummy", name="name"),
)
EXAMPLE_PACKAGE_HASH = "bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo44"
PACKAGE_JSON_FILE = Path(ROOT_DIR, PACKAGES, "packages.json")
DUMMY_PACKAGE_HASH = "bafybei0000000000000000000000000000000000000000000000000000"


class TestPackageManagerV1(BaseAEATestCase):
    """Test aea package manager."""

    use_packages_dir: bool = True
    packages_json_file: Path

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""

        super().setup_class()
        cls.packages_json_file = cls.t / PACKAGES / "packages.json"

    def test_initialization(
        self,
    ) -> None:
        """Test object initialization."""

        pm = PackageManagerV1.from_dir(self.packages_dir_path)
        packages = json.loads(self.packages_json_file.read_text())

        assert len(pm.dev_packages) == len(packages["dev"])
        assert len(pm.third_party_packages) == len(packages["third_party"])

        assert pm.path == self.packages_dir_path
        assert pm.get_package_hash(package_id=EXAMPLE_PACKAGE_ID) is not None
        assert pm.get_package_hash(package_id=DUMMY_PACKAGE_ID) is None

    def test_sync(
        self,
    ) -> None:
        """Test sync."""

        pm = PackageManagerV1(
            path=self.packages_dir_path,
            dev_packages=OrderedDict({DUMMY_PACKAGE_ID: DUMMY_PACKAGE_HASH}),
        )

        with pytest.raises(
            ValueError,
            match=re.escape(
                "Both `update_packages` and `update_hashes` cannot be set to `True`."
            ),
        ):
            pm.sync(update_hashes=True, update_packages=True)

        with mock.patch.object(pm, "add_package") as update_patch:
            pm.sync(dev=True, third_party=False)
            update_patch.assert_called_with(package_id=DUMMY_PACKAGE_ID)

        pm = PackageManagerV1(
            path=self.packages_dir_path,
            third_party_packages=OrderedDict({DUMMY_PACKAGE_ID: DUMMY_PACKAGE_HASH}),
        )

        with mock.patch.object(pm, "add_package") as update_patch:
            pm.sync(dev=False, third_party=True)
            update_patch.assert_called_with(package_id=DUMMY_PACKAGE_ID)


class TestHashUpdateDev(BaseAEATestCase):
    """Test hash update."""

    use_packages_dir: bool = True

    def test_update_package_hashes(
        self,
    ) -> None:
        """Test update package hash method."""

        packages_v1 = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))

        original_hash = packages_v1["dev"][EXAMPLE_PACKAGE_ID.to_uri_path]
        packages_v1["dev"][EXAMPLE_PACKAGE_ID.to_uri_path] = DUMMY_PACKAGE_HASH

        packages_json_file = self.packages_dir_path / "packages.json"
        packages_json_file.write_text(json.dumps(obj=packages_v1))
        pm = PackageManagerV1.from_dir(self.packages_dir_path)

        pm.update_package_hashes().dump()

        packages_v1_updated = json.loads(packages_json_file.read_text(encoding="utf-8"))

        assert pm.dev_packages[EXAMPLE_PACKAGE_ID] == original_hash
        assert (
            packages_v1_updated["dev"][EXAMPLE_PACKAGE_ID.to_uri_path] == original_hash
        )


class TestHashUpdateThirdParty(BaseAEATestCase):
    """Test hash update."""

    use_packages_dir: bool = True

    def test_update_package_hashes(self, caplog) -> None:
        """Test update package hash method."""

        packages_v1 = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))
        original_hash = packages_v1["dev"].pop(EXAMPLE_PACKAGE_ID.to_uri_path)
        packages_v1["third_party"][EXAMPLE_PACKAGE_ID.to_uri_path] = DUMMY_PACKAGE_HASH

        packages_json_file = self.packages_dir_path / "packages.json"
        packages_json_file.write_text(json.dumps(obj=packages_v1))
        pm = PackageManagerV1.from_dir(self.packages_dir_path)

        with caplog.at_level(logging.WARNING):
            pm.update_package_hashes().dump()
            packages_v1_updated = json.loads(
                packages_json_file.read_text(encoding="utf-8")
            )

            assert pm.third_party_packages[EXAMPLE_PACKAGE_ID] == original_hash
            assert (
                packages_v1_updated["third_party"][EXAMPLE_PACKAGE_ID.to_uri_path]
                == original_hash
            )
            assert "Hash change detected for third party package" in caplog.text


class TestVerifyFailure(BaseAEATestCase):
    """Test verify method."""

    use_packages_dir: bool = True

    def test_verify_method(self, caplog) -> None:
        """Test update package hash method."""

        pm = PackageManagerV1.from_dir(self.packages_dir_path)
        assert pm.verify() == 0

        packages_v1 = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))
        packages_json_file = self.packages_dir_path / "packages.json"

        packages_v1["dev"][EXAMPLE_PACKAGE_ID.to_uri_path] = DUMMY_PACKAGE_HASH
        packages_json_file.write_text(json.dumps(obj=packages_v1))

        with caplog.at_level(logging.ERROR):
            pm = PackageManagerV1.from_dir(self.packages_dir_path)

            assert pm.verify() == 1
            assert f"Hash does not match for {EXAMPLE_PACKAGE_ID}" in caplog.text
            assert (
                f"Dependency check failed; Hash does not match for {EXAMPLE_PACKAGE_ID}"
                in caplog.text
            )

    def test_fingerprint_failure(self, caplog) -> None:
        """Test update package hash method."""

        pm = PackageManagerV1(
            path=self.packages_dir_path,
            dev_packages=OrderedDict(
                {
                    EXAMPLE_PACKAGE_ID: EXAMPLE_PACKAGE_HASH,
                }
            ),
        )

        with caplog.at_level(logging.ERROR), mock.patch(
            "aea.package_manager.v1.check_fingerprint",
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

        pm = PackageManagerV1(path=self.packages_dir_path)

        with caplog.at_level(logging.ERROR), mock.patch(
            "aea.package_manager.v1.check_fingerprint",
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
