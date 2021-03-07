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

"""This module contains the identity class."""

from typing import Dict, Optional

from aea.common import Address
from aea.configurations.constants import DEFAULT_LEDGER


class Identity:
    """
    The identity holds the public elements identifying an agent.

    It includes:

    - the agent name
    - the addresses, a map from address identifier to address (can be a single key-value pair)
    """

    __slots__ = ("_name", "_address", "_addresses", "_default_address_key")

    def __init__(
        self,
        name: str,
        address: Optional[str] = None,
        addresses: Optional[Dict[str, Address]] = None,
        default_address_key: str = DEFAULT_LEDGER,
    ) -> None:
        """
        Instantiate the identity.

        :param name: the name of the agent.
        :param address: the default address of the agent.
        :param addresses: the addresses of the agent.
        :param default_address_key: the key for the default address.
        """
        self._name = name
        if default_address_key is None:
            raise ValueError(
                "Provide a key for the default address."
            )  # pragma: nocover
        if (address is None) == (addresses is None):
            raise ValueError(
                "Either provide a single address or a dictionary of addresses, not both."
            )
        if address is None:
            if addresses is None or len(addresses) == 0:  # pragma: nocover
                raise ValueError("Provide at least one pair of addresses.")
            address = addresses[default_address_key]
        self._address = address
        if addresses is None:
            addresses = {default_address_key: address}
        self._addresses = addresses
        self._default_address_key = default_address_key

    @property
    def default_address_key(self) -> str:
        """Get the default address key."""
        return self._default_address_key

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    @property
    def addresses(self) -> Dict[str, Address]:
        """Get the addresses."""
        return self._addresses

    @property
    def address(self) -> Address:
        """Get the default address."""
        return self._address
