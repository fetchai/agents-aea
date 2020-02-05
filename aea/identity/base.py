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

from aea.mail.base import Address


class Identity:
    """
    An identity are the public elements identifying an agent.

    It can include:
    - the agent name
    - the addresses
    """

    def __init__(
        self,
        name: str,
        address: Optional[str] = None,
        addresses: Optional[Dict[str, Address]] = None,
        default_address_key: Optional[str] = None,
    ):
        """
        Instantiate the identity.

        :param name: the name of the agent.
        :param addresses: the addresses of the agent.
        :param default_address_key: the key for the default address
        """
        self._name = name
        self._address = address
        self._addresses = addresses
        self._default_address_key = default_address_key
        self._check_consistency(address, addresses, default_address_key)

    def _check_consistency(self, address, addresses, default_address_key):
        is_single = address is not None
        is_multiple = addresses is not None and len(addresses) > 1
        assert (
            is_single != is_multiple
        ), "Either provide a single address or a dictionary of multiple addresses, not both."
        if is_multiple:
            assert default_address_key is not None, "No key set for default address."
            assert (
                default_address_key in addresses.keys()
            ), "Addresses does not contain default address key."

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    @property
    def addresses(self) -> Dict[str, Address]:
        """Get the addresses."""
        assert self._addresses is not None, "No addresses assigned."
        return self._addresses

    @property
    def address(self) -> Address:
        """Get the default address."""
        if self._address is not None:
            return self._address
        else:
            assert (
                self._default_address_key is not None
            ), "No key set for default address."
            return self.addresses[self._default_address_key]
