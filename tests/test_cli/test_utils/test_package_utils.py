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

"""Test package utils."""
import os
import re
from pathlib import Path
from typing import cast
from unittest import mock
from unittest.mock import patch

import click
import pytest

from aea import Version
from aea.cli.utils.context import Context
from aea.cli.utils.package_utils import (
    is_item_with_hash_present,
    list_available_packages,
    try_get_item_source_path,
    try_get_item_target_path,
    update_aea_version_range,
    validate_package_name,
    verify_private_keys_ctx,
)
from aea.configurations.base import AgentConfig
from aea.configurations.data_types import PublicId
from aea.configurations.manager import AgentConfigManager
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.test_tools.test_cases import BaseAEATestCase


def test_verify_private_keys_ctx_fail() -> None:
    """Test `verify_private_keys_ctx`"""

    ctx = Context(".", "INFO", ".")
    with mock.patch.object(
        AgentConfigManager,
        "verify_private_keys",
        side_effect=ValueError,
    ):
        with pytest.raises(click.ClickException):
            verify_private_keys_ctx(ctx)

    with pytest.raises(
        AttributeError,
        match=re.escape("'Context' object has no attribute 'agent_config'"),
    ):
        _ = ctx.agent_config


def test_validate_package_name() -> None:
    """Test `validate_package_name`"""

    with pytest.raises(
        click.BadParameter, match=re.escape("bad-param is not a valid package name.")
    ):
        validate_package_name("bad-param")


def test_try_get_item_source_path() -> None:
    """Test `try_get_item_source_path`"""

    path = "."
    author_name = "author"
    item_type_plural = "skill"
    item_name = "some_skill"

    with mock.patch("os.path.exists", return_value=True):
        source_path = try_get_item_source_path(
            path, author_name, item_type_plural, item_name
        )
        assert source_path == os.path.join(
            path, author_name, item_type_plural, item_name
        )

    with pytest.raises(
        click.ClickException,
        match=re.escape(
            f'Item "{author_name}/{item_name}" not found in source folder "{source_path}".'
        ),
    ):
        source_path = try_get_item_source_path(
            path, author_name, item_type_plural, item_name
        )

    with mock.patch("os.path.exists", return_value=True):
        source_path = try_get_item_source_path(path, None, item_type_plural, item_name)
        assert source_path == os.path.join(path, item_type_plural, item_name)


def test_try_get_item_target_path() -> None:
    """Test `try_get_item_target_path`"""

    path = "."
    author_name = "author"
    item_type_plural = "skill"
    item_name = "some_skill"

    assert try_get_item_target_path(
        path, author_name, item_type_plural, item_name
    ) == os.path.join(path, author_name, item_type_plural, item_name)

    with mock.patch("os.path.exists", return_value=True):
        with pytest.raises(
            click.ClickException,
            match=re.escape('Item "some_skill" already exists in target folder'),
        ):
            try_get_item_target_path(path, author_name, item_type_plural, item_name)


class TestListAvailablePackages(BaseAEATestCase):
    """Test list_available_packages method."""

    use_packages_dir: bool = True

    def test_list_available_packages(
        self,
    ) -> None:
        """Test `list_available_packages`"""

        agent_name = "agent"
        self.create_agents(agent_name)

        package_list = list_available_packages(Path(self.t / agent_name))
        assert len(package_list) == 1

        (package_id, _), *_ = package_list
        assert package_id.name == "signing"

        with mock.patch.object(Path, "is_dir", return_value=False):
            package_list = list_available_packages(Path(self.t / agent_name))
            assert len(package_list) == 1

            (package_id, package_path), *_ = package_list
            assert package_id.name == "signing"
            assert "vendor" not in package_path.parts


def test_update_aea_version_range() -> None:
    """Test `update_aea_version_range`"""
    package_config = AgentConfig("name", "author", aea_version="0.1.0")
    versions = [
        "1.0.0",
        "2.0.0",
        "2.2.2",
        "1.30.0post0",
        "1.30.0.post1",
        "1.30.0dev1",
        "1.30.0.dev1",
        "0.0.1",
        "1000.0.10000",
        "1.1.0alpha0",
        "1.1.0.alpha1",
    ]
    for version_str in versions:
        version = Version(version_str)
        with patch(
            "aea.cli.utils.package_utils.get_current_aea_version", return_value=version
        ):
            update_aea_version_range(package_configuration=package_config)
            assert version in package_config.aea_version_specifiers


class TestItemPresentWithHash(BaseAEATestCase):
    """Test is_item_with_hash_present method."""

    use_packages_dir: bool = True

    def test_is_item_with_hash_present(
        self,
    ) -> None:
        """Test `is_item_with_hash_present`"""

        agent_name = "agent"
        self.create_agents(agent_name)

        agent_config = self.load_agent_config(agent_name)
        (signing_protocol,) = agent_config.protocols

        assert is_item_with_hash_present(
            str(self.packages_dir_path), agent_config, signing_protocol.hash
        )

        assert (
            is_item_with_hash_present(str(self.packages_dir_path), agent_config, "Qm")
            is None
        )

        dummy_config = mock.MagicMock()

        with mock.patch.object(
            IPFSHashOnly, "hash_directory", return_value="Qm"
        ), mock.patch(
            "aea.cli.utils.config.load_item_config", return_value=dummy_config
        ):
            assert (
                cast(
                    PublicId,
                    is_item_with_hash_present(
                        str(self.t / agent_name), agent_config, "Qm"
                    ),
                ).name
                == "signing"
            )
