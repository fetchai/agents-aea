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

"""This module contains types and helpers for acn Proof-of-Representation."""

import base64
from hashlib import sha256
from pathlib import Path
from typing import List, Tuple

from ecdsa import SECP256k1, VerifyingKey

from aea.crypto.fetchai import FetchAIHelper
from aea.helpers.base import CertRequest


def recover_verify_keys_from_message(message: bytes, signature: str) -> List[str]:
    """
    Get the public key used to produce the `signature` of the `message`

    :param message: raw bytes used to produce signature
    :param signature: signature of the message
    """

    signature_b64 = base64.b64decode(signature)
    verifying_keys = VerifyingKey.from_public_key_recovery(
        signature_b64, message, SECP256k1, hashfunc=sha256,
    )
    public_keys = [
        verifying_key.to_string("compressed").hex() for verifying_key in verifying_keys
    ]
    return public_keys

def signature_from_cert_request(
    cert: CertRequest, message: str, signer_address: str
) -> Tuple[str, str]:
    """
    Get signature and its verifying key from a CertRequest and its message.
    Note: must match aea/cli/issue_certificates.py:_process_certificate

    :param cert: cert request containing the signature
    :param message: the message used to generate signature
    :param signer_address: the address of the signer
    :return: the signature and the verifying public key
    """
    
    signature = bytes.fromhex(Path(cert.save_path).read_bytes().decode("ascii")).decode(
        "ascii"
    )
    public_keys = recover_verify_keys_from_message(
        cert.get_message(message), signature
    )
    if len(public_keys) == 0:
        raise Exception("Malformed signature")
    addresses = [
        FetchAIHelper.get_address_from_public_key(public_key)
        for public_key in public_keys
    ]
    try:
        verify_key = public_keys[addresses.index(signer_address)]
    except ValueError:
        raise Exception("Not signed by agent")
    return signature, verify_key



class AgentRecord:
    """Agent Proof-of-Representation to peer"""

    def __init__(
        self,
        address: str,
        public_key: str,
        peer_public_key: str,
        signature: str,
        service_id: str,
    ):
        """
        Initialize the AgentRecord

        :param address: agent address
        :param public key: agent public key (associated to the address)
        :param peer_public_key: representative peer public key
        :param signature: proof-of-representation of this AgentRecord
        :param service_id: type of service for which the record is used
        """
        self._service_id = service_id
        self._address = address
        self._public_key = public_key
        self._peer_public_key = peer_public_key
        self._signature = signature

    @property
    def address(self) -> str:
        """Get agent address"""
        return self._address

    @property
    def public_key(self) -> str:
        """Get agent public key"""
        return self._public_key

    @property
    def peer_public_key(self) -> str:
        """Get agent's representative peer public key"""
        return self._peer_public_key

    @property
    def signature(self) -> str:
        """Get record signature"""
        return self._signature

    @property
    def service_id(self) -> str:
        """Get record service id"""
        return self._service_id

    def __str__(self):
        """Get string representation."""
        return f"(address={self.address}, public_key={self.public_key}, peer_public_key={self.peer_public_key}, signature={self.signature})"

    def check_validity(self, address: str, peer_public_key: str) -> None:
        """
        Check if the agent record is valid for `address` and `peer_public_key`.
        Raises an Exception if invalid.

        :param address: the expected agent address concerned by the record
        :param peer_public_key: the expected representative peer public key
        """

        if self._address != address:
            raise Exception(
                "Proof-of-representation is not generated for the intended agent"
            )
        if self._peer_public_key != peer_public_key:
            raise Exception(
                "Proof-of-representation is not generated for intended peer"
            )
        if self._address != FetchAIHelper.get_address_from_public_key(self._public_key):
            raise Exception("Agent address and public key doesn't match")
        if self._address not in FetchAIHelper.recover_message(
            self._peer_public_key.encode("utf-8"), self._signature
        ):
            raise Exception("Invalid signature")
