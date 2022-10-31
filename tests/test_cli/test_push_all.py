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

"""Tests for `aea push-all` command."""

from unittest import mock

import click
import pytest

from aea.cli.registry.settings import REMOTE_HTTP, REMOTE_IPFS
from aea.configurations.constants import PYCACHE
from aea.test_tools.test_cases import BaseAEATestCase


class TestPushAll(BaseAEATestCase):
    """Test `push-all` command"""

    def test_run(
        self,
    ) -> None:
        """Test command invocation"""

        with mock.patch("aea.cli.push_all.push_item_ipfs"), mock.patch(
            "aea.cli.push_all.get_default_remote_registry", return_value=REMOTE_IPFS
        ):
            result = self.run_cli_command("push-all", "--remote")

            assert result.exit_code == 0, result.output
            assert all(
                f"Pushing: {package_path}" in result.output
                for package_path in self.packages_dir_path.absolute().glob("*/*/*")
                if package_path.is_dir() and package_path.name != PYCACHE
            )

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
