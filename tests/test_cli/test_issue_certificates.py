# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This test module contains tests for 'issue-certificates' command."""
import json
import os
import shutil
from pathlib import Path
from typing import List

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.test_tools.constants import ETHEREUM_PRIVATE_KEY_FILE
from aea_ledger_fetchai import FetchAICrypto
from aea_ledger_fetchai.test_tools.constants import FETCHAI_PRIVATE_KEY_FILE

from aea.cli.utils.config import dump_item_config
from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.helpers.base import CertRequest
from aea.test_tools.test_cases import AEATestCaseEmpty, _get_password_option_args

from tests.conftest import CUR_PATH
from tests.data.dummy_connection.connection import DummyConnection


NOT_BEFORE = "2022-01-01"
NOT_AFTER = "2023-01-01"


class BaseTestIssueCertificates(AEATestCaseEmpty):
    """Base test class for 'aea issue-certificates' tests."""

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()

        # add dummy connection
        shutil.copytree(
            os.path.join(CUR_PATH, "data", "dummy_connection"),
            os.path.join(cls.current_agent_context, "connections", "dummy"),
        )
        agent_config = cls.load_agent_config(cls.agent_name)
        agent_config.author = FetchAICrypto.identifier
        agent_config.connections.add(DummyConnection.connection_id)
        dump_item_config(agent_config, Path(cls.current_agent_context))

    @classmethod
    def add_cert_requests(cls, cert_requests: List[CertRequest], connection_name: str):
        """Add certificate requests to a target connection."""
        cls.nested_set_config(
            f"connections.{connection_name}.cert_requests", cert_requests
        )


class TestIssueCertificatesPositive(BaseTestIssueCertificates):
    """Test 'issue-certificates', positive case."""

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()

        cls.expected_path_1 = os.path.abspath("path_1")
        cls.expected_path_2 = os.path.abspath("path_2")
        cls.cert_id_1 = "cert_id_1"
        cls.cert_id_2 = "cert_id_2"
        cls.cert_request_1 = CertRequest(
            identifier=cls.cert_id_1,
            ledger_id=FetchAICrypto.identifier,
            not_before=NOT_BEFORE,
            not_after=NOT_AFTER,
            public_key=FetchAICrypto.identifier,
            message_format="{public_key}",
            save_path=cls.expected_path_1,
        )
        cls.cert_request_2 = CertRequest(
            identifier=cls.cert_id_2,
            ledger_id=FetchAICrypto.identifier,
            not_before=NOT_BEFORE,
            not_after=NOT_AFTER,
            public_key="0xABCDEF123456",
            message_format="{public_key}",
            save_path=cls.expected_path_2,
        )
        cls.add_cert_requests(
            [cls.cert_request_1, cls.cert_request_2], DummyConnection.connection_id.name
        )

    def test_issue_certificate(self, password_or_none):
        """Test 'aea issue-certificates' in case of success."""
        # setup: add private key with password
        self.generate_private_key(
            ledger_api_id=FetchAICrypto.identifier, password=password_or_none
        )
        self.add_private_key(
            ledger_api_id=FetchAICrypto.identifier,
            private_key_filepath=PRIVATE_KEY_PATH_SCHEMA.format(
                FetchAICrypto.identifier
            ),
            password=password_or_none,
        )
        self.add_private_key(
            ledger_api_id=FetchAICrypto.identifier,
            private_key_filepath=PRIVATE_KEY_PATH_SCHEMA.format(
                FetchAICrypto.identifier
            ),
            connection=True,
            password=password_or_none,
        )

        # issue certificates and check
        password_options = _get_password_option_args(password_or_none)
        result = self.run_cli_command(
            "issue-certificates", *password_options, cwd=self._get_cwd()
        )
        self._check_signature(self.cert_id_1, self.expected_path_1, result.stdout)
        self._check_signature(self.cert_id_2, self.expected_path_2, result.stdout)

        # teardown: remove private key
        Path(self._get_cwd(), FETCHAI_PRIVATE_KEY_FILE).unlink()
        self.remove_private_key(ledger_api_id=FetchAICrypto.identifier)
        self.remove_private_key(ledger_api_id=FetchAICrypto.identifier, connection=True)

    def _check_signature(self, cert_id, filename, stdout):
        """Check signature has been generated correctly."""
        path = Path(self.current_agent_context, filename)
        assert path.exists()
        signature = path.read_text()

        def is_ascii(s):
            """Check isascii method for all Python 3 versions"""
            return all(ord(c) < 128 for c in s)

        assert is_ascii(signature)
        int(signature, 16)  # this will fail if not hexadecimal

        cert_msg_1 = (
            f"Issuing certificate '{cert_id}' for connection fetchai/dummy:0.1.0..."
        )
        cert_msg_3 = f"Generated signature: '{signature}'"
        cert_msg_2 = f"Dumped certificate '{cert_id}' in '{filename}' for connection fetchai/dummy:0.1.0."
        assert cert_msg_1 in stdout
        assert cert_msg_2 in stdout
        assert cert_msg_3 in stdout


class TestIssueCertificatesWithOverride(TestIssueCertificatesPositive):
    """Test 'issue-certificates' with override configurations."""

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()

        cls.cert_id_3 = "cert_id_3"
        cls.cert_id_4 = "cert_id_4"
        cls.expected_path_3 = os.path.abspath("path_3")
        cls.expected_path_4 = os.path.abspath("path_4")
        cls.cert_request_3 = CertRequest(
            identifier=cls.cert_id_3,
            ledger_id=EthereumCrypto.identifier,
            not_before=NOT_BEFORE,
            not_after=NOT_AFTER,
            public_key=EthereumCrypto.identifier,
            message_format="{public_key}",
            save_path=cls.expected_path_3,
        )
        cls.cert_request_4 = CertRequest(
            identifier=cls.cert_id_4,
            ledger_id=EthereumCrypto.identifier,
            not_before=NOT_BEFORE,
            not_after=NOT_AFTER,
            public_key="0xABCDEF123456",
            message_format="{public_key}",
            save_path=cls.expected_path_4,
        )

        # Add override configurations
        dotted_path = f"connections.{DummyConnection.connection_id.name}.cert_requests"
        json_3 = json.dumps(cls.cert_request_3.json).replace("'", '"')
        json_4 = json.dumps(cls.cert_request_4.json).replace("'", '"')
        new_cert_requests = f"[{json_3}, {json_4}]"
        cls.set_config(dotted_path, new_cert_requests, type_="list")

    def test_issue_certificate(self, password_or_none):
        """Test 'aea issue-certificates' in case of success."""
        # setup: add private key with password
        ledger_id = EthereumCrypto.identifier
        self.generate_private_key(
            ledger_id, ETHEREUM_PRIVATE_KEY_FILE, password=password_or_none
        )
        self.add_private_key(
            ledger_id, ETHEREUM_PRIVATE_KEY_FILE, password=password_or_none
        )
        self.add_private_key(
            ledger_id,
            ETHEREUM_PRIVATE_KEY_FILE,
            connection=True,
            password=password_or_none,
        )

        password_options = _get_password_option_args(password_or_none)
        result = self.run_cli_command(
            "issue-certificates", *password_options, cwd=self._get_cwd()
        )
        self._check_signature(self.cert_id_3, self.expected_path_3, result.stdout)
        self._check_signature(self.cert_id_4, self.expected_path_4, result.stdout)

        # teardown: remove private key
        Path(self._get_cwd(), ETHEREUM_PRIVATE_KEY_FILE).unlink()
        self.remove_private_key(ledger_id)
        self.remove_private_key(ledger_id, connection=True)


class TestIssueCertificatesWrongConnectionKey(BaseTestIssueCertificates):
    """Test 'aea issue-certificates' when a bad connection key id is provided."""

    @classmethod
    def setup_class(cls):
        """Set up class."""
        super().setup_class()
        cls.cert_id_1 = "cert_id_1"
        cls.cert_request_1 = CertRequest(
            identifier=cls.cert_id_1,
            ledger_id=FetchAICrypto.identifier,
            not_before=NOT_BEFORE,
            not_after=NOT_AFTER,
            public_key="bad_ledger_id",
            message_format="{public_key}",
            save_path="path",
        )
        cls.add_cert_requests([cls.cert_request_1], DummyConnection.connection_id.name)

    def test_run(self):
        """Run the test."""
        with pytest.raises(
            Exception,
            match="Cannot find connection private key with id 'bad_ledger_id'",
        ):
            self.run_cli_command("issue-certificates", cwd=self._get_cwd())


class TestIssueCertificatesWrongCryptoKey(BaseTestIssueCertificates):
    """Test 'aea issue-certificates' when a bad crypto key id is provided."""

    @classmethod
    def setup_class(cls):
        """Set up class."""
        super().setup_class()
        cls.cert_id_1 = "cert_id_1"
        cls.cert_request_1 = CertRequest(
            identifier=cls.cert_id_1,
            ledger_id="bad_ledger_id",
            not_before=NOT_BEFORE,
            not_after=NOT_AFTER,
            public_key=FetchAICrypto.identifier,
            message_format="{public_key}",
            save_path="path",
        )
        cls.add_cert_requests([cls.cert_request_1], DummyConnection.connection_id.name)
        # add fetchai key and connection key
        cls.generate_private_key(ledger_api_id=FetchAICrypto.identifier)
        cls.add_private_key(
            ledger_api_id=FetchAICrypto.identifier,
            private_key_filepath=PRIVATE_KEY_PATH_SCHEMA.format(
                FetchAICrypto.identifier
            ),
        )
        cls.add_private_key(
            ledger_api_id=FetchAICrypto.identifier,
            private_key_filepath=PRIVATE_KEY_PATH_SCHEMA.format(
                FetchAICrypto.identifier
            ),
            connection=True,
        )

    def test_run(self):
        """Run the test."""
        with pytest.raises(
            Exception,
            match="Cannot find private key with id 'bad_ledger_id'",
        ):
            self.run_cli_command("issue-certificates", cwd=self._get_cwd())
