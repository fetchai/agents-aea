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
from unittest.mock import mock_open, patch

import pytest

import requests

from aea.crypto.cosmos import COSMOS
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import (
    _try_generate_testnet_wealth,
    _try_validate_private_key_path,
    create_private_key,
)

from ..conftest import CUR_PATH


logger = logging.getLogger(__name__)


class ResponseMock:
    text = "some text"

    def __init__(self, status_code=200):
        self.status_code = status_code


class TestHelperFile:
    """Test helper module in aea/crypto."""

    def tests_private_keys(self):
        """Test the private keys."""
        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        _try_validate_private_key_path(FETCHAI, private_key_path)
        with pytest.raises(SystemExit):
            private_key_path = os.path.join(
                CUR_PATH, "data", "fet_private_key_wrong.txt"
            )
            _try_validate_private_key_path(FETCHAI, private_key_path)

        private_key_path = os.path.join(CUR_PATH, "data", "eth_private_key.txt")
        _try_validate_private_key_path(ETHEREUM, private_key_path)
        with pytest.raises(SystemExit):
            private_key_path = os.path.join(
                CUR_PATH, "data", "fet_private_key_wrong.txt"
            )
            _try_validate_private_key_path(ETHEREUM, private_key_path)

    @patch("aea.crypto.helpers.logger")
    def tests_generate_wealth_fetchai(self, mock_logging):
        """Test generate wealth for fetchai."""
        address = "my_address"
        result = ResponseMock(status_code=500)
        with patch.object(requests, "post", return_value=result):
            _try_generate_testnet_wealth(identifier=FETCHAI, address=address)
            assert mock_logging.error.called

        result.status_code = 200
        with pytest.raises(SystemExit):
            with patch.object(requests, "post", return_value=result):
                _try_generate_testnet_wealth(identifier=FETCHAI, address=address)

    @patch("aea.crypto.helpers.logger")
    def tests_generate_wealth_ethereum(self, mock_logging):
        """Test generate wealth for ethereum."""
        address = "my_address"
        result = ResponseMock(status_code=500)
        with patch.object(requests, "get", return_value=result):
            _try_generate_testnet_wealth(identifier=ETHEREUM, address=address)
            assert mock_logging.error.called

        result.status_code = 200
        with pytest.raises(SystemExit):
            with patch.object(requests, "get", return_value=result):
                _try_generate_testnet_wealth(identifier=ETHEREUM, address=address)

    @patch("aea.crypto.helpers.requests.post", return_value=ResponseMock())
    @patch("aea.crypto.helpers.json.loads", return_value={"error_message": ""})
    def test__try_generate_testnet_wealth_error_resp(self, *mocks):
        """Test _try_generate_testnet_wealth error_resp."""
        _try_generate_testnet_wealth(FETCHAI, "address")
        _try_generate_testnet_wealth(ETHEREUM, "address")

    @patch("builtins.open", mock_open())
    def test__try_validate_private_key_path_positive(self, *mocks):
        """Test _validate_private_key_path positive result."""
        _try_validate_private_key_path(FETCHAI, "path")
        _try_validate_private_key_path(ETHEREUM, "path")

    @patch("builtins.open", mock_open())
    def test__create_ethereum_private_key_positive(self, *mocks):
        """Test _create_ethereum_private_key positive result."""
        create_private_key(ETHEREUM)

    @patch("builtins.open", mock_open())
    def test__create_cosmos_private_key_positive(self, *mocks):
        """Test _create_cosmos_private_key positive result."""
        create_private_key(COSMOS)
