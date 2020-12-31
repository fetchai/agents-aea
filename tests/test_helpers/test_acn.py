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
from aea.helpers.acn.agent_record import AgentRecord, signature_from_cert_request
from aea.helpers.base import CertRequest

from tests.conftest import _process_cert


def test_signature_from_cert_request_errors():
    agent_key_1 = make_crypto(DEFAULT_LEDGER)
    agent_key_2 = make_crypto(DEFAULT_LEDGER)

    peer_public_key = make_crypto(DEFAULT_LEDGER).public_key

    cert_path = "test_acn_cert.txt"

    cert = CertRequest(
        peer_public_key,
        "test_service",
        DEFAULT_LEDGER,
        "2021-01-01",
        "2022-01-01",
        cert_path,
    )
    _process_cert(agent_key_1, cert)

    # success
    _, signer_public_key = signature_from_cert_request(
        cert, peer_public_key, agent_key_1.address
    )
    assert signer_public_key == agent_key_1.public_key

    # error: wrong signer
    with pytest.raises(Exception):
        signature_from_cert_request(cert, peer_public_key, agent_key_2.address)


def test_agent_record_errors():
    agent_key_1 = make_crypto(DEFAULT_LEDGER)
    agent_key_2 = make_crypto(DEFAULT_LEDGER)

    peer_public_key_1 = make_crypto(DEFAULT_LEDGER).public_key
    peer_public_key_2 = make_crypto(DEFAULT_LEDGER).public_key

    cert_path = "test_acn_cert.txt"
    service_id = "test_acn_service"

    cert = CertRequest(
        peer_public_key_1,
        "test_service",
        DEFAULT_LEDGER,
        "2021-01-01",
        "2022-01-01",
        cert_path,
    )
    _process_cert(agent_key_1, cert)
    signature, _ = signature_from_cert_request(
        cert, peer_public_key_1, agent_key_1.address
    )

    # success
    agent_record = AgentRecord(
        agent_key_1.address,
        agent_key_1.public_key,
        peer_public_key_1,
        signature,
        service_id,
    )
    agent_record.check_validity(agent_key_1.address, peer_public_key_1)
    assert (
        agent_record.address == agent_key_1.address
        and agent_record.public_key == agent_key_1.public_key
        and agent_record.peer_public_key == peer_public_key_1
        and agent_record.signature == signature
        and agent_record.service_id == service_id
    )

    # error: wrong agent address
    with pytest.raises(Exception):
        agent_record.check_validity(agent_key_2.address, peer_public_key_1)

    # error: wrong peer
    with pytest.raises(Exception):
        agent_record.check_validity(agent_key_1.address, peer_public_key_2)

    # error: agent address and public key don't match
    agent_record = AgentRecord(
        agent_key_2.address,
        agent_key_1.public_key,
        peer_public_key_1,
        signature,
        service_id,
    )
    with pytest.raises(Exception):
        agent_record.check_validity(agent_key_2.address, peer_public_key_1)

    # error: invalid signature
    _process_cert(agent_key_2, cert)
    signature, _ = signature_from_cert_request(
        cert, peer_public_key_1, agent_key_2.address
    )
    agent_record = AgentRecord(
        agent_key_1.address,
        agent_key_1.public_key,
        peer_public_key_1,
        signature,
        service_id,
    )
    with pytest.raises(Exception):
        agent_record.check_validity(agent_key_1.address, peer_public_key_1)
