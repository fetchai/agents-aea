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

"""Test protocol helpers."""

from pathlib import Path

import pytest
import yaml

from aea.configurations.base import PublicId
from aea.helpers.protocols import (
    get_protocol_specification_from_readme,
    get_protocol_specification_id_from_specification,
)


@pytest.mark.parametrize("protocol_yaml_path", Path("packages").rglob("protocol.yaml"))
def test_get_protocol_specification_from_readme(protocol_yaml_path):
    """Test get_protocol_specification_from_readme"""

    spec = get_protocol_specification_from_readme(protocol_yaml_path.parent)
    assert all(yaml.safe_load_all(spec))
    spec_id = get_protocol_specification_id_from_specification(spec)
    assert PublicId.from_str(spec_id)
