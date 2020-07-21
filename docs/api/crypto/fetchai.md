<a name="aea.crypto.fetchai"></a>
# aea.crypto.fetchai

Fetchai module wrapping the public and private key cryptography and ledger api.

<a name="aea.crypto.fetchai.FetchAICrypto"></a>
## FetchAICrypto Objects

```python
class FetchAICrypto(Crypto[Entity])
```

Class wrapping the Entity Generation from Fetch.AI ledger.

<a name="aea.crypto.fetchai.FetchAICrypto.__init__"></a>
#### `__`init`__`

```python
 | __init__(private_key_path: Optional[str] = None)
```

Instantiate a fetchai crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent

<a name="aea.crypto.fetchai.FetchAICrypto.private_key"></a>
#### private`_`key

```python
 | @property
 | private_key() -> str
```

Return a private key.

**Returns**:

a private key string

<a name="aea.crypto.fetchai.FetchAICrypto.public_key"></a>
#### public`_`key

```python
 | @property
 | public_key() -> str
```

Return a public key in hex format.

**Returns**:

a public key string in hex format

<a name="aea.crypto.fetchai.FetchAICrypto.address"></a>
#### address

```python
 | @property
 | address() -> str
```

Return the address for the key pair.

**Returns**:

a display_address str

<a name="aea.crypto.fetchai.FetchAICrypto.load_private_key_from_path"></a>
#### load`_`private`_`key`_`from`_`path

```python
 | @classmethod
 | load_private_key_from_path(cls, file_name: str) -> Entity
```

Load a private key in hex format from a file.

**Arguments**:

- `file_name`: the path to the hex file.

**Returns**:

the Entity.

<a name="aea.crypto.fetchai.FetchAICrypto.generate_private_key"></a>
#### generate`_`private`_`key

```python
 | @classmethod
 | generate_private_key(cls) -> Entity
```

Generate a key pair for fetchai network.

<a name="aea.crypto.fetchai.FetchAICrypto.sign_message"></a>
#### sign`_`message

```python
 | sign_message(message: bytes, is_deprecated_mode: bool = False) -> str
```

Sign a message in bytes string form.

**Arguments**:

- `message`: the message we want to send
- `is_deprecated_mode`: if the deprecated signing is used

**Returns**:

signature of the message in string form

<a name="aea.crypto.fetchai.FetchAICrypto.sign_transaction"></a>
#### sign`_`transaction

```python
 | sign_transaction(transaction: Any) -> Any
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed

**Returns**:

signed transaction

<a name="aea.crypto.fetchai.FetchAICrypto.dump"></a>
#### dump

```python
 | dump(fp: BinaryIO) -> None
```

Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

**Arguments**:

- `fp`: the output file pointer. Must be set in binary mode (mode='wb')

**Returns**:

None

<a name="aea.crypto.fetchai.FetchAIHelper"></a>
## FetchAIHelper Objects

```python
class FetchAIHelper(Helper)
```

Helper class usable as Mixin for FetchAIApi or as standalone class.

<a name="aea.crypto.fetchai.FetchAIHelper.is_transaction_settled"></a>
#### is`_`transaction`_`settled

```python
 | @staticmethod
 | is_transaction_settled(tx_receipt: Any) -> bool
```

Check whether a transaction is settled or not.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

True if the transaction has been settled, False o/w.

<a name="aea.crypto.fetchai.FetchAIHelper.is_transaction_valid"></a>
#### is`_`transaction`_`valid

```python
 | @staticmethod
 | is_transaction_valid(tx: Any, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
```

Check whether a transaction is valid or not.

**Arguments**:

- `tx`: the transaction.
- `seller`: the address of the seller.
- `client`: the address of the client.
- `tx_nonce`: the transaction nonce.
- `amount`: the amount we expect to get from the transaction.

**Returns**:

True if the random_message is equals to tx['input']

<a name="aea.crypto.fetchai.FetchAIHelper.generate_tx_nonce"></a>
#### generate`_`tx`_`nonce

```python
 | @staticmethod
 | generate_tx_nonce(seller: Address, client: Address) -> str
```

Generate a unique hash to distinguish txs with the same terms.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

<a name="aea.crypto.fetchai.FetchAIHelper.get_address_from_public_key"></a>
#### get`_`address`_`from`_`public`_`key

```python
 | @staticmethod
 | get_address_from_public_key(public_key: str) -> Address
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a name="aea.crypto.fetchai.FetchAIHelper.recover_message"></a>
#### recover`_`message

```python
 | @staticmethod
 | recover_message(message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[Address, ...]
```

Recover the addresses from the hash.

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered addresses

<a name="aea.crypto.fetchai.FetchAIApi"></a>
## FetchAIApi Objects

```python
class FetchAIApi(LedgerApi,  FetchAIHelper)
```

Class to interact with the Fetch ledger APIs.

<a name="aea.crypto.fetchai.FetchAIApi.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs)
```

Initialize the Fetch.AI ledger APIs.

**Arguments**:

- `kwargs`: key word arguments (expects either a pair of 'host' and 'port' or a 'network')

<a name="aea.crypto.fetchai.FetchAIApi.api"></a>
#### api

```python
 | @property
 | api() -> FetchaiLedgerApi
```

Get the underlying API object.

<a name="aea.crypto.fetchai.FetchAIApi.get_balance"></a>
#### get`_`balance

```python
 | get_balance(address: Address) -> Optional[int]
```

Get the balance of a given account.

**Arguments**:

- `address`: the address for which to retrieve the balance.

**Returns**:

the balance, if retrivable, otherwise None

<a name="aea.crypto.fetchai.FetchAIApi.get_transfer_transaction"></a>
#### get`_`transfer`_`transaction

```python
 | get_transfer_transaction(sender_address: Address, destination_address: Address, amount: int, tx_fee: int, tx_nonce: str, **kwargs, ,) -> Optional[Any]
```

Submit a transfer transaction to the ledger.

**Arguments**:

- `sender_address`: the sender address of the payer.
- `destination_address`: the destination address of the payee.
- `amount`: the amount of wealth to be transferred.
- `tx_fee`: the transaction fee.
- `tx_nonce`: verifies the authenticity of the tx

**Returns**:

the transfer transaction

<a name="aea.crypto.fetchai.FetchAIApi.send_signed_transaction"></a>
#### send`_`signed`_`transaction

```python
 | send_signed_transaction(tx_signed: Any) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `tx_signed`: the signed transaction

<a name="aea.crypto.fetchai.FetchAIApi.get_transaction_receipt"></a>
#### get`_`transaction`_`receipt

```python
 | get_transaction_receipt(tx_digest: str) -> Optional[Any]
```

Get the transaction receipt for a transaction digest (non-blocking).

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx receipt, if present

<a name="aea.crypto.fetchai.FetchAIApi.get_transaction"></a>
#### get`_`transaction

```python
 | get_transaction(tx_digest: str) -> Optional[Any]
```

Get the transaction for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx, if present

<a name="aea.crypto.fetchai.FetchAIFaucetApi"></a>
## FetchAIFaucetApi Objects

```python
class FetchAIFaucetApi(FaucetApi)
```

Fetchai testnet faucet API.

<a name="aea.crypto.fetchai.FetchAIFaucetApi.get_wealth"></a>
#### get`_`wealth

```python
 | get_wealth(address: Address) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.

**Returns**:

None

