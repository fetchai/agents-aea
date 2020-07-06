<a name=".aea.crypto.ledger_apis"></a>
# aea.crypto.ledger`_`apis

Module wrapping all the public and private keys cryptography.

<a name=".aea.crypto.ledger_apis.LedgerApis"></a>
## LedgerApis Objects

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

<a name=".aea.crypto.ledger_apis.LedgerApis.default_ledger_id"></a>
#### default`_`ledger`_`id

```python
 | @property
 | default_ledger_id() -> str
```

Get the default ledger id.

<a name=".aea.crypto.ledger_apis.LedgerApis.get_balance"></a>
#### get`_`balance

```python
 | get_balance(identifier: str, address: str) -> Optional[int]
```

Get the token balance.

**Arguments**:

- `identifier`: the identifier of the ledger
- `address`: the address to check for

**Returns**:

the token balance

<a name=".aea.crypto.ledger_apis.LedgerApis.get_transfer_transaction"></a>
#### get`_`transfer`_`transaction

```python
 | get_transfer_transaction(identifier: str, sender_address: str, destination_address: str, amount: int, tx_fee: int, tx_nonce: str, **kwargs, ,) -> Optional[Any]
```

Get a transaction to transfer from self to destination.

**Arguments**:

- `identifier`: the identifier of the ledger
- `sender_address`: the address of the sender
- `destination_address`: the address of the receiver
- `amount`: the amount
- `tx_nonce`: verifies the authenticity of the tx
- `tx_fee`: the tx fee

**Returns**:

tx

<a name=".aea.crypto.ledger_apis.LedgerApis.send_signed_transaction"></a>
#### send`_`signed`_`transaction

```python
 | send_signed_transaction(identifier: str, tx_signed: Any) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_signed`: the signed transaction

**Returns**:

the tx_digest, if present

<a name=".aea.crypto.ledger_apis.LedgerApis.get_transaction_receipt"></a>
#### get`_`transaction`_`receipt

```python
 | get_transaction_receipt(identifier: str, tx_digest: str) -> Optional[Any]
```

Get the transaction receipt for a transaction digest.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx receipt, if present

<a name=".aea.crypto.ledger_apis.LedgerApis.get_transaction"></a>
#### get`_`transaction

```python
 | get_transaction(identifier: str, tx_digest: str) -> Optional[Any]
```

Get the transaction for a transaction digest.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx, if present

<a name=".aea.crypto.ledger_apis.LedgerApis.is_transaction_settled"></a>
#### is`_`transaction`_`settled

```python
 | @staticmethod
 | is_transaction_settled(identifier: str, tx_receipt: Any) -> bool
```

Check whether the transaction is settled and correct.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_receipt`: the transaction digest

**Returns**:

True if correctly settled, False otherwise

<a name=".aea.crypto.ledger_apis.LedgerApis.is_transaction_valid"></a>
#### is`_`transaction`_`valid

```python
 | @staticmethod
 | is_transaction_valid(identifier: str, tx: Any, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
```

Check whether the transaction is valid.

**Arguments**:

- `identifier`: Ledger identifier
- `tx`: the transaction
- `seller`: the address of the seller.
- `client`: the address of the client.
- `tx_nonce`: the transaction nonce.
- `amount`: the amount we expect to get from the transaction.

**Returns**:

True if is valid , False otherwise

<a name=".aea.crypto.ledger_apis.LedgerApis.generate_tx_nonce"></a>
#### generate`_`tx`_`nonce

```python
 | @staticmethod
 | generate_tx_nonce(identifier: str, seller: Address, client: Address) -> str
```

Generate a random str message.

**Arguments**:

- `identifier`: ledger identifier.
- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

