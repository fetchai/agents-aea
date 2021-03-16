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
"""This module contains the tests for MultiAddr helper class."""


import tempfile
from shutil import rmtree

import pytest

from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.registries import make_crypto
from aea.helpers.multiaddr.base import MultiAddr


HOST = "127.0.0.1"
PORT = 13000

PRIV_KEY = "b6dbe68a5b9bc135a3736a9b59892b6c806bf7594092de441f43e6d8609ea5fd"
PEER_ID = "16Uiu2HAkw1VyY3RkiuMy38XKjb6w9EhbtXfwHkRpbQzNvXYVkG1T"


def test_multiaddr_consistency():
    """Test multiaddress consistency."""
    key = make_crypto(DEFAULT_LEDGER)
    maddr1 = MultiAddr(HOST, PORT, key.public_key)

    tmpdir = tempfile.mkdtemp()
    key_file = tmpdir + "/key"
    key.dump(key_file)

    key2 = make_crypto(DEFAULT_LEDGER, private_key_path=key_file)
    maddr2 = MultiAddr(HOST, PORT, key2.public_key)

    rmtree(tmpdir)

    assert str(maddr1) == str(maddr2)
    assert maddr1.public_key == maddr2.public_key
    assert maddr1.peer_id == maddr2.peer_id


def test_multiaddr_correctness():
    """Test multiaddress correctness."""
    tmpdir = tempfile.mkdtemp()
    key_file = tmpdir + "/key"
    with open(key_file, "w+") as k:
        k.write(PRIV_KEY)

    key = make_crypto(DEFAULT_LEDGER, private_key_path=key_file)
    maddr = MultiAddr(HOST, PORT, key.public_key)

    rmtree(tmpdir)

    assert maddr._peerid == PEER_ID


def test_multiaddr_from_string():
    """Test multiaddress from string"""
    maddr_str = "/dns4/" + HOST + "/tcp/" + str(PORT) + "/p2p/"
    maddr = MultiAddr.from_string(maddr_str + PEER_ID)
    assert maddr.host == HOST and maddr.port == PORT and maddr.peer_id == PEER_ID

    with pytest.raises(ValueError):
        MultiAddr.from_string("")

    with pytest.raises(ValueError):
        MultiAddr.from_string(maddr_str + "wrong-peer-id")
