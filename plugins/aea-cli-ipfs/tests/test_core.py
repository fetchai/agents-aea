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

"""Test ipfs core."""

from unittest import mock

from aea_cli_ipfs.core import _get_path_data, register_package


def test_get_path_data() -> None:
    """Test Get path data."""
    with mock.patch(
        "aea_cli_ipfs.core.glob",
        return_value=["./packages/valory/connection/some/connection.yaml"],
    ):
        assert _get_path_data("./packages/") == (
            "./packages/valory/connection/some",
            "connection",
        )


def test_register_package() -> None:
    """Test register package."""
    with mock.patch(
        "aea_cli_ipfs.core.register_item_to_local_registry"
    ) as register_mock, mock.patch(
        "aea_cli_ipfs.core.glob",
        return_value=["./packages/valory/connection/some/connection.yaml"],
    ), mock.patch(
        "aea_cli_ipfs.core.load_item_config"
    ):
        ipfs_tool_mock = mock.Mock()
        ipfs_tool_mock.add = mock.Mock(
            return_value=(
                "some_name",
                "QmcRD4wkPPi6dig81r5sLj9Zm1gDCL4zgpEj9CfuRrGbzF",
                None,
            )
        )

        assert (
            register_package(ipfs_tool_mock, "some_dir", no_pin=True)
            == "bafybeigrf2dwtpjkiovnigysyto3d55opf6qkdikx6d65onrqnfzwgdkfa"
        )

        register_mock.assert_called_once_with(
            item_type="connection",
            public_id=mock.ANY,
            package_hash="bafybeigrf2dwtpjkiovnigysyto3d55opf6qkdikx6d65onrqnfzwgdkfa",
        )
