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
from typing import Optional

from aea.common import PathLike
from aea.crypto.registries import make_ledger_api
from aea.helpers.base import CertRequest


class AgentRecord:
    """Agent Proof-of-Representation to representative."""

    __slots__ = (
        "_address",
        "_representative_public_key",
        "_message",
        "_signature",
        "_ledger_id",
        "_public_key",
    )

    def __init__(
        self,
        address: str,
        representative_public_key: str,
        message: bytes,
        signature: str,
        ledger_id: str,
    ) -> None:
        """
        Initialize the AgentRecord

        :param address: agent address
        :param representative_public_key: representative's public key
        :param message: message to be signed as proof-of-represenation of this AgentRecord
        :param signature: proof-of-representation of this AgentRecord
        :param ledger_id: ledger id
        """
        self._address = address
        self._representative_public_key = representative_public_key
        self._message = message
        self._signature = signature
        self._ledger_id = ledger_id
        self._public_key: Optional[str] = None
        self._check_validity()

    def _check_validity(self) -> None:
        """
        Checks validity of record.

        Specificyally:
        - if ledger_id is valid
        - if agent signed the message
        - if message is correctly formatted
        """
        if self.message != self._get_message(self.representative_public_key):
            raise ValueError("Invalid message.")  # pragma: no cover
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
        self._public_key = public_key

    @property
    def address(self) -> str:
        """Get agent address"""
        return self._address

    @property
    def public_key(self) -> str:
        """Get agent public key"""
        if self._public_key is None:
            raise ValueError("Inconsistent record!")  #  pragma: nocover
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
    def ledger_id(self) -> str:
        """Get ledger id."""
        return self._ledger_id

    def _get_message(self, public_key: str) -> bytes:  # pylint: disable=no-self-use
        """Get the message."""
        # Refactor, needs to match CertRequest!
        message = public_key.encode("ascii")
        # + self.identifier.encode("ascii")  # noqa: E800
        # + self.not_before_string.encode("ascii")  # noqa: E800
        # + self.not_after_string.encode("ascii")  # noqa: E800
        return message

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
        message = cert_request.get_message(representative_public_key)
        signature = cert_request.get_signature(data_dir)
        record = cls(
            address,
            representative_public_key,
            message,
            signature,
            cert_request.ledger_id,
        )
        return record
