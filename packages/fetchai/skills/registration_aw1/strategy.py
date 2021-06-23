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

"""This package contains a scaffold of a model."""

from typing import Any, Dict, List, Optional

from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce
from aea.skills.base import Model


DEFAULT_SHARED_STORAGE_KEY = "agents_found"
DEFAULT_ETHEREUM_ADDRESS = "PUT_YOUR_ETHEREUM_ADDRESS_HERE"
DEFAULT_SIGNATURE_OF_FETCHAI_ADDRESS = "PUT_YOUR_SIGNATURE_HERE"
DEFAULT_DEVELOPER_HANDLE = "PUT_YOUR_DEVELOPER_HANDLE_HERE"
DEFAULT_TWEET = "PUT_THE_LINK_TO_YOUR_TWEET_HERE"
DEFAULT_WHITELIST: List[str] = []


class Strategy(Model):
    """This class is the strategy model."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
        """
        developer_handle = kwargs.pop("developer_handle", DEFAULT_DEVELOPER_HANDLE)
        enforce(
            developer_handle != DEFAULT_DEVELOPER_HANDLE
            and isinstance(developer_handle, str),
            f"Not a valid developer_handle: {developer_handle}",
        )
        self._developer_handle = developer_handle
        self._whitelist = kwargs.pop("whitelist", DEFAULT_WHITELIST)
        self._shared_storage_key = kwargs.pop(
            "shared_storage_key", DEFAULT_SHARED_STORAGE_KEY
        )
        self.announce_termination_key = kwargs.pop("announce_termination_key", None)

        self.developer_handle_only = kwargs.pop("developer_handle_only", False)
        if not self.developer_handle_only:
            ethereum_address = kwargs.pop("ethereum_address", DEFAULT_ETHEREUM_ADDRESS)
            enforce(
                ethereum_address != DEFAULT_ETHEREUM_ADDRESS
                and LedgerApis.is_valid_address("ethereum", ethereum_address),
                f"Not a valid ethereum_address: {ethereum_address}",
            )
            self._ethereum_address = ethereum_address
            signature_of_fetchai_address = kwargs.pop(
                "signature_of_fetchai_address", DEFAULT_SIGNATURE_OF_FETCHAI_ADDRESS
            )
            enforce(
                signature_of_fetchai_address != DEFAULT_SIGNATURE_OF_FETCHAI_ADDRESS
                and isinstance(signature_of_fetchai_address, str),
                f"Not a valid signature_of_fetchai_address: {signature_of_fetchai_address}",
            )
            self._signature_of_fetchai_address = signature_of_fetchai_address
            tweet = kwargs.pop("tweet", DEFAULT_TWEET)
            enforce(isinstance(tweet, str), "Not a valid tweet link")
            self._tweet = tweet
            self._is_ready_to_register = False
        else:
            self._is_ready_to_register = True
            self._ethereum_address = "some_dummy_address"
            self._signature_of_fetchai_address = None
            self._tweet = None
        super().__init__(**kwargs)
        self._is_registered = False
        self.is_registration_pending = False
        self.signature_of_ethereum_address: Optional[str] = None
        self._ledger_id = self.context.default_ledger_id

    @property
    def shared_storage_key(self) -> str:
        """Get shared storage key."""
        return self._shared_storage_key

    @property
    def whitelist(self) -> List[str]:
        """Get the whitelist."""
        return self._whitelist

    @property
    def ethereum_address(self) -> str:
        """Get the ethereum address."""
        return self._ethereum_address

    @property
    def ledger_id(self) -> str:
        """Get ledger id."""
        return self._ledger_id

    @property
    def is_ready_to_register(self) -> bool:
        """Get readiness for registration."""
        return self._is_ready_to_register

    @is_ready_to_register.setter
    def is_ready_to_register(self, is_ready_to_register: bool) -> None:
        """Set readiness for registration."""
        self._is_ready_to_register = is_ready_to_register

    @property
    def is_registered(self) -> bool:
        """Get registration status."""
        return self._is_registered

    @is_registered.setter
    def is_registered(self, is_registered: bool) -> None:
        """Set registration status."""
        enforce(not self._is_registered, "Can only switch to true.")
        self._is_registered = is_registered

    @property
    def registration_info(self) -> Dict[str, str]:
        """
        Get the location description.

        :return: a description of the agent's location
        """
        if self.developer_handle_only:
            info = {
                "fetchai_address": self.context.agent_address,
                "developer_handle": self._developer_handle,
            }
        else:
            info = {
                "ethereum_address": self._ethereum_address,
                "fetchai_address": self.context.agent_address,
                "signature_of_ethereum_address": self.signature_of_ethereum_address,
                "signature_of_fetchai_address": self._signature_of_fetchai_address,
                "developer_handle": self._developer_handle,
            }
            if self._tweet != DEFAULT_TWEET:
                info.update({"tweet": self._tweet})
        return info
