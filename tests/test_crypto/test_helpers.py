
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

"""This module contains the tests for the crypto/helpers module."""

import logging
import os

import pytest

from aea.crypto.helpers import (
    _try_validate_ethereum_private_key_path,
    _try_validate_fet_private_key_path,
    _try_validate_private_key_pem_path
)

from ..conftest import CUR_PATH


logger = logging.getLogger(__name__)


class TestHelperFile:
    """Test helper module in aea/crypto."""

    def tests_private_keys(self):
        """Test the private keys."""
        private_key_path = os.path.join(CUR_PATH, "data", "priv.pem")
        _try_validate_private_key_pem_path(private_key_path)
        with pytest.raises(SystemExit):
            private_key_path = os.path.join(CUR_PATH, "data", "priv_wrong.pem")
            _try_validate_private_key_pem_path(private_key_path)

        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        _try_validate_fet_private_key_path(private_key_path)
        with pytest.raises(SystemExit):
            private_key_path = os.path.join(CUR_PATH, "data", "priv_wrong.pem")
            _try_validate_fet_private_key_path(private_key_path)

        private_key_path = os.path.join(CUR_PATH, "data", "eth_private_key.txt")
        _try_validate_ethereum_private_key_path(private_key_path)
        with pytest.raises(SystemExit):
            private_key_path = os.path.join(CUR_PATH, "data", "priv_wrong.pem")
            _try_validate_ethereum_private_key_path(private_key_path)
