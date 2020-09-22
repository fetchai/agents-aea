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

"""This module contains the crypto and the ledger APIs registries."""
from typing import Callable, Type

from aea.crypto.base import Crypto, FaucetApi, LedgerApi
from aea.crypto.registries.base import Registry


crypto_registry: Registry[Crypto] = Registry[Crypto]()
register_crypto = crypto_registry.register
make_crypto: Callable[..., Crypto] = crypto_registry.make

ledger_apis_registry: Registry[LedgerApi] = Registry[LedgerApi]()
register_ledger_api = ledger_apis_registry.register
make_ledger_api: Callable[..., LedgerApi] = ledger_apis_registry.make
make_ledger_api_cls: Callable[..., Type[LedgerApi]] = ledger_apis_registry.make_cls

faucet_apis_registry: Registry[FaucetApi] = Registry[FaucetApi]()
register_faucet_api = faucet_apis_registry.register
make_faucet_api: Callable[..., FaucetApi] = faucet_apis_registry.make
make_faucet_api_cls: Callable[..., Type[FaucetApi]] = faucet_apis_registry.make_cls
