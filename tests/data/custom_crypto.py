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

"""This module contains a custom crypto class for testing purposes."""
from typing import Any, BinaryIO, Tuple

from aea.crypto.base import Crypto, EntityClass
from aea.mail.base import Address


class CustomCrypto(Crypto):
    """This is a custom crypto class for testing purposes.."""

    @classmethod
    def generate_private_key(cls) -> EntityClass:
        pass

    @classmethod
    def load_private_key_from_path(cls, file_name: str) -> EntityClass:
        pass

    @property
    def public_key(self) -> str:
        pass

    @property
    def address(self) -> str:
        pass

    @property
    def private_key(self) -> str:
        pass

    @classmethod
    def get_address_from_public_key(cls, public_key: str) -> str:
        pass

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        pass

    def sign_transaction(self, transaction: Any) -> Any:
        pass

    def recover_message(
        self, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[Address, ...]:
        pass

    def dump(self, fp: BinaryIO) -> None:
        pass
