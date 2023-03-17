# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Test `aea packages init` command."""


import click
import pytest

from aea.configurations.constants import PACKAGES
from aea.test_tools.test_cases import BaseAEATestCase


class TestInit(BaseAEATestCase):
    """Test init command."""

    use_packages_dir = False

    def test_init_repo(self) -> None:
        """Test init command."""

        result = self.run_cli_command(
            "--registry-path", str(self.t), "packages", "init"
        )

        assert result.exit_code == 0
        assert "Initialized packages repository" in result.stdout
        assert (self.t / PACKAGES).exists()


class TestInitFailure(BaseAEATestCase):
    """Test init command failure."""

    def test_init_repo(self) -> None:
        """Test init command."""

        with pytest.raises(
            click.ClickException, match="Packages repository already exists"
        ):
            self.run_cli_command("--registry-path", str(self.t), "packages", "init")
