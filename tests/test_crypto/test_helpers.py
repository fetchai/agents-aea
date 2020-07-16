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

from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import (
    create_private_key,
    try_generate_testnet_wealth,
    try_validate_private_key_path,
)

from tests.conftest import CUR_PATH, ETHEREUM_PRIVATE_KEY_PATH, FETCHAI_PRIVATE_KEY_PATH

logger = logging.getLogger(__name__)


class ResponseMock:
    text = "some text"

    def __init__(self, status_code=200):
        self.status_code = status_code


class TestHelperFile:
    """Test helper module in aea/crypto."""

    def tests_private_keys(self):
        """Test the private keys."""
        try_validate_private_key_path(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_PATH
        )
        with pytest.raises(SystemExit):
            private_key_path = os.path.join(
                CUR_PATH, "data", "fet_private_key_wrong.txt"
            )
            try_validate_private_key_path(FetchAICrypto.identifier, private_key_path)

        try_validate_private_key_path(
            EthereumCrypto.identifier, ETHEREUM_PRIVATE_KEY_PATH
        )
        with pytest.raises(SystemExit):
            private_key_path = os.path.join(
                CUR_PATH, "data", "fet_private_key_wrong.txt"
            )
            try_validate_private_key_path(EthereumCrypto.identifier, private_key_path)

    @patch("aea.crypto.fetchai.logger")
    def tests_generate_wealth_fetchai(self, mock_logging):
        """Test generate wealth for fetchai."""
        address = "my_address"
        result = ResponseMock(status_code=500)
        with patch.object(requests, "post", return_value=result):
            try_generate_testnet_wealth(
                identifier=FetchAICrypto.identifier, address=address
            )
            assert mock_logging.error.called

        result.status_code = 200
        with patch.object(requests, "post", return_value=result):
            try_generate_testnet_wealth(
                identifier=FetchAICrypto.identifier, address=address
            )

    @patch("aea.crypto.ethereum.logger")
    def tests_generate_wealth_ethereum(self, mock_logging):
        """Test generate wealth for ethereum."""
        address = "my_address"
        result = ResponseMock(status_code=500)
        with patch.object(requests, "get", return_value=result):
            try_generate_testnet_wealth(
                identifier=EthereumCrypto.identifier, address=address
            )
            assert mock_logging.error.called

        result.status_code = 200
        with patch.object(requests, "get", return_value=result):
            try_generate_testnet_wealth(
                identifier=EthereumCrypto.identifier, address=address
            )

    @patch("aea.crypto.fetchai.requests.post", return_value=ResponseMock())
    @patch("aea.crypto.fetchai.json.loads", return_value={"error_message": ""})
    def test_try_generate_testnet_wealth_error_resp_fetchai(self, *mocks):
        """Test try_generate_testnet_wealth error_resp."""
        try_generate_testnet_wealth(FetchAICrypto.identifier, "address")

    @patch("aea.crypto.ethereum.requests.post", return_value=ResponseMock())
    @patch("aea.crypto.ethereum.json.loads", return_value={"error_message": ""})
    def test_try_generate_testnet_wealth_error_resp_ethereum(self, *mocks):
        """Test try_generate_testnet_wealth error_resp."""
        try_generate_testnet_wealth(EthereumCrypto.identifier, "address")

    def test_try_validate_private_key_path_positive(self):
        """Test _validate_private_key_path positive result."""
        try_validate_private_key_path(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_PATH
        )
        try_validate_private_key_path(
            EthereumCrypto.identifier, ETHEREUM_PRIVATE_KEY_PATH
        )

    @patch("builtins.open", mock_open())
    def test__create_ethereum_private_key_positive(self, *mocks):
        """Test _create_ethereum_private_key positive result."""
        create_private_key(EthereumCrypto.identifier)

    @patch("builtins.open", mock_open())
    def test__create_cosmos_private_key_positive(self, *mocks):
        """Test _create_cosmos_private_key positive result."""
        create_private_key(CosmosCrypto.identifier)
