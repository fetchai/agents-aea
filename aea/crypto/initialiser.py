# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Module wrapping all the public and private keys cryptography."""

from typing import cast, Optional

from aea.crypto.base import Crypto
from aea.crypto.fetchai_base import FetchCrypto
from aea.crypto.helpers import _try_validate_private_key_pem_path, _create_temporary_private_key_pem_path


class Wallet(object):
    """Store all the public keys we initialise."""

    def __init__(self, private_key_pem_path: Optional[str] = None):
        """Instantiate a wallet object."""
        self.crypto_objects = {
            "default": self._setup_crypto(private_key_pem_path),
            "fetchai": self._setup_fetch_crypto()
        }

        self.public_keys = {
            "default": self.crypto_objects['default'].public_key,
            "fetchai": self.crypto_objects['fetchai'].public_key
        }

        self.private_key_pem_path = ""


    def _setup_crypto(self, private_key_pem_path: Optional[str] = None):
        """Create the crypto object."""
        private_key_pem_path = cast(str, private_key_pem_path)
        if private_key_pem_path == "":
            private_key_pem_path = _create_temporary_private_key_pem_path()
        else:
            _try_validate_private_key_pem_path(private_key_pem_path)
        self.private_key_pem_path = private_key_pem_path
        crypto = Crypto(private_key_pem_path=private_key_pem_path)
        return crypto

    def _setup_fetch_crypto(self):
        """Create the fetch.ai entity."""
        fetch_crypto = FetchCrypto("pk.txt")
        return fetch_crypto

    @property
    def public_key(self):
        """Get the public_key dictionary."""
        return self.public_keys

    @property
    def crypto_object(self):
        """Get the crypto_objects (key pair)."""
        return self.crypto_objects
