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

"""Test `aea hash` command."""

from typing import Set

import click
import pytest

from aea.configurations.data_types import PackageId
from aea.helpers.dependency_tree import DependencyTree
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.test_cases import BaseAEATestCase


class TestHashAll(BaseAEATestCase):
    """Test `aea hash all`"""

    use_packages_dir: bool = True

    def test_invocation(
        self,
    ) -> None:
        """Test command invocation."""

        tree = DependencyTree.generate(self.packages_dir_path)
        packages: Set[PackageId] = set()
        for level in tree:
            packages.update(level)

        result = self.run_cli_command(
            "hash", "all", "--packages-dir", str(self.packages_dir_path)
        )

        assert result.exit_code == 0, result.output
        assert all(
            f"Processing package {package_id.name} of type {package_id.package_type}"
            in result.output
            for package_id in packages
        )

    def test_empty_packages_dir(
        self,
    ) -> None:
        """Test packages directory being empty"""

        with pytest.raises(
            AEATestingException, match="ValueError: Could not find any package in"
        ):
            self.run_cli_command("hash", "all", "--packages-dir", str(self.t))

    def test_vendor_flag(
        self,
    ) -> None:
        """Test `--vendor` flag"""

        vendor = "valory"
        tree = DependencyTree.generate(self.packages_dir_path)
        packages: Set[PackageId] = set()
        for level in tree:
            packages.update(level)

        result = self.run_cli_command(
            "hash",
            "all",
            "--packages-dir",
            str(self.packages_dir_path),
            "--vendor",
            vendor,
        )

        assert result.exit_code == 0, result.output
        assert all(
            f"Skipping the hash update for {package_id.name} of type {package_id.package_type}"
            in result.output
            for package_id in packages
            if package_id.author != vendor
        ), result.output


class TestHashOne(BaseAEATestCase):
    """Test `aea hash one`"""

    use_packages_dir: bool = True

    def test_run(
        self,
    ) -> None:
        """Test command invocation."""

        temp_file = self.t / "file.txt"
        temp_file.write_text("Hello, World!")

        result = self.run_cli_command("hash", "one", str(temp_file))

        assert result.exit_code == 0, result.output
        assert (
            "Hash : bafybeibv2rf6ebovxm3mnr2bottqerc3p23uezk376pyaob4mu6qyddgw4"
            in result.output
        )

    def test_no_wrap(
        self,
    ) -> None:
        """Test command invocation with `--no-wrap` flag."""

        temp_file = self.t / "file.txt"
        temp_file.write_text("Hello, World!")

        result = self.run_cli_command("hash", "one", str(temp_file), "--no-wrap")

        assert result.exit_code == 0, result.output
        assert (
            "Hash : bafybeifkhqxtv22r566qadr6owj25yqdme2wecr4qsbehnh5wztzjb26le"
            in result.output
        )


class TestHashConversion(BaseAEATestCase):
    """Test hash conversion."""

    v0_hash = "QmZoBFCYa4gJRYhpKuVWXon461apqQYKb7FUqS2h9HPM3e"
    v1_hash = "bafybeifkhqxtv22r566qadr6owj25yqdme2wecr4qsbehnh5wztzjb26le"

    def test_to_v1(
        self,
    ) -> None:
        """Test `to-v1` command."""

        result = self.run_cli_command("hash", "to-v1", self.v0_hash)

        assert result.exit_code == 0, result.output
        assert self.v1_hash in result.output, result.output

    def test_to_v0(
        self,
    ) -> None:
        """Test `to-v0` command."""

        result = self.run_cli_command(
            "hash",
            "to-v0",
            self.v1_hash,
        )

        assert result.exit_code == 0, result.output
        assert self.v0_hash in result.output, result.output

    def test_to_v1_failure(
        self,
    ) -> None:
        """Test `to-v1` command."""

        with pytest.raises(click.ClickException, match=f"{self.v1_hash} is already v1"):
            self.run_cli_command("hash", "to-v1", self.v1_hash)

    def test_to_v0_failure(
        self,
    ) -> None:
        """Test `to-v1` command."""

        with pytest.raises(click.ClickException, match=f"{self.v0_hash} is already v0"):
            self.run_cli_command("hash", "to-v0", self.v0_hash)
