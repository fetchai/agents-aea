# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
import re
import shutil
import tempfile
from collections import OrderedDict
from pathlib import Path
from unittest import mock

import pytest

from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.package_manager.base import (
    DepedencyMismatchErrors,
    PackageFileNotValid,
    PackageHashDoesNotMatch,
    PackageNotValid,
)
from aea.package_manager.v1 import PackageManagerV1
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


TEST_SKILL_ID = PackageId(
    package_type=PackageType.SKILL,
    public_id=PublicId.from_str(
        "valory/abstract_round_abci:0.1.0:bafybeifh4qtjurq5637ykxexzexca5l4n6t4ujw26tpnern2swajanvhny"
    ),
)


class TestPackageManagerV1(BaseAEATestCase):
    """Test aea package manager."""

    use_packages_dir: bool = True
    packages_json_file: Path

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""

        super().setup_class()
        cls.packages_json_file = cls.t / PACKAGES / "packages.json"


class TestPackageManagerV1Initialization(TestPackageManagerV1):
    """Test object initialization."""

    def test_initialization(
        self,
    ) -> None:
        """Test object initialization."""

        pm = PackageManagerV1.from_dir(self.packages_dir_path)
        packages = json.loads(self.packages_json_file.read_text())

        assert len(pm.dev_packages) == len(packages["dev"])
        assert len(pm.third_party_packages) == len(packages["third_party"])

        assert pm.path == self.packages_dir_path
        assert pm.get_package_hash(package_id=EXAMPLE_PACKAGE_ID) is not None, packages
        assert pm.get_package_hash(package_id=DUMMY_PACKAGE_ID) is None

        # fails on bad file
        with mock.patch.object(
            PackageManagerV1, "_load_packages", return_value={"some": []}
        ):
            with pytest.raises(PackageFileNotValid):
                PackageManagerV1.from_dir(self.packages_dir_path)


class TestPackageManagerV1Sync(TestPackageManagerV1):
    """Test sync."""

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

        # test package already exists.
        with mock.patch.object(pm, "add_package") as update_patch, mock.patch(
            "pathlib.Path.exists", return_value=True
        ), mock.patch(
            "aea.helpers.ipfs.base.IPFSHashOnly.get", return_value=DUMMY_PACKAGE_HASH
        ):
            pm.sync(dev=True, third_party=False)
            update_patch.assert_not_called()

        # test package already exists but hash differs.
        with mock.patch.object(pm, "add_package") as add_patch, mock.patch(
            "pathlib.Path.exists", return_value=True
        ), mock.patch(
            "aea.helpers.ipfs.base.IPFSHashOnly.get",
            return_value=DUMMY_PACKAGE_HASH + "X",
        ):
            with pytest.raises(PackageHashDoesNotMatch):
                pm.sync(dev=True, third_party=False)
            add_patch.assert_not_called()

        # update hashes
        pm = PackageManagerV1(
            path=self.packages_dir_path,
            dev_packages=OrderedDict({DUMMY_PACKAGE_ID: DUMMY_PACKAGE_HASH}),
        )

        with mock.patch.object(pm, "add_package") as add_patch, mock.patch(
            "pathlib.Path.exists", return_value=True
        ), mock.patch(
            "aea.helpers.ipfs.base.IPFSHashOnly.get",
            return_value=DUMMY_PACKAGE_HASH + "X",
        ):
            pm.sync(dev=True, third_party=False, update_hashes=True)
            add_patch.assert_not_called()

        # update packages
        pm = PackageManagerV1(
            path=self.packages_dir_path,
            dev_packages=OrderedDict({DUMMY_PACKAGE_ID: DUMMY_PACKAGE_HASH}),
        )

        with mock.patch.object(pm, "add_package") as add_patch, mock.patch.object(
            pm, "_update_package"
        ) as update_patch, mock.patch(
            "pathlib.Path.exists", return_value=True
        ), mock.patch(
            "aea.helpers.ipfs.base.IPFSHashOnly.get",
            return_value=DUMMY_PACKAGE_HASH + "X",
        ):
            pm.sync(dev=True, third_party=False, update_packages=True)
            update_patch.assert_called_once()

        # third party
        pm = PackageManagerV1(
            path=self.packages_dir_path,
            third_party_packages=OrderedDict({DUMMY_PACKAGE_ID: DUMMY_PACKAGE_HASH}),
        )

        with mock.patch.object(pm, "add_package") as update_patch:
            pm.sync(dev=False, third_party=True)
            update_patch.assert_called_with(package_id=DUMMY_PACKAGE_ID)

        # 3d part hashes
        pm = PackageManagerV1(
            path=self.packages_dir_path,
            third_party_packages=OrderedDict({DUMMY_PACKAGE_ID: DUMMY_PACKAGE_HASH}),
        )

        with mock.patch.object(pm, "add_package") as update_patch:
            pm.sync(dev=False, third_party=True, update_hashes=True)
            update_patch.assert_called_with(package_id=DUMMY_PACKAGE_ID)

        # 3d part packages
        with mock.patch.object(pm, "update_package") as update_patch, mock.patch.object(
            pm,
            "_sync",
            return_value=[True, None, {DUMMY_PACKAGE_ID: DUMMY_PACKAGE_HASH}],
        ):
            pm.sync(dev=False, third_party=True, update_packages=True)
            update_patch.assert_called_with(package_id=DUMMY_PACKAGE_ID)


class TestPackageManagerV1UpdateFingerprint(TestPackageManagerV1):
    """Test update fingerprints."""

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
        package_hash = IPFSHashOnly.get(str(original_package))

        with tempfile.TemporaryDirectory() as temp_dir:
            packages_dir = Path(temp_dir, PACKAGES)
            temp_package = Path(temp_dir, *package_dir_rel.parts)

            os.makedirs(temp_package.parent)

            shutil.copytree(original_package, temp_package)
            pm = PackageManagerV1(
                path=packages_dir,
                dev_packages=OrderedDict({package_id: package_hash}),
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

        with mock.patch.object(
            pm,
            "iter_dependency_tree",
            return_value=[EXAMPLE_PACKAGE_ID],
        ), mock.patch.object(
            pm, "is_third_party_package", return_value=True
        ), mock.patch.object(
            pm, "is_dev_package", return_value=False
        ), mock.patch.object(
            pm,
            "calculate_hash_from_package_id",
            return_value=EXAMPLE_PACKAGE_HASH,
        ), mock.patch.object(
            pm._logger, "warning"
        ) as mock_warning:
            pm._third_party_packages[EXAMPLE_PACKAGE_ID] = EXAMPLE_PACKAGE_HASH
            pm.update_package_hashes()
            mock_warning.assert_not_called()

        with mock.patch.object(
            pm, "iter_dependency_tree", return_value=[TEST_SKILL_ID]
        ):
            with pytest.raises(
                PackageNotValid,
                match="Found a package which is not listed in the `packages.json`",
            ):
                pm.update_package_hashes()


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

        with caplog.at_level(logging.ERROR), mock.patch.object(
            pm,
            "check_dependencies",
            return_value=[
                (EXAMPLE_PACKAGE_ID, DepedencyMismatchErrors.HASH_NOT_FOUND),
                (EXAMPLE_PACKAGE_ID, DepedencyMismatchErrors.HASH_DOES_NOT_MATCH),
            ],
        ):
            assert pm.verify() == 1
            assert (
                "Package contains a dependency that is not defined in the"
                in caplog.text
            )
            assert "Dependency check failed\nHash does not match for" in caplog.text

        with mock.patch.object(
            pm, "check_dependencies", side_effect=ValueError("expected")
        ), mock.patch("traceback.print_exc") as print_tb_mock:
            assert pm.verify() == 1
            print_tb_mock.assert_called_once()

        # updating the `packages/open_aea/protocols/signing/__init__.py` file
        init_file = (
            pm.package_path_from_package_id(package_id=EXAMPLE_PACKAGE_ID)
            / INIT_FILE_NAME
        )
        init_file.write_text("")

        with caplog.at_level(logging.ERROR), mock.patch(
            "aea.package_manager.v1.check_fingerprint",
            return_value=True,
        ):
            pm = PackageManagerV1.from_dir(self.packages_dir_path)

            assert pm.verify() == 1
            assert f"Hash does not match for {EXAMPLE_PACKAGE_ID}" in caplog.text
            assert (
                f"Dependency check failed\nHash does not match for {EXAMPLE_PACKAGE_ID}"
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

        with mock.patch.object(
            pm,
            "_calculate_hash",
            return_value=DUMMY_PACKAGE_HASH,
        ), mock.patch.object(
            pm,
            "is_third_party_package",
            return_value=True,
        ):
            assert pm.verify() == 1
            assert pm._third_party_packages[EXAMPLE_PACKAGE_ID] == DUMMY_PACKAGE_HASH

        with caplog.at_level(logging.ERROR), mock.patch(
            "aea.package_manager.v1.check_fingerprint",
            return_value=False,
        ), mock.patch.object(
            pm,
            "iter_dependency_tree",
            return_value=[
                EXAMPLE_PACKAGE_ID,
            ],
        ), mock.patch.object(
            pm,
            "is_third_party_package",
            return_value=True,
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


@pytest.mark.integration
def test_package_manager_add_item_dependency_support():
    """Check PackageManager.add_packages works with dependencies on real packages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        package_manager = PackageManagerV1(Path(tmpdir))
        package_manager.add_package(TEST_SKILL_ID)
        assert len(package_manager.dev_packages) == 1
        package_manager.dump()

    with tempfile.TemporaryDirectory() as tmpdir:
        package_manager = PackageManagerV1(Path(tmpdir))
        package_manager.add_package(
            TEST_SKILL_ID,
            with_dependencies=True,
        )
        assert len(package_manager.dev_packages) > 1

        str_packages = str(package_manager.dev_packages)
        # check some  deps
        assert "protocol, valory/abci" in str_packages
        assert "skill, valory/abstract_round_abci" in str_packages
        assert "protocol, valory/tendermint" in str_packages
        package_manager.dump()


@mock.patch("aea.package_manager.base.fetch_ipfs")
def test_package_manager_add_item_dependency_support_mock(fetch_mock):
    """Check PackageManager.add_packages works with dependencies on mocks."""
    FAKE_PACKAGES = [
        PackageId(
            package_type=PackageType.SKILL,
            public_id=PublicId.from_str(
                f"valory/abstract_{i}:0.1.0:bafybeifh4qtjurq5637ykxexzexca5l4n6t4ujw26tpnern2swajanvhny"
            ),
        )
        for i in range(3)
    ]

    # no deps
    with tempfile.TemporaryDirectory() as tmpdir:
        package_manager = PackageManagerV1(Path(tmpdir))
        with mock.patch.object(package_manager, "calculate_hash_from_package_id"):
            package_manager.add_package(TEST_SKILL_ID)
            assert len(package_manager.dev_packages) == 1

    # deps loading
    with tempfile.TemporaryDirectory() as tmpdir:
        package_manager = PackageManagerV1(Path(tmpdir))
        with mock.patch.object(
            package_manager, "calculate_hash_from_package_id"
        ), mock.patch.object(
            package_manager,
            "get_package_dependencies",
            side_effect=[
                [FAKE_PACKAGES[0]],
                [FAKE_PACKAGES[1]],
                [FAKE_PACKAGES[2]],
                [],
                [],
                [],
                [],
            ],
        ):
            package_manager.add_package(
                TEST_SKILL_ID,
                with_dependencies=True,
            )
            assert len(package_manager.dev_packages) == 4


@mock.patch("aea.package_manager.base.fetch_ipfs")
def test_package_manager_add_package_already_installed(fetch_mock: mock.Mock):
    """Test package already installed."""
    # version already installed
    with tempfile.TemporaryDirectory() as tmpdir:
        package_manager = PackageManagerV1(Path(tmpdir))
        with mock.patch.object(
            package_manager, "get_package_version_with_hash", return_value=TEST_SKILL_ID
        ), mock.patch.object(
            package_manager, "is_package_files_exist", return_value=True
        ), mock.patch.object(
            package_manager, "calculate_hash_from_package_id"
        ):
            package_manager.add_package(TEST_SKILL_ID)
            fetch_mock.assert_not_called()


@mock.patch("aea.package_manager.base.fetch_ipfs")
def test_package_manager_add_package_can_be_updated(fetch_mock: mock.Mock):
    """Test package update on add_package."""
    # version already installed
    data = TEST_SKILL_ID.public_id.json
    data["version"] = "0.0.1"
    OLDER_VERSION = PackageId(
        package_type=TEST_SKILL_ID.package_type, public_id=PublicId.from_json(data)
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        package_manager = PackageManagerV1(Path(tmpdir))
        with mock.patch.object(
            package_manager, "get_package_version_with_hash", return_value=OLDER_VERSION
        ), mock.patch.object(
            package_manager, "is_package_files_exist", return_value=True
        ), mock.patch.object(
            package_manager, "calculate_hash_from_package_id"
        ), mock.patch.object(
            package_manager, "_remove_package_dir"
        ) as remove_mock:
            with pytest.raises(
                ValueError,
                match="Required package and package in the registry does not match",
            ):
                package_manager.add_package(TEST_SKILL_ID)
            fetch_mock.assert_not_called()

            package_manager.add_package(TEST_SKILL_ID, allow_update=True)
            remove_mock.assert_called_once_with(TEST_SKILL_ID)


class TestGetPackageDependencies(BaseAEATestCase):
    """Test test_get_package_dependencies."""

    HTTP_CONNECTION_PACKAGE = PackageId(
        package_type=PackageType.CONNECTION,
        public_id=PublicId(
            author="valory", name="http_client", version="1.0.0"
        ).to_latest(),
    )
    use_packages_dir: bool = True

    def test_get_package_dependencies(
        self,
    ) -> None:
        """Test get_package_dependencies method."""

        pm = PackageManagerV1.from_dir(self.t / self.packages_dir_path)
        assert "PackageId(protocol, valory/http" in str(
            pm.get_package_dependencies(self.HTTP_CONNECTION_PACKAGE)
        )


class TestGetPackageVersionWithHash(BaseAEATestCase):
    """Test get_package_version_with_hash."""

    HTTP_CONNECTION_PACKAGE = PackageId(
        package_type=PackageType.CONNECTION,
        public_id=PublicId(
            author="valory", name="http_client", version="1.0.0"
        ).to_latest(),
    )
    use_packages_dir: bool = True

    def test_get_package_version_with_hash(
        self,
    ) -> None:
        """Test get_package_dependencies method."""

        pm = PackageManagerV1.from_dir(self.t / self.packages_dir_path)
        package_id = pm.get_package_version_with_hash(self.HTTP_CONNECTION_PACKAGE)
        assert package_id.package_hash
