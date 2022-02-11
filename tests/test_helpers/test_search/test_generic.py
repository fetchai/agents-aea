# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This module contains the tests for the helpers.search.generic."""

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.generic import GenericDataModel


def test_generic_data_model():
    """Test generic data model creation."""
    # ok
    GenericDataModel(
        "test", {"attr1": {"name": "attr1", "type": "str", "is_required": True}}
    )

    # bad type
    with pytest.raises(AEAEnforceError):
        GenericDataModel(
            "test",
            {"attr1": {"name": "attr1", "type": "bad type", "is_required": True}},
        )

    # bad name
    with pytest.raises(AEAEnforceError):
        GenericDataModel(
            "test", {"attr1": {"name": 1231, "type": "str", "is_required": True}}
        )

    # bad is required
    with pytest.raises(AEAEnforceError):
        GenericDataModel(
            "test", {"attr1": {"name": "attr1", "type": "str", "is_required": "True"}}
        )
