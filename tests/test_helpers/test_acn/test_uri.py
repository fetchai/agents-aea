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
"""This module contains the tests for acn helper module."""

from aea.helpers.acn.uri import Uri


def test_uri():
    """Test URI class"""
    Uri(uri="localhost:9000")
    uri = Uri(host="localhost", port=9000)
    assert str(uri) == "localhost:9000"
    assert uri.host == "localhost"
    assert uri.port == 9000
    Uri()


def test_uri2():
    """Test the uri."""
    Uri(host="127.0.0.1")
    uri = Uri(host="127.0.0.1", port=10000)
    assert str(uri) == "127.0.0.1:10000"
    assert uri.host == "127.0.0.1"
    assert uri.port == 10000
