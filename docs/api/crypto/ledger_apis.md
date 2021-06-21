<a name="aea.crypto.ledger_apis"></a>
# aea.crypto.ledger`_`apis

Module wrapping all the public and private keys cryptography.

<a name="aea.crypto.ledger_apis.LedgerApis"></a>
## LedgerApis Objects

```python
class LedgerApis()
```

Store all the ledger apis we initialise.

<a name="aea.crypto.ledger_apis.LedgerApis.has_ledger"></a>
#### has`_`ledger

```python
 | @staticmethod
 | has_ledger(identifier: str) -> bool
```

Check if it has the api.

<a name="aea.crypto.ledger_apis.LedgerApis.get_api"></a>
#### get`_`api

```python
 | @classmethod
 | get_api(cls, identifier: str) -> LedgerApi
```

Get the ledger API.

<a name="aea.crypto.ledger_apis.LedgerApis.get_balance"></a>
#### get`_`balance

```python
 | @classmethod
 | get_balance(cls, identifier: str, address: str) -> Optional[int]
```

Get the token balance.

**Arguments**:

- `identifier`: the identifier of the ledger
- `address`: the address to check for

**Returns**:

the token balance

<a name="aea.crypto.ledger_apis.LedgerApis.get_transfer_transaction"></a>
#### get`_`transfer`_`transaction

```python
 | @classmethod
 | get_transfer_transaction(cls, identifier: str, sender_address: str, destination_address: str, amount: int, tx_fee: int, tx_nonce: str, **kwargs: Any, ,) -> Optional[Any]
```

Get a transaction to transfer from self to destination.

**Arguments**:

- `identifier`: the identifier of the ledger
- `sender_address`: the address of the sender
- `destination_address`: the address of the receiver
- `amount`: the amount
- `tx_nonce`: verifies the authenticity of the tx
- `tx_fee`: the tx fee
- `kwargs`: the keyword arguments.

**Returns**:

tx

<a name="aea.crypto.ledger_apis.LedgerApis.send_signed_transaction"></a>
#### send`_`signed`_`transaction

```python
 | @classmethod
 | send_signed_transaction(cls, identifier: str, tx_signed: Any) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_signed`: the signed transaction

**Returns**:

the tx_digest, if present

<a name="aea.crypto.ledger_apis.LedgerApis.get_transaction_receipt"></a>
#### get`_`transaction`_`receipt

```python
 | @classmethod
 | get_transaction_receipt(cls, identifier: str, tx_digest: str) -> Optional[Any]
```

Get the transaction receipt for a transaction digest.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx receipt, if present

<a name="aea.crypto.ledger_apis.LedgerApis.get_transaction"></a>
#### get`_`transaction

```python
 | @classmethod
 | get_transaction(cls, identifier: str, tx_digest: str) -> Optional[Any]
```

Get the transaction for a transaction digest.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx, if present

<a name="aea.crypto.ledger_apis.LedgerApis.get_contract_address"></a>
#### get`_`contract`_`address

```python
 | @staticmethod
 | get_contract_address(identifier: str, tx_receipt: Any) -> Optional[Address]
```

Get the contract address from a transaction receipt.

**Arguments**:

- `identifier`: the identifier of the ledger
- `tx_receipt`: the transaction receipt

**Returns**:

the contract address if successful

<a name="aea.crypto.ledger_apis.LedgerApis.is_transaction_settled"></a>
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

<a name="aea.crypto.ledger_apis.LedgerApis.is_transaction_valid"></a>
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

<a name="aea.crypto.ledger_apis.LedgerApis.generate_tx_nonce"></a>
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

<a name="aea.crypto.ledger_apis.LedgerApis.recover_message"></a>
#### recover`_`message

```python
 | @staticmethod
 | recover_message(identifier: str, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[Address, ...]
```

Recover the addresses from the hash.

**Arguments**:

- `identifier`: ledger identifier.
- `message`: the message we expect
- `signature`: the transaction signature
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered addresses

<a name="aea.crypto.ledger_apis.LedgerApis.get_hash"></a>
#### get`_`hash

```python
 | @staticmethod
 | get_hash(identifier: str, message: bytes) -> str
```

Get the hash of a message.

**Arguments**:

- `identifier`: ledger identifier.
- `message`: the message to be hashed.

**Returns**:

the hash of the message.

<a name="aea.crypto.ledger_apis.LedgerApis.is_valid_address"></a>
#### is`_`valid`_`address

```python
 | @staticmethod
 | is_valid_address(identifier: str, address: Address) -> bool
```

Check if the address is valid.

**Arguments**:

- `identifier`: ledger identifier.
- `address`: the address to validate.

**Returns**:

whether it is a valid address or not.

