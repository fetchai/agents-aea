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

"""This module contains functions and classes regarding Proof-of-Representation (PoR) features."""
import contextlib
import datetime
from pathlib import Path
from typing import Dict, Optional, Union

from aea.exceptions import enforce
from aea.helpers.base import SimpleId, SimpleIdOrStr, parse_datetime_from_str


class CertRequest:
    """Certificate request for proof of representation."""

    def __init__(
        self,
        public_key: str,
        identifier: SimpleIdOrStr,
        ledger_id: SimpleIdOrStr,
        not_before: str,
        not_after: str,
        save_path: str,
    ):
        """
        Initialize the certificate request.

        :param public_key: the public key, or the key id.
        :param identifier: certificate identifier.
        :param not_before: specify the lower bound for certificate validity.
          If it is a string, it must follow the format: 'YYYY-MM-DD'. It
          will be interpreted as timezone UTC.
        :param not_before: specify the lower bound for certificate validity.
          if it is a string, it must follow the format: 'YYYY-MM-DD' It
          will be interpreted as timezone UTC-0.
        :param save_path: the save_path where to save the certificate.
        """
        self._key_identifier: Optional[str] = None
        self._public_key: Optional[str] = None
        self._identifier = str(SimpleId(identifier))
        self._ledger_id = str(SimpleId(ledger_id))
        self._not_before_string = not_before
        self._not_after_string = not_after
        self._not_before = self._parse_datetime(not_before)
        self._not_after = self._parse_datetime(not_after)
        self._save_path = Path(save_path)

        self._parse_public_key(public_key)
        self._check_validation_boundaries()

    @classmethod
    def _parse_datetime(cls, obj: Union[str, datetime.datetime]) -> datetime.datetime:
        """
        Parse datetime string.

        It is expected to follow ISO 8601.

        :param obj: the input to parse.
        :return: a datetime.datetime instance.
        """
        result = (
            parse_datetime_from_str(obj)  # type: ignore
            if isinstance(obj, str)
            else obj
        )
        enforce(result.microsecond == 0, "Microsecond field not allowed.")
        return result

    def _check_validation_boundaries(self):
        """
        Check the validation boundaries are consistent.

        Namely, that not_before < not_after.
        """
        enforce(
            self._not_before < self._not_after,
            f"Inconsistent certificate validity period: 'not_before' field '{self._not_before_string}' is not before than 'not_after' field '{self._not_after_string}'",
            ValueError,
        )

    def _parse_public_key(self, public_key_str: str) -> None:
        """
        Parse public key from string.

        It first tries to parse it as an identifier,
        and in case of failure as a sequence of hexadecimals, starting with "0x".
        """
        with contextlib.suppress(ValueError):
            # if this raises ValueError, we don't return
            self._key_identifier = str(SimpleId(public_key_str))
            return

        with contextlib.suppress(ValueError):
            # this raises ValueError if the input is not a valid hexadecimal string.
            int(public_key_str, 16)
            self._public_key = public_key_str
            return

        enforce(
            False,
            f"Public key field '{public_key_str}' is neither a valid identifier nor an address.",
            exception_class=ValueError,
        )

    @property
    def public_key(self) -> Optional[str]:
        """Get the public key."""
        return self._public_key

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def key_identifier(self) -> Optional[str]:
        """Get the key identifier."""
        return self._key_identifier

    @property
    def identifier(self) -> str:
        """Get the identifier."""
        return self._identifier

    @property
    def not_before_string(self) -> str:
        """Get the not_before field as string."""
        return self._not_before_string

    @property
    def not_after_string(self) -> str:
        """Get the not_after field as string."""
        return self._not_after_string

    @property
    def not_before(self) -> datetime.datetime:
        """Get the not_before field."""
        return self._not_before

    @property
    def not_after(self) -> datetime.datetime:
        """Get the not_after field."""
        return self._not_after

    @property
    def save_path(self) -> Path:
        """Get the save_path"""
        return self._save_path

    def get_message(self, public_key: str) -> bytes:  # pylint: disable=no-self-use
        """Get the message to sign."""
        message = public_key.encode("ascii")
        # + self.identifier.encode("ascii")  # noqa: E800
        # + self.not_before_string.encode("ascii")  # noqa: E800
        # + self.not_after_string.encode("ascii")  # noqa: E800
        return message

    def get_signature(self) -> str:
        """Get signature from save_path."""
        if not Path(self.save_path).is_file():
            raise Exception(  # pragma: no cover
                f"cert_request 'save_path' field {self.save_path} is not a file. "
                "Please ensure that 'issue-certificates' command is called beforehand."
            )
        signature = bytes.fromhex(
            Path(self.save_path).read_bytes().decode("ascii")
        ).decode("ascii")
        return signature

    @property
    def json(self) -> Dict:
        """Compute the JSON representation."""
        result = dict(
            identifier=self.identifier,
            ledger_id=self.ledger_id,
            not_before=self._not_before_string,
            not_after=self._not_after_string,
            save_path=str(self.save_path),
        )
        if self.public_key is not None:
            result["public_key"] = self.public_key
        elif self.key_identifier is not None:
            result["public_key"] = self.key_identifier
        return result

    @classmethod
    def from_json(cls, obj: Dict) -> "CertRequest":
        """Compute the JSON representation."""
        return cls(**obj)

    def __eq__(self, other):
        """Check equality."""
        return (
            isinstance(other, CertRequest)
            and self.identifier == other.identifier
            and self.ledger_id == other.ledger_id
            and self.public_key == other.public_key
            and self.key_identifier == other.key_identifier
            and self.not_after == other.not_after
            and self.not_before == other.not_before
            and self.save_path == other.save_path
        )
