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
"""This test module contains the tests for the private key password support."""
from pathlib import Path

import pytest
from click.exceptions import ClickException

from aea.helpers.base import cd
from aea.test_tools.test_cases import AEATestCaseEmpty


class TestKeyEncryption(AEATestCaseEmpty):
    """Test that the command 'aea generate-key' works as expected."""

    @pytest.mark.parametrize("ledger_name", ["fetchai", "ethereum", "cosmos"])
    def test_crypto_plugin(self, ledger_name):
        """Test that the fetch private key is created correctly."""
        with cd(self._get_cwd()):
            plain_file_name = Path(f"{ledger_name}_key")
            encrypted_file_name = Path(f"{ledger_name}_key_encrypted")
            password = "somePwd"  # nosec
            self.invoke("generate-key", ledger_name, str(plain_file_name))
            assert plain_file_name.exists()

            self.invoke(
                "generate-key",
                ledger_name,
                str(encrypted_file_name),
                "--password",
                password,
            )
            assert encrypted_file_name.exists()
            assert len(encrypted_file_name.read_bytes()) != len(
                plain_file_name.read_bytes()
            )

            with pytest.raises(ClickException, match="Error on key.*load.*password"):
                self.invoke("add-key", ledger_name, str(encrypted_file_name))

            with pytest.raises(ClickException, match="Decrypt error! Bad password?"):
                self.invoke(
                    "add-key",
                    ledger_name,
                    str(encrypted_file_name),
                    "--password",
                    "incorrectpassword",
                )
            r = self.invoke(
                "add-key",
                ledger_name,
                str(encrypted_file_name),
                "--password",
                password,
            )
            assert r.exit_code == 0

            r = self.invoke("get-address", ledger_name, "--password", password,)
            assert r.exit_code == 0
