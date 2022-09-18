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

"""Test if constants are valid."""


from pathlib import Path

from aea.cli.packages import PackageManager
from aea.configurations.constants import PACKAGES, SIGNING_PROTOCOL_WITH_HASH
from aea.configurations.data_types import PackageId, PackageType, PublicId

from tests.conftest import ROOT_DIR


def test_signing_protocol_hash() -> None:
    """Test signing protocol"""

    package_manager = PackageManager.from_dir(Path(ROOT_DIR, PACKAGES))
    public_id = PublicId.from_str(SIGNING_PROTOCOL_WITH_HASH)
    package_id = PackageId(PackageType.PROTOCOL, public_id)

    assert public_id.hash == package_manager.packages[package_id]
