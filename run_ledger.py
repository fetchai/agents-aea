#!/usr/bin/env python3
from tests.conftest import (
    DEFAULT_FETCH_MNEMONIC,
    DEFAULT_MONIKER,
    DEFAULT_FETCH_CHAIN_ID,
    DEFAULT_GENESIS_ACCOUNT,
    DEFAULT_DENOMINATION,
    DEFAULT_FETCH_LEDGER_ADDR,
    DEFAULT_FETCH_LEDGER_RPC_PORT,
    DEFAULT_FETCH_DOCKER_IMAGE_TAG,
    _launch_image,
    fund_accounts_from_local_validator,
)
from contextlib import contextmanager
from tests.common.docker_image import FetchLedgerDockerImage
import docker
import time
import sys

fetchd_configuration = dict(
    mnemonic=DEFAULT_FETCH_MNEMONIC,
    moniker=DEFAULT_MONIKER,
    chain_id=DEFAULT_FETCH_CHAIN_ID,
    genesis_account=DEFAULT_GENESIS_ACCOUNT,
    denom=DEFAULT_DENOMINATION,
)


@contextmanager
def fetchd():
    client = docker.from_env()
    image = FetchLedgerDockerImage(
        client,
        DEFAULT_FETCH_LEDGER_ADDR,
        DEFAULT_FETCH_LEDGER_RPC_PORT,
        DEFAULT_FETCH_DOCKER_IMAGE_TAG,
        config=fetchd_configuration,
    )
    yield from _launch_image(image, timeout=2, max_attempts=20)


DEFAULT_AMOUNT = 10000000000000000


def main():
    if len(sys.argv) < 2:
        raise ValueError("Use command as ./scriptname addr1,addr2 [amount]")
    addresses = sys.argv[1].split(",")
    amount = DEFAULT_AMOUNT
    if len(sys.argv) > 2:
        amount = int(sys.argv[2])
    print("fund addresses", addresses, "with amount", amount)
    with fetchd():
        time.sleep(5)
        print("fetchd started")
        fund_accounts_from_local_validator(addresses, amount)
        print("addresses funded!\n")
        print("press ctrl+c once to stop")
        try:
            while 1:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("stopping. please wait...")


if __name__ == "__main__":
    main()
