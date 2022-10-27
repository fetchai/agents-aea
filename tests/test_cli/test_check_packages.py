# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
#   Copyright 2018-2019 Fetch.AI Limited
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

"""Test check packages command module."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List
from unittest import mock

import pytest

from aea.cli.check_packages import find_all_configuration_files, get_public_id_from_yaml
from aea.test_tools.test_cases import BaseAEATestCase


check_author_patch = mock.patch("aea.cli.check_packages.check_author")
check_dependencies_patch = mock.patch("aea.cli.check_packages.check_dependencies")
find_all_packages_ids_patch = mock.patch(
    "aea.cli.check_packages.find_all_packages_ids", return_value=set()
)


def _unified_yaml_load_patch(**config) -> Any:
    return mock.patch(
        "aea.cli.check_packages.unified_yaml_load",
        return_value=dict(**config),
    )


def _find_all_configuration_files_patch(config_files: List) -> Any:
    return mock.patch(
        "aea.cli.check_packages.find_all_configuration_files",
        return_value=config_files,
    )


@dataclass
class _TestPublicIdParameters:
    """Dataclass to store parameters for a public id check test."""

    side_effect: List
    exit_code: int
    message: str


class TestCheckPackagesCommand(BaseAEATestCase):
    """Test check-packages command."""

    use_packages_dir: bool = True
    test_aea_config: Path
    test_connection_config: Path

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""
        super().setup_class()

        cls.test_aea_config = (
            cls.t / "packages" / "fetchai" / "agents" / "error_test" / "aea-config.yaml"
        )
        cls.test_connection_config = (
            cls.t / "packages" / "fetchai" / "connections" / "gym" / "connection.yaml"
        )

    def test_invocation(
        self,
    ) -> None:
        """Test command invocation."""

        result = self.invoke(
            "--registry-path",
            str(self.packages_dir_path),
            "check-packages",
        )

        assert result.exit_code == 0, result.output
        assert all(
            str(file) in result.output
            for file in find_all_configuration_files(self.packages_dir_path.absolute())
        )

    def test_dependency_not_found(
        self,
    ) -> None:
        """Test"""

        with find_all_packages_ids_patch, _find_all_configuration_files_patch(
            [self.test_aea_config]
        ):
            result = self.invoke(
                "--registry-path",
                str(self.packages_dir_path),
                "check-packages",
            )

        assert result.exit_code == 1, result.output
        assert "Missing: " in result.output, result.output

    def test_check_description_failure(
        self,
    ) -> None:
        """Test description check."""

        with _unified_yaml_load_patch(
            description=""
        ), check_author_patch, check_dependencies_patch, find_all_packages_ids_patch, _find_all_configuration_files_patch(
            [
                self.test_aea_config,
            ]
        ):
            result = self.invoke(
                "--registry-path",
                str(self.packages_dir_path),
                "check-packages",
            )

        assert result.exit_code == 1, result.output
        assert "has empty description field." in result.output

    def test_check_author_failure(
        self,
    ) -> None:
        """Test `check_author` failure."""

        with _unified_yaml_load_patch(
            author="SOME_AUTHOR"
        ), find_all_packages_ids_patch, _find_all_configuration_files_patch(
            [
                self.test_aea_config,
            ]
        ):
            result = self.invoke(
                "--registry-path",
                str(self.packages_dir_path),
                "check-packages",
            )

        assert result.exit_code == 1, result.output
        assert (
            "has an unexpected author value: expected fetchai, found 'SOME_AUTHOR'"
            in result.output
        )

    def test_check_public_id_failure(
        self,
    ) -> None:
        """Test `check_public_id` failure."""

        with mock.patch(
            "re.findall", return_value=[]
        ), _find_all_configuration_files_patch(
            [self.test_connection_config]
        ), check_dependencies_patch:
            result = self.invoke(
                "--registry-path",
                str(self.packages_dir_path),
                "check-packages",
            )

        assert result.exit_code == 1, result.output
        assert "expected unique definition of PUBLIC_ID for package" in result.output
        assert "found 0" in result.output

    @pytest.mark.parametrize(
        "test_param",
        [
            _TestPublicIdParameters(
                side_effect=[
                    [(None,)],
                    [(None, None, None)],
                ],
                exit_code=1,
                message="found 'None'",
            ),
            _TestPublicIdParameters(
                side_effect=[
                    [(None,)],
                    [],
                    [(None, None, None)],
                ],
                exit_code=1,
                message="found 'None/None:None'",
            ),
            _TestPublicIdParameters(
                side_effect=[
                    [(None,)],
                    [],
                    [("fetchai", "gym", "0.19.0")],
                ],
                exit_code=0,
                message="OK!",
            ),
            _TestPublicIdParameters(
                side_effect=[
                    [(None,)],
                    [],
                    ["", ()],
                ],
                exit_code=1,
                message="found ''",
            ),
        ],
    )
    def test_check_public_id_failure_wrong_public_id(
        self, test_param: _TestPublicIdParameters
    ) -> None:
        """Test `check_public_id` failure."""

        with mock.patch(
            "re.findall",
            side_effect=test_param.side_effect,
        ), _find_all_configuration_files_patch(
            [self.test_connection_config]
        ), check_dependencies_patch:
            result = self.invoke(
                "--registry-path",
                str(self.packages_dir_path),
                "check-packages",
            )

        assert result.exit_code == test_param.exit_code, result.output
        assert test_param.message in result.output

    def test_check_pypi_dependencies_failure(
        self,
    ) -> None:
        """Test `check_pypi_dependencies`"""

        with mock.patch(
            "aea.cli.check_packages.PyPIDependenciesCheckTool.check_imports",
            return_value=(
                [
                    "dep_1",
                ],
                [],
            ),
        ), _find_all_configuration_files_patch(
            [self.test_connection_config]
        ), check_dependencies_patch:
            result = self.invoke(
                "--registry-path",
                str(self.packages_dir_path),
                "check-packages",
            )

        assert result.exit_code == 1, result.output
        assert "unresolved imports: dep_1" in result.output, result.output


def test_get_public_id_from_yaml_failure() -> None:
    """Test `get_public_id_from_yaml` failures."""

    with _unified_yaml_load_patch(author="author"):
        with pytest.raises(KeyError, match="agent_name"):
            get_public_id_from_yaml(Path("."))
