<a name=".aea.crypto.ledger_apis"></a>
## aea.crypto.ledger`_`apis

Module wrapping all the public and private keys cryptography.

<a name=".aea.crypto.ledger_apis.LedgerApis"></a>
### LedgerApis

```python
class LedgerApis()
```

Store all the ledger apis we initialise.

<a name=".aea.crypto.ledger_apis.LedgerApis.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_api_configs: Dict[str, Dict[str, Union[str, int]]], default_ledger_id: str)
```

Instantiate a wallet object.

**Arguments**:

- `ledger_api_configs`: the ledger api configs.
- `default_ledger_id`: the default ledger id.

<a name=".aea.crypto.ledger_apis.LedgerApis.configs"></a>
#### configs

```python
 | @property
 | configs() -> Dict[str, Dict[str, Union[str, int]]]
```

Get the configs.

<a name=".aea.crypto.ledger_apis.LedgerApis.apis"></a>
#### apis

```python
 | @property
 | apis() -> Dict[str, LedgerApi]
```

Get the apis.

<a name=".aea.crypto.ledger_apis.LedgerApis.has_ledger"></a>
#### has`_`ledger

```python
 | has_ledger(identifier: str) -> bool
```

Check if it has a .

<a name=".aea.crypto.ledger_apis.LedgerApis.get_api"></a>
#### get`_`api

```python
 | get_api(identifier: str) -> LedgerApi
```

Get the ledger API.

<a name=".aea.crypto.ledger_apis.LedgerApis.has_default_ledger"></a>
#### has`_`default`_`ledger

```python
 | @property
 | has_default_ledger() -> bool
```

Check if it has the default ledger API.

<a name=".aea.crypto.ledger_apis.LedgerApis.last_tx_statuses"></a>
#### last`_`tx`_`statuses

```python
 | @property
 | last_tx_statuses() -> Dict[str, str]
```

Get last tx statuses.

<a name=".aea.crypto.ledger_apis.LedgerApis.default_ledger_id"></a>
#### default`_`ledger`_`id

```python
 | @property
 | default_ledger_id() -> str
```

Get the default ledger id.

<a name=".aea.crypto.ledger_apis.LedgerApis.token_balance"></a>
#### token`_`balance

```python
 | token_balance(identifier: str, address: str) -> int
```

Get the token balance.

**Arguments**:

- `identifier`: the identifier of the ledger
- `address`: the address to check for

**Returns**:

the token balance

<a name=".aea.crypto.ledger_apis.LedgerApis.transfer"></a>
#### transfer

```python
 | transfer(crypto_object: Crypto, destination_address: str, amount: int, tx_fee: int, tx_nonce: str, **kwargs) -> Optional[str]
```

Transfer from self to destination.

**Arguments**:

- `tx_nonce`: verifies the authenticity of the tx
- `crypto_object`: the crypto object that contains the fucntions for signing transactions.
- `destination_address`: the address of the receive
- `amount`: the amount
- `tx_fee`: the tx fee

**Returns**:

tx digest if successful, otherwise None

<a name=".aea.crypto.ledger_apis.LedgerApis.send_signed_transaction"></a>
#### send`_`signed`_`transaction

```python
 | send_signed_transaction(identifier: str, tx_signed: Any) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `tx_signed`: the signed transaction

**Returns**:

the tx_digest, if present

<a name=".aea.crypto.ledger_apis.LedgerApis.is_transaction_settled"></a>
#### is`_`transaction`_`settled

```python
 | is_transaction_settled(identifier: str, tx_digest: str) -> bool
```

Check whether the transaction is settled and correct.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_digest`: the transaction digest

**Returns**:

True if correctly settled, False otherwise

<a name=".aea.crypto.ledger_apis.LedgerApis.is_tx_valid"></a>
#### is`_`tx`_`valid

```python
 | is_tx_valid(identifier: str, tx_digest: str, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
```

Kept for backwards compatibility!

<a name=".aea.crypto.ledger_apis.LedgerApis.is_transaction_valid"></a>
#### is`_`transaction`_`valid

```python
 | is_transaction_valid(identifier: str, tx_digest: str, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
```

Check whether the transaction is valid

**Arguments**:

- `identifier`: Ledger identifier
- `tx_digest`: the transaction digest
- `seller`: the address of the seller.
- `client`: the address of the client.
- `tx_nonce`: the transaction nonce.
- `amount`: the amount we expect to get from the transaction.

**Returns**:

True if is valid , False otherwise

<a name=".aea.crypto.ledger_apis.LedgerApis.generate_tx_nonce"></a>
#### generate`_`tx`_`nonce

```python
 | generate_tx_nonce(identifier: str, seller: Address, client: Address) -> str
```

Generate a random str message.

**Arguments**:

- `identifier`: ledger identifier.
- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

