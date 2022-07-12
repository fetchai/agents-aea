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

from aea.configurations.constants import SIGNING_PROTOCOL_WITH_HASH
from aea.configurations.data_types import PublicId
from aea.helpers.io import from_csv

from tests.conftest import ROOT_DIR


def test_signing_protocol_hash() -> None:
    """Test signing protocol"""

    public_id = PublicId.from_str(SIGNING_PROTOCOL_WITH_HASH)
    hashes = from_csv(Path(ROOT_DIR, "packages", "hashes.csv"))
    assert public_id.hash == hashes["open_aea/protocols/signing"]
