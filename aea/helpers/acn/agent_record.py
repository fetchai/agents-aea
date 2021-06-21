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

"""This module contains types and helpers for ACN Proof-of-Representation."""
from typing import Optional

from aea.common import PathLike
from aea.crypto.registries import make_ledger_api
from aea.helpers.base import CertRequest, SimpleId, SimpleIdOrStr


class AgentRecord:
    """Agent Proof-of-Representation to representative."""

    __slots__ = (
        "_address",
        "_representative_public_key",
        "_identifier",
        "_ledger_id",
        "_not_before",
        "_not_after",
        "_message_format",
        "_signature",
        "_message",
        "_public_key",
    )

    def __init__(
        self,
        address: str,
        representative_public_key: str,
        identifier: SimpleIdOrStr,
        ledger_id: SimpleIdOrStr,
        not_before: str,
        not_after: str,
        message_format: str,
        signature: str,
    ) -> None:
        """
        Initialize the AgentRecord

        :param address: agent address
        :param representative_public_key: representative's public key
        :param identifier: certificate identifier.
        :param ledger_id: ledger identifier the request is referring to.
        :param not_before: specify the lower bound for certificate validity. If it is a string, it must follow the format: 'YYYY-MM-DD'. It will be interpreted as timezone UTC-0.
        :param not_after: specify the lower bound for certificate validity. If it is a string, it must follow the format: 'YYYY-MM-DD'. It will be interpreted as timezone UTC-0.
        :param message_format: message format used for signing
        :param signature: proof-of-representation of this AgentRecord
        """
        self._address = address
        self._representative_public_key = representative_public_key
        self._identifier = str(SimpleId(identifier))
        self._ledger_id = str(SimpleId(ledger_id))
        self._not_before = not_before
        self._not_after = not_after
        self._message_format = message_format
        self._signature = signature
        self._message = CertRequest.construct_message(
            self.representative_public_key,
            self.identifier,
            self.not_before,
            self.not_after,
            self.message_format,
        )
        self._public_key = self._check_validity()

    def _check_validity(self) -> str:
        """
        Checks validity of record.

        Specifically:
        - if ledger_id is valid
        - if agent signed the message

        :return: agent public key
        """
        ledger_api = make_ledger_api(self.ledger_id)
        public_keys = ledger_api.recover_public_keys_from_message(
            self.message, self.signature
        )
        if len(public_keys) == 0:
            raise ValueError("Malformed signature!")  # pragma: no cover
        public_key: Optional[str] = None
        for public_key_ in public_keys:
            address = ledger_api.get_address_from_public_key(public_key_)
            if address == self.address:
                public_key = public_key_
                break
        if public_key is None:
            raise ValueError(
                "Invalid signature for provided representative_public_key and agent address!"
            )
        return public_key

    @property
    def address(self) -> str:
        """Get agent address"""
        return self._address

    @property
    def public_key(self) -> str:
        """Get agent public key"""
        return self._public_key

    @property
    def representative_public_key(self) -> str:
        """Get agent representative's public key"""
        return self._representative_public_key

    @property
    def signature(self) -> str:
        """Get record signature"""
        return self._signature

    @property
    def message(self) -> bytes:
        """Get the message."""
        return self._message

    @property
    def identifier(self) -> SimpleIdOrStr:
        """Get the identifier."""
        return self._identifier

    @property
    def ledger_id(self) -> SimpleIdOrStr:
        """Get ledger id."""
        return self._ledger_id

    @property
    def not_before(self) -> str:
        """Get the not_before field."""
        return self._not_before

    @property
    def not_after(self) -> str:
        """Get the not_after field."""
        return self._not_after

    @property
    def message_format(self) -> str:
        """Get the message format."""
        return self._message_format

    def __str__(self) -> str:  # pragma: no cover
        """Get string representation."""
        return f"(address={self.address}, public_key={self.public_key}, representative_public_key={self.representative_public_key}, signature={self.signature}, ledger_id={self.ledger_id})"

    @classmethod
    def from_cert_request(
        cls,
        cert_request: CertRequest,
        address: str,
        representative_public_key: str,
        data_dir: Optional[PathLike] = None,
    ) -> "AgentRecord":
        """Get agent record from cert request."""
        signature = cert_request.get_signature(data_dir)
        record = cls(
            address,
            representative_public_key,
            cert_request.identifier,
            cert_request.ledger_id,
            cert_request.not_before_string,
            cert_request.not_after_string,
            cert_request.message_format,
            signature,
        )
        return record
