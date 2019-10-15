# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Helper script that generates wealth on a specific address."""
import logging
import sys
from typing import Optional

from fetchai.ledger.api import LedgerApi        # type: ignore
from fetchai.ledger.crypto import Entity, Address, Identity  # type: ignore

logger = logging.getLogger(__name__)


def _generate_wealth(amount, private_key: Optional[str] = None) -> None:
    """
    Generate tokens to be able to make a transaction.

    :return:
    """
    entity_to_generate_wealth = Entity.from_hex(private_key)
    api = LedgerApi("127.0.0.1", 8000)
    api.sync(api.tokens.wealth(entity_to_generate_wealth, amount))
    address = Address(entity_to_generate_wealth)
    logger.info('The new balance of the address {} is : {} FET'.format(address, api.tokens.balance(address)))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        _generate_wealth(sys.argv[1], sys.argv[2])
    else:
        _generate_wealth(sys.argv[1])
