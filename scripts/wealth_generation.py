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
import argparse
import logging
import pprint
import sys

from fetchai.ledger.api import LedgerApi        # type: ignore
from fetchai.ledger.crypto import Entity, Address  # type: ignore

logger = logging.getLogger(__name__)


def generate_wealth(arguments: argparse.Namespace) -> None:
    """
    Generate tokens to be able to make a transaction.

    :return:
    """
    api = LedgerApi("127.0.0.1", 8000)

    try:
        if arguments.private_key is None or arguments.private_key == "":
            raise ValueError
        entity_to_generate_wealth = Entity.from_hex(arguments.private_key)
    except ValueError:
        logger.debug("Please provide a private key. --privte-key .... ")
        sys.exit("-Please provide a private key. --private-key .... ")

    api.sync(api.tokens.wealth(entity_to_generate_wealth, arguments.amount))
    address = Address(entity_to_generate_wealth)
    logger.info('The new balance of the address {} is : {} FET'.format(address, api.tokens.balance(address)))


def parse_arguments():
    """Arguments parsing."""
    parser = argparse.ArgumentParser("wealth_creation")
    parser.add_argument("--amount", type=int, default=10, help="The amount we want to generate to the address")
    parser.add_argument("--private-key", type=str, default=None,
                        help="The amount we want to generate to the address")
    arguments = parser.parse_args()
    logger.debug("Arguments: {}".format(pprint.pformat(arguments.__dict__)))

    return arguments


if __name__ == "__main__":
    arguments = parse_arguments()
    generate_wealth(arguments)
