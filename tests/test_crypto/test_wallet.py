
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

"""This module contains the tests of the ethereum module."""
import os
import unittest

from aea.crypto.wallet import Wallet
from ..conftest import CUR_PATH


class WalletTest(unittest.TestCase):
    """Wallet test class."""

    def test_initialisation_with_wrong_identifier(self):
        """Test the initialisation of the the fet crypto."""
        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        with self.assertRaises(Exception) as context:
            Wallet({'default': private_key_pem_path, 'not_an_identifier': ''})
            unittest.TestCase.assertTrue('This is broken' in context.exception)
