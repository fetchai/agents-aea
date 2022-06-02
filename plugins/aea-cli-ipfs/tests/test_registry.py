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
"""This test package contains the tests for ipfs registry tools."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pytest
from aea_cli_ipfs.registry import (
    LOCAL_REGISTRY_DEFAULT,
    fetch_ipfs,
    get_ipfs_hash_from_public_id,
    load_local_registry,
    register_item_to_local_registry,
    validate_registry,
    write_local_registry,
)

from aea.configurations.data_types import PublicId


DUMMY_REGISTRY_DATA = LOCAL_REGISTRY_DEFAULT.copy()
DUMMY_REGISTRY_DATA["protocols"] = {
    "default_author/component:0.1.0": "hash_1",
    "default_author/component:0.2.0": "hash_2",
    "default_author/component:0.3.0": "hash_3",
}


def test_validate_registry() -> None:
    """Test validate registry."""

    with pytest.raises(ValueError):
        validate_registry({})


def test_write_local_registry() -> None:
    """Test write_local_registry method."""

    with TemporaryDirectory() as temp_dir:
        registry_path = Path(temp_dir) / "local_registry.json"
        write_local_registry(LOCAL_REGISTRY_DEFAULT, str(registry_path))

        assert registry_path.is_file()
        assert load_local_registry(str(registry_path)) == LOCAL_REGISTRY_DEFAULT


def test_load_local_registry() -> None:
    """Test write_local_registry method."""

    with TemporaryDirectory() as temp_dir:
        registry_path = Path(temp_dir) / "local_registry.json"
        assert load_local_registry(str(registry_path)) == LOCAL_REGISTRY_DEFAULT

        write_local_registry(DUMMY_REGISTRY_DATA, str(registry_path))
        assert load_local_registry(str(registry_path)) == DUMMY_REGISTRY_DATA


def test_get_ipfs_hash_from_public_id() -> None:
    """Test get_ipfs_hash_from_public_id method."""

    with mock.patch(
        "aea_cli_ipfs.registry.load_local_registry",
        new=lambda *_, **__: DUMMY_REGISTRY_DATA,
    ):
        # test hash retrival
        package_hash = get_ipfs_hash_from_public_id(
            "protocol", PublicId.from_str("default_author/component:0.1.0")
        )
        assert package_hash == "hash_1"

        # test hash retrival for latest package
        package_hash = get_ipfs_hash_from_public_id(
            "protocol", PublicId.from_str("default_author/component:latest")
        )
        assert package_hash == "hash_3"

        # test hash retrival for non existing package
        package_hash = get_ipfs_hash_from_public_id(
            "protocol", PublicId.from_str("default_author/component:1.0.0")
        )
        assert package_hash is None


def test_register_item_to_local_registry() -> None:
    """Test register_item_to_local_registry method."""

    with TemporaryDirectory() as temp_dir:
        registry_path = Path(temp_dir) / "local_registry.json"
        write_local_registry(DUMMY_REGISTRY_DATA, str(registry_path))
        register_item_to_local_registry(
            "skill", "fetchai/skill:0.1.0", "skill_hash", registry_path=registry_path
        )
        assert (
            get_ipfs_hash_from_public_id(
                "skill",
                PublicId.from_str("fetchai/skill:0.1.0"),
                registry_path=registry_path,
            )
            == "skill_hash"
        )

        assert (
            get_ipfs_hash_from_public_id(
                "skill",
                PublicId.from_str("fetchai/skill:latest"),
                registry_path=registry_path,
            )
            == "skill_hash"
        )


def test_fetch_ipfs() -> None:
    """Test fetch_ipfs method."""

    with mock.patch(
        "aea_cli_ipfs.registry.load_local_registry",
        new=lambda *_, **__: DUMMY_REGISTRY_DATA,
    ), TemporaryDirectory() as dest_path:

        with mock.patch("aea_cli_ipfs.ipfs_utils.IPFSTool.download"), mock.patch(
            "aea_cli_ipfs.ipfs_utils.IPFSTool.check_ipfs_node_running"
        ):
            package_path = fetch_ipfs(
                "protocol",
                PublicId.from_str(
                    "default_author/component:0.2.0:QmYAXgX8ARiriupMQsbGXtKdDyGzWry1YV3sycKw1qqmgH"
                ),
                dest_path,
            )
            assert package_path == Path(dest_path).absolute()
