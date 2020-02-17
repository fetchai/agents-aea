In this section, we show you how to integrate the AEA with the Fetch.ai and third-party ledgers.

The framework currently natively supports two ledgers:

- Fetch.ai
- Ethereum

To this end, the framework wraps APIs to interact with the two ledgers and exposes them in the `LedgerApis` class. The framework also wraps the account APIs to create identities on both ledgers and exposes them in the `Wallet`.

The `Wallet` holds instantiation of the abstract `Crypto` base class, in particular `FetchaiCrypto` and `EthereumCrypto`.

The `LedgerApis` holds instantiation of the abstract `LedgerApi` base class, in particular `FetchaiLedgerApi` and `EthereumLedgerApi`.
You can think the concrete implementations of the base class `LedgerApi` as wrappers of the blockchain specific python SDK. 


## Abstract class LedgerApi

Each `LedgerApi` must implement all the methods based on the abstract class.
```python
class LedgerApi(ABC):
    """Interface for ledger APIs."""

    identifier = "base"  # type: str

    @property
    @abstractmethod
    def api(self) -> Any:
        """
        Get the underlying API object.
        If there is no such object, return None.
        """
```
The api property can be used for low-level operation with the concrete ledger APIs.

```python

    @abstractmethod
    def get_balance(self, address: AddressLike) -> int:
        """
        Get the balance of a given account.

        This usually takes the form of a web request to be waited synchronously.

        :param address: the address.
        :return: the balance.
        """
```
The `get_balance` method returns the amount of tokens we hold for a specific address.
```python

    @abstractmethod
    def send_transaction(
        self,
        crypto: Crypto,
        destination_address: AddressLike,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        **kwargs
    ) -> Optional[str]:
        """
        Submit a transaction to the ledger.

        If the mandatory arguments are not enough for specifying a transaction
        in the concrete ledger API, use keyword arguments for the additional parameters.

        :param tx_nonce: verifies the authenticity of the tx
        :param crypto: the crypto object associated to the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :return: tx digest if successful, otherwise None
        """
```
The `send_transaction` is where we must implement the logic for sending a transaction to the ledger. 

```python
    @abstractmethod
    def is_transaction_settled(self, tx_digest: str) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_digest: the digest associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """

    @abstractmethod
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

        :return: True if the transaction referenced by the tx_digest matches the terms.
        """
```
The `is_transaction_settled` and `validate_transaction` are two functions that helps us to verify a transaction digest.
```python
    @abstractmethod
    def generate_tx_nonce(self, seller: Address, client: Address) -> str:
        """
        Generate a random str message.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
```
Lastly, we implemented a support function that generates a random hash to help us with verifying the uniqueness of transactions. The sender of the funds must include this hash in the transaction
as extra data for the transaction to be considered valid.

Next, we are going to discuss the different implementation of `send_transaction` and `validate_transacaction` for the two natively supported ledgers of the framework.

## Fetch.ai Ledger
```python
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
```
As you can see, the implementation for sending a transcation to the Fetch.ai ledger is relatively trivial.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>We cannot use the tx_nonce yet in the Fetch.ai ledger.</p>
</div>

```python
    def is_transaction_settled(self, tx_digest: str) -> bool:
         """Check whether a transaction is settled or not."""
         tx_status = cast(TxStatus, self._api.tx.status(tx_digest))
         is_successful = False
         if tx_status.status in SUCCESSFUL_TERMINAL_STATES:
             is_successful = True
         return is_successful
```
```python
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
```
Inside the `validate_transcation` we request the contents of the transaction based on the tx_digest we received. We are checking that the address
of the client is the same as the one that is inside the `from` field of the transaction. Lastly, we are checking that the transaction is settled.
If both of these checks return True we consider the transaction as valid.

## Ethereum Ledger

```python
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
```
On contrary to the Fetch.ai implementation of the `send_transaction` function, the Ethereum implementation is more complicated. This happens because we must create 
the transaction dictionary and send a raw transaction.

- The `nonce` is a counter for the transaction we are sending. This is an auto-increment int based on how many transactions we are sending from the specific account.
- The `chain_id` specifies if we are trying to reach the `mainnet` or another `testnet`.
- The `to` field is the address we want to send the funds.
- The `value` is the number of tokens we want to transfer.
- The `gas` is the price we are paying to be able to send the transaction.
- The `gasPrice` is the price of the gas we want to pay.
- The `data` in the field that enables to send custom data (originally is used to send data to a smart contract).

Once we filled the transaction dictionary. We are checking that the transaction fee is more than the estimated gas for the transaction otherwise we will not be able to complete the transfer. Then we are signing and we are sending the transaction. Once we get the transaction receipt we consider the transaction completed and
we return the transaction digest. 

```python
 def is_transaction_settled(self, tx_digest: str) -> bool:
         """Check whether a transaction is settled or not."""
         tx_status = self._api.eth.getTransactionReceipt(tx_digest)
         is_successful = False
         if tx_status is not None:
             is_successful = True
         return is_successful
```
```python
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
The `validate_transaction` and `is_transaction_settled` functions help us to check if a transaction digest is valid and is settled. 
In the Ethereum API, we can pass the `tx_nonce`, so we can check that it's the same. If it is different, we consider that transaction as no valid. The same happens if any of `amount`, `client` address
or the `seller` address is different.

Lastly, the `generate_tx_nonce` function is the same for both `LedgerApi` implementations but we use different hashing functions. 
Both use the timestamp as a random factor alongside the seller and client addresses.

#### Fetch.ai implementation 
```python
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
#### Ethereum implementation
```python
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
```
