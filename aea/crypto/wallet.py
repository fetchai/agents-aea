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

"""Module wrapping all the public and private keys cryptography."""

from typing import Dict, cast

import aea.crypto
from aea.crypto.base import Crypto
from aea.crypto.cosmos import COSMOS
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI

SUPPORTED_CRYPTOS = [COSMOS, ETHEREUM, FETCHAI]


class Wallet:
    """Store all the cryptos we initialise."""

    def __init__(self, private_key_paths: Dict[str, str]):
        """
        Instantiate a wallet object.

        :param private_key_paths: the private key paths
        """
        crypto_objects = {}  # type: Dict[str, Crypto]
        public_keys = {}  # type: Dict[str, str]
        addresses = {}  # type: Dict[str, str]

        for identifier, path in private_key_paths.items():
            crypto = aea.crypto.make(identifier, private_key_path=path)
            crypto_objects[identifier] = crypto
            public_keys[identifier] = cast(str, crypto.public_key)
            addresses[identifier] = cast(str, crypto.address)

        self._crypto_objects = crypto_objects
        self._public_keys = public_keys
        self._addresses = addresses

    @property
    def public_keys(self):
        """Get the public_key dictionary."""
        return self._public_keys

    @property
    def crypto_objects(self):
        """Get the crypto objects (key pair)."""
        return self._crypto_objects

    @property
    def addresses(self) -> Dict[str, str]:
        """Get the crypto addresses."""
        return self._addresses
