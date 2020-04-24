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

"""Test that the documentation of the ledger integration (ledger-integration.md) is consistent."""

from pathlib import Path

import mistune

import pytest

from tests.conftest import ROOT_DIR


class TestLedgerIntegrationDocs:
    """
    Test that all the code blocks in the docs (ledger-integration.md)
    are present in the aea.crypto.* modules.
    """

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())

        ledger_doc_file = Path(ROOT_DIR, "docs", "ledger-integration.md")
        doc = markdown_parser(ledger_doc_file.read_text())
        # get only code blocks
        cls.code_blocks = list(filter(lambda x: x["type"] == "block_code", doc))

    def test_ledger_api_baseclass(self):
        """Test the section on LedgerApis interface."""
        offset = 0
        expected_code_path = Path(ROOT_DIR, "aea", "crypto", "base.py",)
        expected_code = expected_code_path.read_text()

        # all code blocks must be present in the expected code
        for code_block in self.code_blocks[offset : offset + 5]:
            text = code_block["text"]
            if text.strip() not in expected_code:
                pytest.fail(
                    "The following code cannot be found in {}:\n{}".format(
                        expected_code_path, text
                    )
                )

    def test_fetchai_ledger_docs(self):
        """Test the section on FetchAIApi interface."""
        offset = 5
        expected_code_path = Path(ROOT_DIR, "aea", "crypto", "fetchai.py",)
        expected_code = expected_code_path.read_text()

        # all code blocks re. Fetchai must be present in the expected code
        # the second-to-last is on FetchAiApi.generate_tx_nonce
        all_blocks = self.code_blocks[offset : offset + 3] + [self.code_blocks[-2]]
        for code_block in all_blocks:
            text = code_block["text"]
            if text.strip() not in expected_code:
                pytest.fail(
                    "The following code cannot be found in {}:\n{}".format(
                        expected_code_path, text
                    )
                )

    def test_ethereum_ledger_docs(self):
        """Test the section on EthereumApi interface."""
        offset = 8
        expected_code_path = Path(ROOT_DIR, "aea", "crypto", "ethereum.py",)
        expected_code = expected_code_path.read_text()

        # all code blocks re. Fetchai must be present in the expected code
        # the last is on EthereumApi.generate_tx_nonce
        all_blocks = self.code_blocks[offset : offset + 3] + [self.code_blocks[-1]]
        for code_block in all_blocks:
            text = code_block["text"]
            if text.strip() not in expected_code:
                pytest.fail(
                    "The following code cannot be found in {}:\n{}".format(
                        expected_code_path, text
                    )
                )
