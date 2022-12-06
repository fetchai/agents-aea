# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Test for hashfunc utility module."""
from aea_ledger_fetchai.hashfuncs import ripemd160, sha256


def test_sha256():
    """Test sha256."""
    data = b"some test data"
    precalculated = "f70c5e847d0ea29088216d81d628df4b4f68f3ccabb2e4031c09cc4d129ae216"
    assert sha256(data).hex() == precalculated


def test_ripemd160():
    """Test ripemd160."""
    data = b"some test data"
    precalculated = "b2067369354e52a1e1b5627a49549229992f4b0d"
    assert ripemd160(data).hex() == precalculated
