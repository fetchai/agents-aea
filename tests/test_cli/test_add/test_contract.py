# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
"""This test module contains the tests for the `aea add contract` sub-command."""

import os
from unittest import TestCase, mock

import pytest

from aea.cli import cli
from aea.cli.registry.settings import REMOTE_HTTP
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.test_tools.test_cases import AEATestCaseEmptyFlaky

from packages.fetchai.contracts.erc1155.contract import PUBLIC_ID as ERC1155_PUBLIC_ID

from tests.conftest import (
    CLI_LOG_OPTION,
    CliRunner,
    MAX_FLAKY_RERUNS,
    TEST_IPFS_REGISTRY_CONFIG,
    get_package_id_with_hash,
)
from tests.test_cli.test_add.test_generic import BaseTestAddRemoteMode


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.utils.decorators._validate_config_consistency")
class AddContractCommandTestCase(TestCase):
    """Test that the command 'aea add contract' works as expected."""

    def setUp(self):
        """Set the test up."""
        self.runner = CliRunner()

    @mock.patch("aea.cli.add.add_item")
    def test_add_contract_positive(self, *mocks):
        """Test add contract command positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "contract", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "contract", "author/name:0.1.0"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@pytest.mark.integration
class TestAddContractFromRemoteRegistryHTTP(AEATestCaseEmptyFlaky):
    """Test case for add contract from Registry command."""

    IS_LOCAL = False
    IS_EMPTY = True

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    @mock.patch(
        "aea.cli.registry.utils.get_or_create_cli_config",
        return_value=TEST_IPFS_REGISTRY_CONFIG,
    )
    @mock.patch("aea.cli.add.get_default_remote_registry", return_value=REMOTE_HTTP)
    @mock.patch("aea.cli.add.is_fingerprint_correct", return_value=True)
    @mock.patch(
        "aea.configurations.validation.ConfigValidator.validate", return_value=True
    )  # cause validator changed
    def test_add_contract_from_remote_registry_positive(self, *_):
        """Test add contract from Registry positive result."""
        self.add_item(
            "contract", str(ERC1155_PUBLIC_ID.to_latest()), local=self.IS_LOCAL
        )

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "contracts")
        items_folders = os.listdir(items_path)
        item_name = "erc1155"
        assert item_name in items_folders


class TestAddContractWithLatestVersion(AEATestCaseEmptyFlaky):
    """Test case for add contract with latest version."""

    IS_LOCAL = True

    @pytest.mark.integration
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_add_contract_latest_version(self):
        """Test add contract with latest version."""
        self.add_item(
            "contract", str(ERC1155_PUBLIC_ID.to_latest()), local=self.IS_LOCAL
        )

        items_path = os.path.join(self.agent_name, "vendor", "fetchai", "contracts")
        items_folders = os.listdir(items_path)
        item_name = "erc1155"
        assert item_name in items_folders


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
class TestAddContractRemoteMode(BaseTestAddRemoteMode):
    """Test case for add contract, --remote mode."""

    COMPONENT_ID = get_package_id_with_hash(
        PackageId(
            package_type=PackageType.CONTRACT,
            public_id=PublicId(
                "fetchai",
                "erc1155",
                "0.22.0",
            ),
        )
    ).public_id
    COMPONENT_TYPE = PackageType.CONTRACT
