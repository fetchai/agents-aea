import time
from typing import List

from cosmpy.clients.signing_cosmwasm_client import SigningCosmWasmClient
from cosmpy.common.rest_client import RestClient
from cosmpy.crypto.address import Address as CosmpyAddress
from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.protos.cosmos.base.v1beta1.coin_pb2 import Coin

DEFAULT_FETCH_LEDGER_ADDR = "http://127.0.0.1"
DEFAULT_FETCH_LEDGER_REST_PORT = 1317
DEFAULT_FETCH_CHAIN_ID = "stargateworld-2"
DEFAULT_DENOMINATION = "atestfet"
FETCHD_INITIAL_TX_SLEEP = 6

FUNDED_FETCHAI_PRIVATE_KEY_1 = (
    "bbaef7511f275dc15f47436d14d6d3c92d4d01befea073d23d0c2750a46f6cb3"
)  # validator address

FUNDED_FETCHAI_ADDRESS_ONE = "fetch17ff72sh5svekjvpkpheedzdsghxgzd7clvaay5"  # controller address
FUNDED_FETCHAI_ADDRESS_TWO = "fetch168xkfqd6p264zgr3w44ftcq2mr5hw8wulmn3fu"  # participant 1
FUNDED_FETCHAI_ADDRESS_THREE = "fetch1ruu9sc8gsux0tgmdt9p3uj3gha5h3u7ea5v4sn"  # participant 2


def fund_accounts_from_local_validator(
    addresses: List[str], amount: int, denom: str = DEFAULT_DENOMINATION
):
    """Send funds to local accounts from the local genesis validator."""
    rest_client = RestClient(
        f"{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_REST_PORT}"
    )
    pk = PrivateKey(bytes.fromhex(FUNDED_FETCHAI_PRIVATE_KEY_1))

    time.sleep(FETCHD_INITIAL_TX_SLEEP)
    client = SigningCosmWasmClient(pk, rest_client, DEFAULT_FETCH_CHAIN_ID)
    coins = [Coin(amount=str(amount), denom=denom)]

    for address in addresses:
        client.send_tokens(CosmpyAddress(address), coins)
        balance = client.get_balance(address=CosmpyAddress(address), denom=denom)
        print(f"Balance for {address}={balance}")


if __name__ == "__main__":
    """Fund test accounts from local validator."""
    fund_accounts_from_local_validator(
        [
            FUNDED_FETCHAI_ADDRESS_ONE,
            FUNDED_FETCHAI_ADDRESS_TWO,
            FUNDED_FETCHAI_ADDRESS_THREE
        ],
        10000000000000000000,
    )
