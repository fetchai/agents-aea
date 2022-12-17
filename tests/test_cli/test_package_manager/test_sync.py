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

"""Test `aea packages sync` command."""


import json
import logging
import re
from unittest import mock

import click
import pytest

from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PackageId
from aea.package_manager.base import PACKAGES_FILE
from aea.package_manager.v1 import PackageManagerV1
from aea.test_tools.test_cases import BaseAEATestCase


@mock.patch("aea.package_manager.base.fetch_ipfs")
@mock.patch(
    "aea.package_manager.base.BasePackageManager.calculate_hash_from_package_id"
)
class TestSyncCommand(BaseAEATestCase):
    """Test sync command."""

    def test_sync_normal(self, ipfs_mock, hash_mock, caplog) -> None:
        """Test sync command."""

        with caplog.at_level(logging.INFO):
            result = self.run_cli_command("packages", "sync")
            assert result.exit_code == 0
            assert "No package was updated." in caplog.text

    def test_sync_with_missing_dev_packages(self, ipfs_mock, hash_mock, caplog) -> None:
        """Test sync with missing packages."""

        packages_file = self.t / PACKAGES / PACKAGES_FILE
        packages = dict(
            map(
                lambda x: (PackageId.from_uri_path(x[0]), x[1]),
                json.loads(packages_file.read_text())["dev"].items(),
            )
        )
        packages[
            PackageId.from_uri_path("skill/author/some_skill/0.1.0")
        ] = "bafybeidv77u2xl52mnxakwvh7fuh46aiwfpteyof4eaptfd4agoi6cdblb"

        with mock.patch.object(
            PackageManagerV1, "dev_packages", new=packages
        ), caplog.at_level(logging.INFO):
            result = self.run_cli_command("packages", "sync", "--dev")
            assert result.exit_code == 0
            assert (
                "(skill, author/some_skill:0.1.0) not found locally, downloading..."
                in caplog.text
            )

    def test_sync_with_missing_third_party_packages(
        self, ipfs_mock, hash_mock, caplog
    ) -> None:
        """Test sync with missing packages."""

        packages = {
            PackageId.from_uri_path(
                "skill/author/some_skill/0.1.0"
            ): "bafybeidv77u2xl52mnxakwvh7fuh46aiwfpteyof4eaptfd4agoi6cdblb"
        }

        with mock.patch.object(
            PackageManagerV1, "third_party_packages", new=packages
        ), caplog.at_level(logging.INFO):
            result = self.run_cli_command("packages", "sync")
            assert result.exit_code == 0
            assert (
                "(skill, author/some_skill:0.1.0) not found locally, downloading..."
                in caplog.text
            )

    def test_sync_with_wrong_hash(self, ipfs_mock, hash_mock, caplog) -> None:
        """Test sync with missing packages."""

        packages = {
            PackageId.from_uri_path(
                "protocol/open_aea/signing/1.0.0"
            ): "bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo41"
        }

        with mock.patch.object(PackageManagerV1, "third_party_packages", new=packages):
            with pytest.raises(
                click.ClickException,
                match=re.escape(
                    "Hashes for (protocol, open_aea/signing:1.0.0) does not match;"
                ),
            ):
                self.run_cli_command("packages", "sync")

        with mock.patch.object(
            PackageManagerV1, "third_party_packages", new=packages
        ), mock.patch("shutil.rmtree"), caplog.at_level(logging.INFO):
            result = self.run_cli_command(
                "packages",
                "sync",
                "--update-packages",
            )
            assert result.exit_code == 0
            assert (
                "Hash does not match for (protocol, open_aea/signing:1.0.0), downloading package again..."
                in caplog.text
            )

        with mock.patch.object(
            PackageManagerV1, "third_party_packages", new=packages
        ), mock.patch("shutil.rmtree"), caplog.at_level(logging.INFO):
            result = self.run_cli_command(
                "packages",
                "sync",
                "--update-hashes",
            )
            assert result.exit_code == 0
            assert (
                "Updating (protocol, open_aea/signing:1.0.0:bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo41)"
                in caplog.text
            )
