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
"""Beacon World module wrapping the public and private key cryptography and ledger api."""

from typing import Any

from aea.crypto.cosmos import CosmosCrypto, CosmosFaucetApi, CosmosHelper, _CosmosApi

_BEACON_WORLD = "beacon_world"
_FETCH = "fetch"
TESTNET_NAME = "testnet"
BEACON_WORLD_FAUCET_URL = "https://faucet-beaconworld.fetch.ai"
DEFAULT_ADDRESS = "https://rest-beaconworld.fetch.ai:443"
DEFAULT_CURRENCY_DENOM = "atestfet"
DEFAULT_CHAIN_ID = "beaconworld-1"
DEFAULT_CLI_COMMAND = "fetchcli"


class BeaconWorldHelper(CosmosHelper):
    """Helper class usable as Mixin for FetchAIApi or as standalone class."""

    address_prefix = _FETCH


class BeaconWorldCrypto(CosmosCrypto):
    """Class wrapping the Entity Generation from Fetch.AI Beacon World ledger."""

    identifier = _BEACON_WORLD
    helper = BeaconWorldHelper


class BeaconWorldApi(_CosmosApi, BeaconWorldHelper):
    """Class to interact with the Fetch Beacon World ledger APIs."""

    identifier = _BEACON_WORLD

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Fetch.ai Beacon World ledger APIs."""
        if "address" not in kwargs:
            kwargs["address"] = DEFAULT_ADDRESS  # pragma: nocover
        if "denom" not in kwargs:
            kwargs["denom"] = DEFAULT_CURRENCY_DENOM
        if "chain_id" not in kwargs:
            kwargs["chain_id"] = DEFAULT_CHAIN_ID
        if "cli_command" not in kwargs:
            kwargs["cli_command"] = DEFAULT_CLI_COMMAND
        super().__init__(**kwargs)


class BeaconWorldFaucetApi(CosmosFaucetApi):
    """Beacon World testnet faucet API."""

    identifier = _BEACON_WORLD
    testnet_name = TESTNET_NAME
    testnet_faucet_url = BEACON_WORLD_FAUCET_URL
