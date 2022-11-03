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
from typing import Any
from unittest import mock

from aea.cli import cli
from aea.configurations.constants import PACKAGES
from aea.configurations.data_types import PackageId
from aea.package_manager.base import PACKAGES_FILE
from aea.package_manager.v1 import PackageManagerV1
from aea.test_tools.test_cases import BaseAEATestCase


@mock.patch("aea.package_manager.base.fetch_ipfs")
class TestLockCommand(BaseAEATestCase):
    """Test sync command."""

    def test_lock(self, *args: Any) -> None:
        """Test sync command."""

        result = self.run_cli_command("packages", "lock")
        assert result.exit_code == 0
        assert "Updating hashes" in result.stdout
        assert "Done" in result.stdout

    def test_lock_check(self, fetch_mock, caplog) -> None:
        """Test sync command."""

        result = self.run_cli_command("packages", "lock", "--check")
        assert result.exit_code == 0

        packages_file = self.t / PACKAGES / PACKAGES_FILE
        dev_packages = dict(
            map(
                lambda x: (PackageId.from_uri_path(x[0]), x[1]),
                json.loads(packages_file.read_text())["dev"].items(),
            )
        )
        dev_packages[
            PackageId.from_uri_path("protocol/open_aea/signing/1.0.0")
        ] = "bafybeiambqptflge33eemdhis2whik67hjplfnqwieoa6wblzlaf7vu"

        with mock.patch.object(
            PackageManagerV1, "dev_packages", new=dev_packages
        ), caplog.at_level(logging.INFO):
            result = self.runner.invoke(cli, ["packages", "lock", "--check"])
            assert result.exit_code == 1
            assert (
                "Hash does not match for (protocol, open_aea/signing:1.0.0)"
                in caplog.text
            )
