In this section, we show you how to integrate the AEA with the Fetch.ai and third-party ledgers.

The framework currently natively supports two ledgers:

- Fetch.ai
- Ethereum

To this end, the framework wraps APIs to interact with the two ledgers and exposes them in the `LedgerApis` class. The framework also wraps the account APIs to create identities on both ledgers and exposes them in the `Wallet`.

The `Wallet` holds instantiation of the abstract `Crypto` base class, in particular `FetchaiCrypto` and `EthereumCrypto`.

The `LedgerApis` holds instantiation of the abstract `LedgerApi` base class, in particular `FetchaiLedgerApi` and `EthereumLedgerApi`.
You can consider the `Ledger Api` implementation of each block-chain as a wrapper of their python library. 


## Fetch.ai Ledger

```python
class FetchAIApi(LedgerApi):
    """Class to interact with the Fetch ledger APIs."""

    identifier = FETCHAI

    def __init__(self, **kwargs):
        """
        Initialize the Fetch.AI ledger APIs.

        :param kwargs: key word arguments (expects either a pair of 'host' and 'port' or a 'network')
        """
        self._api = FetchaiLedgerApi(**kwargs)

    @property
    def api(self) -> FetchaiLedgerApi:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: AddressLike) -> int:
        """Get the balance of a given account."""
        return self._api.tokens.balance(address)

    def send_transaction(
        self,
        crypto: Crypto,
        destination_address: AddressLike,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        **kwargs
    ) -> Optional[str]:
        """Submit a transaction to the ledger."""
        tx_digest = self._api.tokens.transfer(
            crypto.entity, destination_address, amount, tx_fee
        )
        self._api.sync(tx_digest)
        return tx_digest

    def is_transaction_settled(self, tx_digest: str) -> bool:
        """Check whether a transaction is settled or not."""
        tx_status = cast(TxStatus, self._api.tx.status(tx_digest))
        is_successful = False
        if tx_status.status in SUCCESSFUL_TERMINAL_STATES:
            is_successful = True
        return is_successful

    def validate_transaction(
        self,
        tx_digest: str,
        seller: Address,
        client: Address,
        tx_nonce: str,
        amount: int,
    ) -> bool:
        """
        Check whether a transaction is valid or not.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.
        :param tx_digest: the transaction digest.

        :return: True if the random_message is equals to tx['input']
        """
        tx_contents = cast(TxContents, self._api.tx.contents(tx_digest))
        transfers = tx_contents.transfers
        seller_address = Address(seller)
        is_valid = (
            str(tx_contents.from_address) == client
            and amount == transfers[seller_address]
        )
        is_settled = self.is_transaction_settled(tx_digest=tx_digest)
        result = is_valid and is_settled
        return result

    def generate_tx_nonce(self, seller: Address, client: Address) -> str:
        """
        Generate a random str message.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """

        time_stamp = int(time.time())
        seller = cast(str, seller)
        client = cast(str, client)
        aggregate_hash = sha256_hash(
            b"".join([seller.encode(), client.encode(), time_stamp.to_bytes(32, "big")])
        )

        return aggregate_hash.hex()
```

## Ethereum Ledger

```python
class EthereumApi(LedgerApi):
    """Class to interact with the Ethereum Web3 APIs."""

    identifier = ETHEREUM

    def __init__(self, address: str, gas_price: str = DEFAULT_GAS_PRICE):
        """
        Initialize the Ethereum ledger APIs.

        :param address: the endpoint for Web3 APIs.
        """
        self._api = Web3(HTTPProvider(endpoint_uri=address))
        self._gas_price = gas_price

    @property
    def api(self) -> Web3:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: AddressLike) -> int:
        """Get the balance of a given account."""
        return self._api.eth.getBalance(address)

    def send_transaction(
        self,
        crypto: Crypto,
        destination_address: AddressLike,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        chain_id: int = 3,
        **kwargs
    ) -> Optional[str]:
        """
        Submit a transaction to the ledger.

        :param tx_nonce: verifies the authenticity of the tx
        :param crypto: the crypto object associated to the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :param chain_id: the Chain ID of the Ethereum transaction. Default is 1 (i.e. mainnet).
        :return: the transaction digest, or None if not available.
        """
        nonce = self._api.eth.getTransactionCount(
            self._api.toChecksumAddress(crypto.address)
        )

        # TODO : handle misconfiguration
        transaction = {
            "nonce": nonce,
            "chainId": chain_id,
            "to": destination_address,
            "value": amount,
            "gas": tx_fee,
            "gasPrice": self._api.toWei(self._gas_price, GAS_ID),
            "data": tx_nonce,
        }
        gas_estimation = self._api.eth.estimateGas(transaction=transaction)
        assert (
            tx_fee >= gas_estimation
        ), "Need to increase tx_fee in the configs to cover the gas consumption of the transaction. Estimated gas consumption is: {}.".format(
            gas_estimation
        )
        signed = self._api.eth.account.signTransaction(transaction, crypto.entity.key)

        hex_value = self._api.eth.sendRawTransaction(signed.rawTransaction)

        logger.info("TX Hash: {}".format(str(hex_value.hex())))
        while True:
            try:
                self._api.eth.getTransactionReceipt(hex_value)
                logger.info("transaction validated - exiting")
                tx_digest = hex_value.hex()
                break
            except web3.exceptions.TransactionNotFound:  # pragma: no cover
                logger.info("transaction not found - sleeping for 3.0 seconds")
                time.sleep(3.0)
        return tx_digest

    def is_transaction_settled(self, tx_digest: str) -> bool:
        """Check whether a transaction is settled or not."""
        tx_status = self._api.eth.getTransactionReceipt(tx_digest)
        is_successful = False
        if tx_status is not None:
            is_successful = True
        return is_successful

    def generate_tx_nonce(self, seller: Address, client: Address) -> str:
        """
        Generate a unique hash to distinguish txs with the same terms.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        time_stamp = int(time.time())
        aggregate_hash = Web3.keccak(
            b"".join([seller.encode(), client.encode(), time_stamp.to_bytes(32, "big")])
        )
        return aggregate_hash.hex()

    def validate_transaction(
        self,
        tx_digest: str,
        seller: Address,
        client: Address,
        tx_nonce: str,
        amount: int,
    ) -> bool:
        """
        Check whether a transaction is valid or not.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.
        :param tx_digest: the transaction digest.

        :return: True if the random_message is equals to tx['input']
        """

        tx = self._api.eth.getTransaction(tx_digest)
        is_valid = (
            tx.get("input") == tx_nonce
            and tx.get("value") == amount
            and tx.get("from") == client
            and tx.get("to") == seller
        )
        return is_valid
```

