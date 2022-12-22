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

"""Test test_tools."""

from unittest.mock import patch

import pytest
from _pytest.compat import get_real_func
from aea_cli_ipfs.test_tools.fixture_helpers import ipfs_daemon


def test_daemon_fixture() -> None:
    """Test ipfs daemon fixture."""
    with patch("aea_cli_ipfs.ipfs_utils.IPFSDaemon.start") as start_mock, patch(
        "aea_cli_ipfs.ipfs_utils.IPFSDaemon.stop"
    ) as stop_mock:
        gen = get_real_func(ipfs_daemon)()

        assert next(gen) is False
        with pytest.raises(StopIteration):
            next(gen)
        start_mock.assert_called_once()
        stop_mock.assert_called_once()
