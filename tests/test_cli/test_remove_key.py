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
"""This test module contains the tests for the `aea remove-key` sub-command."""
import pytest
from click.exceptions import ClickException

from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import FETCHAI_PRIVATE_KEY_PATH


class BaseTestRemovePrivateKey(AEATestCaseEmpty):
    """Base test class on removing private keys."""

    WITH_CONNECTION: bool

    @classmethod
    def setup_class(cls):
        """Set up class."""
        super().setup_class()
        cls.add_private_key(
            private_key_filepath=FETCHAI_PRIVATE_KEY_PATH,
            connection=cls.WITH_CONNECTION,
        )

    def test_remove(self):
        """Test remove."""
        result = self.remove_private_key(connection=self.WITH_CONNECTION)
        assert result.exit_code == 0


class TestRemoveCryptoPrivateKey(BaseTestRemovePrivateKey):
    """Test removing a crypto private key."""

    WITH_CONNECTION = False


class TestRemoveConnectionPrivateKey(BaseTestRemovePrivateKey):
    """Test removing a connection private key."""

    WITH_CONNECTION = True


class BaseTestRemovePrivateKeyNegative(AEATestCaseEmpty):
    """Base test class on removing private keys, when key is not present"""

    WITH_CONNECTION: bool
    EXPECTED_ERROR_MSG: str

    def test_remove(self):
        """Test remove."""
        with pytest.raises(ClickException, match=self.EXPECTED_ERROR_MSG):
            self.remove_private_key(connection=self.WITH_CONNECTION)


class TestRemoveCryptoPrivateKeyNegative(BaseTestRemovePrivateKeyNegative):
    """Test removing a crypto private key."""

    WITH_CONNECTION = False
    EXPECTED_ERROR_MSG = "There is no key registered with id fetchai."


class TestRemoveConnectionPrivateKeyNegative(BaseTestRemovePrivateKeyNegative):
    """Test removing a connection private key."""

    WITH_CONNECTION = True
    EXPECTED_ERROR_MSG = "There is no connection key registered with id fetchai."
