# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This test module contains tests for CLI Registry add methods."""

import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

from aea.cli.add import HashNotProvided
from aea.cli.registry.add import fetch_package
from aea.cli.registry.settings import REMOTE_IPFS
from aea.configurations.base import PublicId
from aea.helpers.base import cd
from aea.test_tools.test_cases import BaseAEATestCase


@mock.patch("aea.cli.registry.utils.request_api", return_value={"file": "url"})
@mock.patch("aea.cli.registry.add.download_file", return_value="filepath")
@mock.patch("aea.cli.registry.add.extract")
class FetchPackageTestCase(TestCase):
    """Test case for fetch_package method."""

    def test_fetch_package_positive(
        self, extract_mock, download_file_mock, request_api_mock
    ):
        """Test for fetch_package method positive result."""
        obj_type = "connection"
        public_id = PublicId.from_str("author/name:0.1.0")
        cwd = "cwd"
        dest_path = os.path.join("dest", "path", "package_folder_name")

        fetch_package(obj_type, public_id, cwd, dest_path)
        request_api_mock.assert_called_with(
            "GET", "/connections/author/name/0.1.0", params=None
        )
        download_file_mock.assert_called_once_with("url", "cwd")
        extract_mock.assert_called_once_with("filepath", os.path.join("dest", "path"))


class BaseTestAdd(BaseAEATestCase):
    """Test `aea add` command."""

    agent_name: str
    agent_dir: Path
    skill_path: Path
    skill_id: PublicId = PublicId(
        author="fetchai",
        name="echo",
        package_hash="bafybeia3ovoxmnipktwnyztie55itsuempnfeircw72jn62uojzry5pwsu",
    )

    @classmethod
    def setup_class(cls) -> None:
        """Setup test class."""

        super().setup_class()

        cls.agent_name = "agent"
        cls.create_agents(cls.agent_name)

        cls.agent_dir = cls.t / cls.agent_name
        cls.skill_path = (
            cls.packages_dir_path.absolute()
            / cls.skill_id.author
            / "skills"
            / cls.skill_id.name
        )


class TestAddFromHash(BaseTestAdd):
    """Test add using hash."""

    def test_from_hash(
        self,
    ) -> None:
        """Test run."""

        with cd(self.agent_dir), TemporaryDirectory() as temp_dir:
            download_path = Path(temp_dir, self.skill_id.name)
            shutil.copytree(self.skill_path, download_path)
            with mock.patch(
                "aea.cli.add.get_default_remote_registry", return_value=REMOTE_IPFS
            ), mock.patch(
                "aea.cli.add.fetch_ipfs", return_value=download_path
            ), mock.patch(
                "aea.cli.add._add_item_deps"
            ):
                result = self.run_cli_command(
                    "add",
                    "skill",
                    self.skill_id.hash,
                    "--remote",
                )

                assert result.exit_code == 0, result.output
                assert "Successfully added skill" in result.stdout

                assert (Path.cwd() / "vendor" / "fetchai" / "skills" / "echo").exists()


class TestAddFromHashIPFSFail(BaseTestAdd):
    """Test ipfs registry failing"""

    def test_hash_not_provided(
        self,
    ) -> None:
        """Test run."""

        with cd(self.agent_dir), TemporaryDirectory() as temp_dir:
            download_path = Path(temp_dir, self.skill_id.name)
            shutil.copytree(self.skill_path, download_path)
            with mock.patch(
                "aea.cli.add.get_default_remote_registry", return_value=REMOTE_IPFS
            ), mock.patch(
                "aea.cli.add.fetch_ipfs", side_effect=HashNotProvided
            ), mock.patch(
                "aea.cli.add.fetch_package", return_value=download_path
            ), mock.patch(
                "aea.cli.add._add_item_deps"
            ):
                result = self.run_cli_command(
                    "add",
                    "skill",
                    self.skill_id.hash,
                    "--remote",
                )

                assert result.exit_code == 0, result.output
                assert "Hash was not provided for" in result.stdout
                assert "Will try with http repository" in result.stdout
                assert "Successfully added skill" in result.stdout
