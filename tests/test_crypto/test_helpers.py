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
from pathlib import Path
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
    verify_or_create_private_keys,
)

from tests.conftest import (
    COSMOS_PRIVATE_KEY_FILE,
    CUR_PATH,
    ETHEREUM_PRIVATE_KEY_FILE,
    ETHEREUM_PRIVATE_KEY_PATH,
    FETCHAI_PRIVATE_KEY_PATH,
)


logger = logging.getLogger(__name__)


class ResponseMock:
    """Mock for response class."""

    text = "some text"

    def __init__(self, status_code=200):
        """Initialise response mock."""
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

    def tests_generate_wealth_ethereum_fail_no_url(self, caplog):
        """Test generate wealth for ethereum."""
        address = "my_address"
        with caplog.at_level(
            logging.DEBUG, logger="aea.crypto.ethereum._default_logger"
        ):
            try_generate_testnet_wealth(
                identifier=EthereumCrypto.identifier, address=address
            )
            assert (
                "Url is none, no default url provided. Please provide a faucet url."
                in caplog.text
            )

    def tests_generate_wealth_ethereum_fail_invalid_url(self, caplog):
        """Test generate wealth for ethereum."""
        address = "my_address"
        result = ResponseMock(status_code=500)
        with patch.object(requests, "get", return_value=result):
            with caplog.at_level(
                logging.DEBUG, logger="aea.crypto.ethereum._default_logger"
            ):
                try_generate_testnet_wealth(
                    identifier=EthereumCrypto.identifier,
                    address=address,
                    url="wrong_url",
                )
                assert "Response: 500" in caplog.text

    def tests_generate_wealth_ethereum_fail_valid_url(self, caplog):
        """Test generate wealth for ethereum."""
        address = "my_address"
        result = ResponseMock(status_code=200)
        with patch.object(requests, "get", return_value=result):
            with caplog.at_level(
                logging.DEBUG, logger="aea.crypto.ethereum._default_logger"
            ):
                try_generate_testnet_wealth(
                    identifier=EthereumCrypto.identifier,
                    address=address,
                    url="correct_url",
                )

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
        create_private_key(EthereumCrypto.identifier, ETHEREUM_PRIVATE_KEY_FILE)

    @patch("builtins.open", mock_open())
    def test__create_cosmos_private_key_positive(self, *mocks):
        """Test _create_cosmos_private_key positive result."""
        create_private_key(CosmosCrypto.identifier, COSMOS_PRIVATE_KEY_FILE)

    @patch("aea.crypto.helpers.create_private_key")
    @patch("aea.crypto.helpers.try_validate_private_key_path")
    def test_verify_or_create_private_keys(self, *mocks):
        """Test _create_ethereum_private_key positive result."""
        verify_or_create_private_keys(Path(os.path.join(CUR_PATH, "data", "dummy_aea")))
