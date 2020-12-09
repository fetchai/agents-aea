# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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

"""Test P2PLibp2p connection build."""
from unittest import mock

import pytest

from aea.exceptions import AEAException

from packages.fetchai.connections.p2p_libp2p.check_dependencies import main


def test_build_script():
    """Test the build script - positive case."""
    main()


def test_build_script_negative_binary_not_found():
    """Test the build script - negative case, binary not found."""
    with mock.patch("shutil.which", return_value=None):
        with pytest.raises(
            AEAException,
            match="'go' is required by the libp2p connection, but it is not installed, or it is not accessible from the system path.",
        ):
            main()


def test_build_script_negative_version_too_low():
    """Test the build script - negative case, version too low."""
    with mock.patch(
        "packages.fetchai.connections.p2p_libp2p.check_dependencies.get_version",
        return_value=(0, 0, 0),
    ):
        with pytest.raises(
            AEAException,
            match="The installed version of 'go' is too low: expected at least 1.14.0; found 0.0.0.",
        ):
            main()
