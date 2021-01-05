# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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

"""Implementation of the custom crypto."""
from typing import BinaryIO

from aea.common import JSONLike
from aea.crypto.base import Crypto, EntityClass


class MyCrypto(Crypto):
    """Main class of the MyCrypto plug-in."""

    @classmethod
    def generate_private_key(cls) -> EntityClass:
        """To be implemented."""

    @classmethod
    def load_private_key_from_path(cls, file_name: str) -> EntityClass:
        """To be implemented."""

    @property
    def private_key(self) -> str:
        """To be implemented."""
        raise NotImplementedError

    @property
    def public_key(self) -> str:
        """To be implemented."""
        raise NotImplementedError

    @property
    def address(self) -> str:
        """To be implemented."""
        raise NotImplementedError

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """To be implemented."""
        raise NotImplementedError

    def sign_transaction(self, transaction: JSONLike) -> JSONLike:
        """To be implemented."""
        raise NotImplementedError

    def dump(self, fp: BinaryIO) -> None:
        """To be implemented."""
        raise NotImplementedError
