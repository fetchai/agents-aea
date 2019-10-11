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
from pathlib import Path
from typing import cast, Optional

from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE
from aea.crypto.base import Crypto
from aea.crypto.fetchai_base import FetchCrypto
from aea.crypto.ethereum_base import EthCrypto
from aea.crypto.helpers import _try_validate_private_key_pem_path, _create_temporary_private_key_pem_path
from aea.configurations.loader import ConfigLoader


class Wallet(object):
    """Store all the public keys we initialise."""

    def __init__(self):
        """Instantiate a wallet object."""
        path = Path(DEFAULT_AEA_CONFIG_FILE)
        self.agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
        fp = open(str(path), mode="r", encoding="utf-8")
        self.aea_conf = self.agent_loader.load(fp)

        self.crypto_objects = {
            "default": self._setup_crypto(self.aea_conf.private_key_paths['default']),
            "fetch": self._setup_fetch_crypto(self.aea_conf.private_key_paths['fetchai']),
            "ethereum": self._setup_ethereum_crypto(self.aea_conf.private_key_paths['ethereum'])
        }

        self._public_keys = {
            "default": self.crypto_objects['default'].public_key,
            "fetch": self.crypto_objects['fetch'].public_key,
            "ethereum": self.crypto_objects['ethereum'].public_key
        }

        self._update_config()

    def _update_config(self):
        path = Path(DEFAULT_AEA_CONFIG_FILE)
        fp = open(str(path), mode="w", encoding="utf-8")
        self.agent_loader.dump(self.aea_conf, fp)

    def _setup_crypto(self, private_key_path: Optional[str] = None):
        """Create the crypto object."""
        private_key_pem_path = cast(str, private_key_path)
        if private_key_path == "" or private_key_path is None:
            private_key_pem_path = _create_temporary_private_key_pem_path()
        else:
            _try_validate_private_key_pem_path(private_key_pem_path)
        self.aea_conf.private_key_paths['default'] = private_key_pem_path
        crypto = Crypto(private_key_pem_path=private_key_pem_path)
        return crypto

    def _setup_fetch_crypto(self, private_key_path: Optional[str] = None):
        """Create the fetch.ai entity."""
        if private_key_path == "" or private_key_path is None:
            private_key_path = "fet_pk.txt"
        self.aea_conf.private_key_paths['fetch'] = private_key_path
        fetch_crypto = FetchCrypto(private_key_path)
        return fetch_crypto

    def _setup_ethereum_crypto(self, private_key_path: Optional[str] = None):
        """Create an ethereum account."""
        if private_key_path == "" or private_key_path is None:
            private_key_path = "eth_pk.txt"
        self.aea_conf.private_key_paths['ethereum'] = private_key_path
        ethereum_crypto = EthCrypto(private_key_path)
        return ethereum_crypto

    @property
    def public_keys(self):
        """Get the public_key dictionary."""
        return self._public_keys

    @property
    def crypto_object(self):
        """Get the crypto_objects (key pair)."""
        return self.crypto_objects
