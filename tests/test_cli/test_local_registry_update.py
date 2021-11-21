# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
"""This test module contains the tests for the `aea local-registry-sync"""
import os
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from aea.cli.core import cli
from aea.cli.local_registry_sync import enlist_packages
from aea.cli.registry.add import fetch_package
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.helpers.base import cd
from aea.test_tools.click_testing import CliRunner


@pytest.mark.skip  # need remote registry
def test_local_registry_update():
    """Test local-registry-sync cli command."""
    PACKAGES = [
        PackageId(PackageType.CONNECTION, PublicId("fetchai", "local", "0.17.0")),
        PackageId(PackageType.AGENT, PublicId("fetchai", "my_first_aea", "0.24.0")),
    ]
    with TemporaryDirectory() as tmp_dir:
        for package_id in PACKAGES:
            package_dir = os.path.join(
                tmp_dir,
                package_id.public_id.author,
                str(package_id.package_type.to_plural()),
                package_id.public_id.name,
            )
            os.makedirs(package_dir)
            fetch_package(
                str(package_id.package_type),
                public_id=package_id.public_id,
                cwd=tmp_dir,
                dest=package_dir,
            )

        assert set(PACKAGES) == set([i[0] for i in enlist_packages(tmp_dir)])

        runner = CliRunner()
        with cd(tmp_dir):
            # check intention to upgrade
            with patch(
                "aea.cli.local_registry_sync.replace_package"
            ) as replace_package_mock:
                result = runner.invoke(
                    cli, ["-s", "local-registry-sync"], catch_exceptions=False
                )
                assert result.exit_code == 0, result.stdout
            assert replace_package_mock.call_count == 2

            # do actual upgrade
            result = runner.invoke(
                cli, ["-s", "local-registry-sync"], catch_exceptions=False
            )
            assert result.exit_code == 0, result.stdout

            # check next update will do nothing
            with patch(
                "aea.cli.local_registry_sync.replace_package"
            ) as replace_package_mock:
                result = runner.invoke(
                    cli, ["-s", "local-registry-sync"], catch_exceptions=False
                )
                assert result.exit_code == 0, result.stdout
            assert replace_package_mock.call_count == 0

        def sort_(packages):
            return sorted(packages, key=lambda x: str(x))

        new_packages = [i[0] for i in enlist_packages(tmp_dir)]

        for new_package, old_package in zip(sort_(new_packages), sort_(PACKAGES)):
            assert new_package.public_id != old_package.public_id
