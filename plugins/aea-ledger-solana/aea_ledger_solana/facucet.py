import json
import time

from aea.crypto.base import FaucetApi
from aea.common import Address
from aea.helpers.base import try_decorator
from typing import Optional, Union

from solders.pubkey import Pubkey as PublicKey
from solana.rpc.api import Client  # type: ignore

from .constants import (
    _SOLANA,
    TESTNET_NAME,
    DEFAULT_ADDRESS,
    LAMPORTS_PER_SOL,
    DEFAULT_CHAIN_ID,
    DEFAULT_CURRENCY_DENOM,
)
from .utils import default_logger


class SolanaFaucetApi(FaucetApi):
    """Solana testnet faucet API."""

    identifier = _SOLANA
    testnet_name = TESTNET_NAME
    DEFAULT_AMOUNT = 500000000

    def get_wealth(self, address: Address, url: Optional[str] = None) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param url: the url

        """
        amount = self.DEFAULT_AMOUNT
        self._try_get_wealth(address, amount, url)

    @staticmethod
    @try_decorator(
        "An error occurred while attempting to generate wealth:\n{}",
        logger_method="error",
    )
    def _try_get_wealth(
        address: Address, amount: Optional[int] = None, url: Optional[str] = None
    ) -> Optional[str]:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param amount: optional int
        :param url: the url

        :return: optional string
        """
        if url is None:
            url = DEFAULT_ADDRESS

        if amount is None:
            amount = int(LAMPORTS_PER_SOL * 0.5)
        else:
            amount = LAMPORTS_PER_SOL * amount

        solana_client = Client(url, commitment="confirmed")
        resp = solana_client.request_airdrop(PublicKey.from_string(address), amount)

        response = json.loads(resp.to_json())
        if "message" in response:
            default_logger.error("Response: {}".format(response["message"]))
            raise Exception(response.get("message"))
        if response["result"] is None:
            default_logger.error("Response: {}".format("airdrop failed"))
        elif "error" in response:  # pragma: no cover
            default_logger.error("Response: {}".format("airdrop failed"))
        elif "result" in response:  # pragma: nocover
            default_logger.warning(
                "Response: {}\nMessage: {}".format("success", response["result"])
            )
            return response["result"]
        raise Exception("airdrop failed")

    @staticmethod
    def generate_wealth_if_needed(
        api,
        address,
        min_amount=None,
    ) -> Union[str, None]:
        balance = api.get_balance(address)

        min_balance = min_amount if min_amount is not None else 1000000000
        if balance >= min_balance:
            return "not required"
        else:
            faucet = SolanaFaucetApi()
            cnt = 0
            transaction_digest = None
            while transaction_digest is None and cnt < 10:
                transaction_digest = faucet._try_get_wealth(address)
                cnt += 1
                time.sleep(5)

            if transaction_digest is None:
                return "failed"
            else:
                _, is_settled = api.wait_get_receipt(transaction_digest)
                if is_settled is True:
                    return "success"
                else:
                    return "failed"
