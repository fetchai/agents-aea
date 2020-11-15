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

"""This test module contains the tests configuration utils."""
from unittest.mock import MagicMock

from aea.configurations.base import ComponentId, ComponentType, PublicId
from aea.configurations.utils import get_latest_component_id_from_prefix


def test_get_latest_component_id_from_prefix():
    """Test the utility to get the latest concrete version id."""
    agent_config = MagicMock()
    expected_component_id = ComponentId(
        ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
    )
    agent_config.package_dependencies = {expected_component_id}

    result = get_latest_component_id_from_prefix(
        agent_config, expected_component_id.component_prefix
    )
    assert result == expected_component_id


def test_get_latest_component_id_from_prefix_negative():
    """Test the utility to get the latest concrete version id, negative case."""
    agent_config = MagicMock()
    agent_config.package_dependencies = {}

    result = get_latest_component_id_from_prefix(
        agent_config, (ComponentType.PROTOCOL, "author", "name")
    )
    assert result is None
