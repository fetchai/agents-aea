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
from pathlib import Path

from fetchai.ledger.api import LedgerApi  # type: ignore
from fetchai.ledger.crypto import Address, Entity  # type: ignore


def generate_fetchai_wealth(arguments: argparse.Namespace) -> None:
    """
    Generate tokens to be able to make a transaction.

    :param arguments: the arguments
    :return: None
    """
    try:
        api = LedgerApi(arguments.addr, arguments.port)
    except Exception:
        logging.info("Couldn't connect! Please check your add and port.")
        sys.exit(1)

    try:
        if arguments.private_key is None or arguments.private_key == "":
            raise ValueError
    except ValueError:
        logging.error("Please provide a private key. --private-key .... ")
        sys.exit(1)

    logging.info("Waiting for token wealth generation...")
    entity_to_generate_wealth = Entity.from_hex(Path(arguments.private_key).read_text())
    api.sync(api.tokens.wealth(entity_to_generate_wealth, arguments.amount))
    address = Address(entity_to_generate_wealth)
    balance = api.tokens.balance(address)
    logging.info(
        "The new balance of the address {} is : {} FET".format(address, balance)
    )


def parse_arguments():
    """Arguments parsing."""
    parser = argparse.ArgumentParser("wealth_creation")
    parser.add_argument(
        "--addr", type=str, default="127.0.0.1", help="The addr for the ledger api"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="The port for the ledger api"
    )
    parser.add_argument(
        "--amount",
        type=int,
        default=10,
        help="The amount we want to generate to the address",
    )
    parser.add_argument(
        "--private-key",
        type=str,
        default=None,
        help="The path to the private key file.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity."
    )
    arguments = parser.parse_args()

    return arguments


if __name__ == "__main__":
    arguments = parse_arguments()
    if arguments.verbose:
        logging.basicConfig(
            format="[%(asctime)s][%(levelname)s] %(message)s", level=logging.DEBUG
        )
    else:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

    logging.debug("Arguments: {}".format(pprint.pformat(arguments.__dict__)))
    generate_fetchai_wealth(arguments)
