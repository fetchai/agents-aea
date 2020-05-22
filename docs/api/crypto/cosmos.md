<a name=".aea.crypto.cosmos"></a>
## aea.crypto.cosmos

Cosmos module wrapping the public and private key cryptography and ledger api.

<a name=".aea.crypto.cosmos.CosmosCrypto"></a>
### CosmosCrypto

```python
class CosmosCrypto(Crypto[SigningKey])
```

Class wrapping the Account Generation from Ethereum ledger.

<a name=".aea.crypto.cosmos.CosmosCrypto.__init__"></a>
#### `__`init`__`

```python
 | __init__(private_key_path: Optional[str] = None)
```

Instantiate an ethereum crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent

<a name=".aea.crypto.cosmos.CosmosCrypto.public_key"></a>
#### public`_`key

```python
 | @property
 | public_key() -> str
```

Return a public key in hex format.

**Returns**:

a public key string in hex format

<a name=".aea.crypto.cosmos.CosmosCrypto.address"></a>
#### address

```python
 | @property
 | address() -> str
```

Return the address for the key pair.

**Returns**:

a display_address str

<a name=".aea.crypto.cosmos.CosmosCrypto.load_private_key_from_path"></a>
#### load`_`private`_`key`_`from`_`path

```python
 | @classmethod
 | load_private_key_from_path(cls, file_name) -> SigningKey
```

Load a private key in hex format from a file.

**Arguments**:

- `file_name`: the path to the hex file.

**Returns**:

the Entity.

<a name=".aea.crypto.cosmos.CosmosCrypto.sign_message"></a>
#### sign`_`message

```python
 | sign_message(message: bytes, is_deprecated_mode: bool = False) -> str
```

Sign a message in bytes string form.

**Arguments**:

- `message`: the message to be signed
- `is_deprecated_mode`: if the deprecated signing is used

**Returns**:

signature of the message in string form

<a name=".aea.crypto.cosmos.CosmosCrypto.sign_transaction"></a>
#### sign`_`transaction

```python
 | sign_transaction(transaction: Any) -> Any
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed

**Returns**:

signed transaction

<a name=".aea.crypto.cosmos.CosmosCrypto.recover_message"></a>
#### recover`_`message

```python
 | recover_message(message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[Address, ...]
```

Recover the addresses from the hash.

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered addresses

<a name=".aea.crypto.cosmos.CosmosCrypto.generate_private_key"></a>
#### generate`_`private`_`key

```python
 | @classmethod
 | generate_private_key(cls) -> SigningKey
```

Generate a key pair for cosmos network.

<a name=".aea.crypto.cosmos.CosmosCrypto.get_address_from_public_key"></a>
#### get`_`address`_`from`_`public`_`key

```python
 | @classmethod
 | get_address_from_public_key(cls, public_key: str) -> str
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a name=".aea.crypto.cosmos.CosmosCrypto.dump"></a>
#### dump

```python
 | dump(fp: BinaryIO) -> None
```

Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

**Arguments**:

- `fp`: the output file pointer. Must be set in binary mode (mode='wb')

**Returns**:

None

<a name=".aea.crypto.cosmos.CosmosApi"></a>
### CosmosApi

```python
class CosmosApi(LedgerApi)
```

Class to interact with the Cosmos SDK via a HTTP APIs.

<a name=".aea.crypto.cosmos.CosmosApi.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs)
```

Initialize the Ethereum ledger APIs.

**Arguments**:

- `address`: the endpoint for Web3 APIs.

<a name=".aea.crypto.cosmos.CosmosApi.api"></a>
#### api

```python
 | @property
 | api() -> None
```

Get the underlying API object.

<a name=".aea.crypto.cosmos.CosmosApi.get_balance"></a>
#### get`_`balance

```python
 | get_balance(address: Address) -> Optional[int]
```

Get the balance of a given account.

<a name=".aea.crypto.cosmos.CosmosApi.transfer"></a>
#### transfer

```python
 | transfer(crypto: Crypto, destination_address: Address, amount: int, tx_fee: int, tx_nonce: str = "", denom: str = "testfet", account_number: int = 0, sequence: int = 0, gas: int = 80000, memo: str = "", sync_mode: str = "sync", chain_id: str = "aea-testnet", **kwargs, ,) -> Optional[str]
```

Submit a transfer transaction to the ledger.

**Arguments**:

- `crypto`: the crypto object associated to the payer.
- `destination_address`: the destination address of the payee.
- `amount`: the amount of wealth to be transferred.
- `tx_fee`: the transaction fee.
- `tx_nonce`: verifies the authenticity of the tx
- `chain_id`: the Chain ID of the Ethereum transaction. Default is 1 (i.e. mainnet).

**Returns**:

tx digest if present, otherwise None

<a name=".aea.crypto.cosmos.CosmosApi.send_signed_transaction"></a>
#### send`_`signed`_`transaction

```python
 | send_signed_transaction(tx_signed: Any) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `tx_signed`: the signed transaction

**Returns**:

tx_digest, if present

<a name=".aea.crypto.cosmos.CosmosApi.is_transaction_settled"></a>
#### is`_`transaction`_`settled

```python
 | is_transaction_settled(tx_digest: str) -> bool
```

Check whether a transaction is settled or not.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

True if the transaction has been settled, False o/w.

<a name=".aea.crypto.cosmos.CosmosApi.get_transaction_receipt"></a>
#### get`_`transaction`_`receipt

```python
 | get_transaction_receipt(tx_digest: str) -> Optional[Any]
```

Get the transaction receipt for a transaction digest (non-blocking).

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx receipt, if present

<a name=".aea.crypto.cosmos.CosmosApi.generate_tx_nonce"></a>
#### generate`_`tx`_`nonce

```python
 | generate_tx_nonce(seller: Address, client: Address) -> str
```

Generate a unique hash to distinguish txs with the same terms.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

<a name=".aea.crypto.cosmos.CosmosApi.is_transaction_valid"></a>
#### is`_`transaction`_`valid

```python
 | is_transaction_valid(tx_digest: str, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
```

Check whether a transaction is valid or not (non-blocking).

**Arguments**:

- `tx_digest`: the transaction digest.
- `seller`: the address of the seller.
- `client`: the address of the client.
- `tx_nonce`: the transaction nonce.
- `amount`: the amount we expect to get from the transaction.

**Returns**:

True if the random_message is equals to tx['input']

<a name=".aea.crypto.cosmos.CosmosFaucetApi"></a>
### CosmosFaucetApi

```python
class CosmosFaucetApi(FaucetApi)
```

Cosmos testnet faucet API.

<a name=".aea.crypto.cosmos.CosmosFaucetApi.get_wealth"></a>
#### get`_`wealth

```python
 | get_wealth(address: Address) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.

**Returns**:

None

