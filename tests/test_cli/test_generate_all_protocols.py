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

"""Test `generate-all-protocols` command."""

import logging
import pprint
import shutil
import subprocess  # nosec
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from aea.configurations.constants import (
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_README_FILE,
)
from aea.exceptions import enforce
from aea.manager.helpers import AEAProject
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.test_cases import AEATestCaseMany


def _run_cli_patch(*args: Any, **kwargs: Any) -> None:
    if "isort" in args or "black" in args:
        return

    print(f"Calling command {args} with kwargs {kwargs}")
    return_code = subprocess.check_call(args, **kwargs)  # nosec
    enforce(
        return_code == 0,
        f"Return code of {pprint.pformat(args)} is {return_code} != 0.",
    )


class BaseGenerateAllProtocolsTestCase(AEATestCaseMany):
    """Base test class."""

    use_packages_dir: bool = True
    find_packages_patch: Any
    package_path: Path

    @classmethod
    def setup_class(cls) -> None:
        """Setup test class."""
        super().setup_class()

        cls.packages_dir_path = cls.packages_dir_path.absolute()
        cls.package_path = cls.packages_dir_path / "fetchai" / "protocols" / "fipa"
        cls.find_packages_patch = mock.patch(
            "aea.cli.generate_all_protocols.find_protocols_in_local_registry",
            return_value=(cls.package_path,),
        )


class TestGenerateAllProtcols(BaseGenerateAllProtocolsTestCase):
    """Test generate all protocols."""

    def test_run(self, caplog) -> None:
        """Test command invocation."""

        with self.find_packages_patch, mock.patch.object(
            AEAProject, "run_cli", new=_run_cli_patch
        ), caplog.at_level(logging.INFO):
            result = self.run_cli_command(
                "generate-all-protocols",
                str(self.packages_dir_path),
                "--root-dir",
                str(self.packages_dir_path.parent),
            )

            assert result.exit_code == 0
            assert f"Processing protocol at path {self.package_path}"

    def test_check_clean_pass(self) -> None:
        """Test command invocation."""

        with self.find_packages_patch, mock.patch.object(
            AEAProject, "run_cli", new=_run_cli_patch
        ), mock.patch(
            "aea.cli.generate_all_protocols.check_working_tree_is_dirty",
            return_value=True,
        ):
            result = self.run_cli_command(
                "generate-all-protocols",
                str(self.packages_dir_path),
                "--root-dir",
                str(self.packages_dir_path.parent),
                "--check-clean",
            )

            assert result.exit_code == 0, result.output

    def test_check_clean_fail(self) -> None:
        """Test command invocation."""

        with self.find_packages_patch, mock.patch.object(
            AEAProject, "run_cli", new=_run_cli_patch
        ), mock.patch(
            "aea.cli.generate_all_protocols.check_working_tree_is_dirty",
            return_value=False,
        ):
            with pytest.raises(AEATestingException, match="Exit code: 1"):
                self.run_cli_command(
                    "generate-all-protocols",
                    str(self.packages_dir_path),
                    "--root-dir",
                    str(self.packages_dir_path.parent),
                    "--check-clean",
                )

    def test_check_bump(self) -> None:
        """Test command invocation."""

        fipa_dir = self.package_path

        def _download_patch(_: Any, temp_dir: str):
            temp_fipa = Path(temp_dir, "fipa")
            shutil.copytree(fipa_dir, temp_fipa)

            config_file = temp_fipa / DEFAULT_PROTOCOL_CONFIG_FILE
            config_file.write_text(
                config_file.read_text().replace("version: 1.0.0", "version: 0.1.0")
            )

            readme_file = temp_fipa / DEFAULT_README_FILE
            readme_file.write_text(
                readme_file.read_text().replace("version: 1.0.0", "version: 0.1.0")
            )

        with self.find_packages_patch, mock.patch(
            "aea.cli.generate_all_protocols.download_package", new=_download_patch
        ), mock.patch(
            "aea.cli.generate_all_protocols._process_packages_protocol"
        ), mock.patch(
            "aea.cli.generate_all_protocols.log"
        ) as logger:
            self.run_cli_command(
                "generate-all-protocols",
                str(self.packages_dir_path),
                "--root-dir",
                str(self.packages_dir_path.parent),
            )
            logger.assert_called_with(
                "Bumping protocol specification id from 'fetchai/fipa:1.0.0' to 'fetchai/fipa:1.0.0'"
            )

    def test_check_bump_fail(self) -> None:
        """Test command invocation."""

        fipa_dir = self.package_path

        def _download_patch(_: Any, temp_dir: str):
            temp_fipa = Path(temp_dir, "fipa")
            shutil.copytree(fipa_dir, temp_fipa)

        with self.find_packages_patch, mock.patch(
            "aea.cli.generate_all_protocols.download_package", new=_download_patch
        ), mock.patch(
            "aea.cli.generate_all_protocols._process_packages_protocol"
        ), mock.patch(
            "aea.cli.generate_all_protocols.log"
        ) as logger:
            self.run_cli_command(
                "generate-all-protocols",
                str(self.packages_dir_path),
                "--root-dir",
                str(self.packages_dir_path.parent),
            )
            logger.assert_called_with(
                "Protocol specification id not bumped - content is not different, or version is not newer."
            )

    def test_no_bump(self) -> None:
        """Test command invocation."""

        with self.find_packages_patch, mock.patch.object(
            AEAProject, "run_cli", new=_run_cli_patch
        ):
            self.run_cli_command(
                "generate-all-protocols",
                str(self.packages_dir_path),
                "--root-dir",
                str(self.packages_dir_path.parent),
                "--no-bump",
            )

    def test_no_bump_failure(self) -> None:
        """Test command invocation."""

        with self.find_packages_patch, mock.patch.object(
            AEAProject, "run_cli", new=_run_cli_patch
        ), mock.patch("re.compile", return_value=mock.MagicMock(search=lambda _: None)):
            with pytest.raises(
                ValueError, match="protocol generator docstring not found"
            ):
                self.run_cli_command(
                    "generate-all-protocols",
                    str(self.packages_dir_path),
                    "--root-dir",
                    str(self.packages_dir_path.parent),
                    "--no-bump",
                )


class TestParentAsRootDir(BaseGenerateAllProtocolsTestCase):
    """Test generate all protocols."""

    def test_root_dir_parent(self, caplog) -> None:
        """Test command invocation."""

        with self.find_packages_patch, mock.patch.object(
            AEAProject, "run_cli", new=_run_cli_patch
        ), caplog.at_level(logging.INFO):
            result = self.run_cli_command(
                "generate-all-protocols",
                str(self.packages_dir_path),
                "--root-dir",
                str(self.packages_dir_path.parent.parent),
            )

            assert result.exit_code == 0
            assert (
                "Replace prefix of import statements in directory 'fipa'" in caplog.text
            )

    def test_root_dir_dont_match(self) -> None:
        """Test command invocation."""

        with self.find_packages_patch, mock.patch.object(
            AEAProject, "run_cli", new=_run_cli_patch
        ):
            with pytest.raises(
                ValueError,
                match="Packages dir should be a sub directory of the root directory.",
            ):
                self.run_cli_command(
                    "generate-all-protocols",
                    str(self.packages_dir_path),
                )
