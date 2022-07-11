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

"""Test ipfs utils."""

from aea_cli_ipfs.ipfs_utils import IPFSTool

from aea.cli.registry.settings import DEFAULT_IPFS_URL, DEFAULT_IPFS_URL_LOCAL


def test_init_tool() -> None:
    """Test tool initialization."""

    tool = IPFSTool(DEFAULT_IPFS_URL)
    assert tool.is_remote is True

    tool = IPFSTool(DEFAULT_IPFS_URL_LOCAL)
    assert tool.is_remote is False
