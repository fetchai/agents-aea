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
"""This module contains the tests for acn helper module."""

import pytest

from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.registries import make_crypto
from aea.helpers.acn.agent_record import AgentRecord
from aea.helpers.base import CertRequest

from tests.conftest import _process_cert


def test_agent_record(change_directory):
    """Test signature and public key proper retrieval from a CertRequest"""
    agent_key_1 = make_crypto(DEFAULT_LEDGER)
    agent_key_2 = make_crypto(DEFAULT_LEDGER)

    peer_public_key_1 = make_crypto(DEFAULT_LEDGER).public_key
    peer_public_key_2 = make_crypto(DEFAULT_LEDGER).public_key

    cert_path = "test_acn_cert.txt"

    cert = CertRequest(
        peer_public_key_1,
        "test_service",
        DEFAULT_LEDGER,
        "2021-01-01",
        "2022-01-01",
        "{public_key}",
        cert_path,
    )
    _process_cert(agent_key_1, cert, change_directory)

    # success
    agent_record = AgentRecord.from_cert_request(
        cert, agent_key_1.address, peer_public_key_1
    )
    assert (
        agent_record.address == agent_key_1.address
        and agent_record.public_key == agent_key_1.public_key
        and agent_record.representative_public_key == peer_public_key_1
        and agent_record.signature == cert.get_signature()
        and agent_record.message == cert.get_message(peer_public_key_1)
    )

    # success
    agent_record = AgentRecord(
        agent_key_1.address,
        peer_public_key_1,
        cert.identifier,
        cert.ledger_id,
        cert.not_before,
        cert.not_after,
        cert.message_format,
        cert.get_signature(),
    )
    assert (
        agent_record.address == agent_key_1.address
        and agent_record.public_key == agent_key_1.public_key
        and agent_record.representative_public_key == peer_public_key_1
        and agent_record.signature == cert.get_signature()
        and agent_record.message == cert.get_message(peer_public_key_1)
    )

    # error: wrong signer
    with pytest.raises(
        ValueError,
        match="Invalid signature for provided representative_public_key and agent address!",
    ):
        AgentRecord.from_cert_request(cert, agent_key_2.address, peer_public_key_1)

    # error: wrong signer
    with pytest.raises(
        ValueError,
        match="Invalid signature for provided representative_public_key and agent address!",
    ):
        AgentRecord.from_cert_request(cert, agent_key_1.address, peer_public_key_2)
