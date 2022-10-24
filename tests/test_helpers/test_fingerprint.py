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

"""Tests for fingerprinting packages."""

from pathlib import Path

from tests.conftest import PACKAGES_DIR
from aea.helpers.cid import CID
from aea.helpers.fingerprint import compute_fingerprint


def test_compute_fingerprint():
    """ Test compute_fingerprint"""

    ignore_pattern = '__init__.py'
    package_path = Path(PACKAGES_DIR)
    fingerprints = compute_fingerprint(package_path, fingerprint_ignore_patterns=None)
    assert all(map(lambda multihash: CID.is_cid(multihash), fingerprints.values()))

    n_fingerprints_without_ignore = len(fingerprints)
    n_init_dot_py = sum(p.endswith(ignore_pattern) for p in fingerprints)
    fingerprints = compute_fingerprint(package_path, (ignore_pattern, ))
    assert len(fingerprints) + n_init_dot_py == n_fingerprints_without_ignore
    assert all(map(lambda multihash: CID.is_cid(multihash), fingerprints.values()))
