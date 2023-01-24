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

"""Tests for `aea push-all` command."""

from collections import OrderedDict
from pathlib import Path
from unittest import mock

import click
import pytest

from aea.cli.registry.settings import REMOTE_HTTP, REMOTE_IPFS
from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.package_manager.v0 import PackageManagerV0
from aea.package_manager.v1 import PackageManagerV1
from aea.test_tools.test_cases import BaseAEATestCase


TEST_PACKAGE = PublicId(
    "open_aea",
    "signing",
    "0.1.0",
    "bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vuo44",
)
TEST_PACKAGE_ID = PackageId(PackageType.PROTOCOL, TEST_PACKAGE)
TEST_PACKAGES = [
    (
        TEST_PACKAGE_ID,
        TEST_PACKAGE.hash,
    )
]


class TestPushAll(BaseAEATestCase):
    """Test `push-all` command"""

    @pytest.mark.parametrize(
        "package_manager",
        (
            PackageManagerV1(
                path=Path(".", PACKAGES),
                dev_packages=OrderedDict(TEST_PACKAGES),
            ),
            PackageManagerV0(
                path=Path(".", PACKAGES),
                packages=OrderedDict(TEST_PACKAGES),
            ),
        ),
    )
    def test_run(self, package_manager) -> None:
        """Test command invocation"""
        with mock.patch("aea.cli.push_all.push_item_ipfs"), mock.patch(
            "aea.cli.push_all.get_default_remote_registry", return_value=REMOTE_IPFS
        ), mock.patch(
            "aea.cli.push_all.get_package_manager", return_value=package_manager
        ):
            result = self.run_cli_command("push-all", "--remote")

            package_path = package_manager.package_path_from_package_id(TEST_PACKAGE_ID)
            assert result.exit_code == 0, result.output
            assert f"Pushing: {package_path}" in result.output

    def test_local(
        self,
    ) -> None:
        """Test"""

        with pytest.raises(
            click.ClickException,
            match="Pushing all packages is not supported for the local registry",
        ):
            self.run_cli_command("push-all", "--local")

    def test_remote_http(
        self,
    ) -> None:
        """Test command invocation"""

        with mock.patch(
            "aea.cli.push_all.get_default_remote_registry", return_value=REMOTE_HTTP
        ):
            with pytest.raises(
                click.ClickException,
                match="Pushing all packages is not supported for the HTTP registry",
            ):
                self.run_cli_command("push-all", "--remote")

    def test_retries_applied(self) -> None:
        """Test retries flag works for pushing packages."""
        with mock.patch(
            "aea.cli.push_all.get_package_manager",
            return_value=PackageManagerV1(
                path=Path(".", PACKAGES),
                dev_packages=OrderedDict(TEST_PACKAGES[:1]),
            ),
        ), mock.patch(
            "aea.cli.push_all.get_default_remote_registry", return_value=REMOTE_IPFS
        ), mock.patch(
            "pathlib.Path.glob", return_value=[]
        ):
            with mock.patch(
                "aea.cli.push.IPFSTool.add", side_effect=Exception("expected")
            ) as push_item_ipfs_mock, pytest.raises(Exception, match="expected"):
                self.run_cli_command("push-all", "--remote")
            push_item_ipfs_mock.assert_called_once()

            with mock.patch(
                "aea.cli.push.IPFSTool.add", side_effect=Exception("expected")
            ) as push_item_ipfs_mock, pytest.raises(Exception, match="expected"):
                self.run_cli_command("push-all", "--remote", "--retries=3")
            assert push_item_ipfs_mock.call_count == 3
