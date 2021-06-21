<a name="aea.helpers.transaction.base"></a>
# aea.helpers.transaction.base

This module contains terms related classes.

<a name="aea.helpers.transaction.base.RawTransaction"></a>
## RawTransaction Objects

```python
class RawTransaction()
```

This class represents an instance of RawTransaction.

<a name="aea.helpers.transaction.base.RawTransaction.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_id: str, body: JSONLike) -> None
```

Initialise an instance of RawTransaction.

<a name="aea.helpers.transaction.base.RawTransaction.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a name="aea.helpers.transaction.base.RawTransaction.body"></a>
#### body

```python
 | @property
 | body() -> JSONLike
```

Get the body.

<a name="aea.helpers.transaction.base.RawTransaction.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(raw_transaction_protobuf_object: Any, raw_transaction_object: "RawTransaction") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the raw_transaction_protobuf_object argument must be matched with the instance of this class in the 'raw_transaction_object' argument.

**Arguments**:

- `raw_transaction_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `raw_transaction_object`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.transaction.base.RawTransaction.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, raw_transaction_protobuf_object: Any) -> "RawTransaction"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.

**Arguments**:

- `raw_transaction_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.

<a name="aea.helpers.transaction.base.RawTransaction.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.transaction.base.RawTransaction.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.helpers.transaction.base.RawMessage"></a>
## RawMessage Objects

```python
class RawMessage()
```

This class represents an instance of RawMessage.

<a name="aea.helpers.transaction.base.RawMessage.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_id: str, body: bytes, is_deprecated_mode: bool = False) -> None
```

Initialise an instance of RawMessage.

<a name="aea.helpers.transaction.base.RawMessage.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a name="aea.helpers.transaction.base.RawMessage.body"></a>
#### body

```python
 | @property
 | body() -> bytes
```

Get the body.

<a name="aea.helpers.transaction.base.RawMessage.is_deprecated_mode"></a>
#### is`_`deprecated`_`mode

```python
 | @property
 | is_deprecated_mode() -> bool
```

Get the is_deprecated_mode.

<a name="aea.helpers.transaction.base.RawMessage.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(raw_message_protobuf_object: Any, raw_message_object: "RawMessage") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the raw_message_protobuf_object argument must be matched with the instance of this class in the 'raw_message_object' argument.

**Arguments**:

- `raw_message_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `raw_message_object`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.transaction.base.RawMessage.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, raw_message_protobuf_object: Any) -> "RawMessage"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.

**Arguments**:

- `raw_message_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.

<a name="aea.helpers.transaction.base.RawMessage.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.transaction.base.RawMessage.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.helpers.transaction.base.SignedTransaction"></a>
## SignedTransaction Objects

```python
class SignedTransaction()
```

This class represents an instance of SignedTransaction.

<a name="aea.helpers.transaction.base.SignedTransaction.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_id: str, body: JSONLike) -> None
```

Initialise an instance of SignedTransaction.

<a name="aea.helpers.transaction.base.SignedTransaction.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a name="aea.helpers.transaction.base.SignedTransaction.body"></a>
#### body

```python
 | @property
 | body() -> JSONLike
```

Get the body.

<a name="aea.helpers.transaction.base.SignedTransaction.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(signed_transaction_protobuf_object: Any, signed_transaction_object: "SignedTransaction") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the signed_transaction_protobuf_object argument must be matched with the instance of this class in the 'signed_transaction_object' argument.

**Arguments**:

- `signed_transaction_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `signed_transaction_object`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.transaction.base.SignedTransaction.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, signed_transaction_protobuf_object: Any) -> "SignedTransaction"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.

**Arguments**:

- `signed_transaction_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.

<a name="aea.helpers.transaction.base.SignedTransaction.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.transaction.base.SignedTransaction.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.helpers.transaction.base.SignedMessage"></a>
## SignedMessage Objects

```python
class SignedMessage()
```

This class represents an instance of RawMessage.

<a name="aea.helpers.transaction.base.SignedMessage.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_id: str, body: str, is_deprecated_mode: bool = False) -> None
```

Initialise an instance of SignedMessage.

<a name="aea.helpers.transaction.base.SignedMessage.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a name="aea.helpers.transaction.base.SignedMessage.body"></a>
#### body

```python
 | @property
 | body() -> str
```

Get the body.

<a name="aea.helpers.transaction.base.SignedMessage.is_deprecated_mode"></a>
#### is`_`deprecated`_`mode

```python
 | @property
 | is_deprecated_mode() -> bool
```

Get the is_deprecated_mode.

<a name="aea.helpers.transaction.base.SignedMessage.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(signed_message_protobuf_object: Any, signed_message_object: "SignedMessage") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the signed_message_protobuf_object argument must be matched with the instance of this class in the 'signed_message_object' argument.

**Arguments**:

- `signed_message_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `signed_message_object`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.transaction.base.SignedMessage.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, signed_message_protobuf_object: Any) -> "SignedMessage"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'signed_message_protobuf_object' argument.

**Arguments**:

- `signed_message_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'signed_message_protobuf_object' argument.

<a name="aea.helpers.transaction.base.SignedMessage.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.transaction.base.SignedMessage.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.helpers.transaction.base.State"></a>
## State Objects

```python
class State()
```

This class represents an instance of State.

<a name="aea.helpers.transaction.base.State.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_id: str, body: JSONLike) -> None
```

Initialise an instance of State.

<a name="aea.helpers.transaction.base.State.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a name="aea.helpers.transaction.base.State.body"></a>
#### body

```python
 | @property
 | body() -> JSONLike
```

Get the body.

<a name="aea.helpers.transaction.base.State.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(state_protobuf_object: Any, state_object: "State") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the state_protobuf_object argument must be matched with the instance of this class in the 'state_object' argument.

**Arguments**:

- `state_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `state_object`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.transaction.base.State.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, state_protobuf_object: Any) -> "State"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'state_protobuf_object' argument.

**Arguments**:

- `state_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'state_protobuf_object' argument.

<a name="aea.helpers.transaction.base.State.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.transaction.base.State.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.helpers.transaction.base.Terms"></a>
## Terms Objects

```python
class Terms()
```

Class to represent the terms of a multi-currency & multi-token ledger transaction.

<a name="aea.helpers.transaction.base.Terms.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_id: str, sender_address: Address, counterparty_address: Address, amount_by_currency_id: Dict[str, int], quantities_by_good_id: Dict[str, int], nonce: str, is_sender_payable_tx_fee: bool = True, fee_by_currency_id: Optional[Dict[str, int]] = None, is_strict: bool = False, **kwargs: Any, ,) -> None
```

Instantiate terms of a transaction.

**Arguments**:

- `ledger_id`: the ledger on which the terms are to be settled.
- `sender_address`: the sender address of the transaction.
- `counterparty_address`: the counterparty address of the transaction.
- `amount_by_currency_id`: the amount by the currency of the transaction.
- `quantities_by_good_id`: a map from good id to the quantity of that good involved in the transaction.
- `nonce`: nonce to be included in transaction to discriminate otherwise identical transactions.
- `is_sender_payable_tx_fee`: whether the sender or counterparty pays the tx fee.
- `fee_by_currency_id`: the fee associated with the transaction.
- `is_strict`: whether or not terms must have quantities and amounts of opposite signs.
- `kwargs`: keyword arguments

<a name="aea.helpers.transaction.base.Terms.id"></a>
#### id

```python
 | @property
 | id() -> str
```

Get hash of the terms.

<a name="aea.helpers.transaction.base.Terms.sender_hash"></a>
#### sender`_`hash

```python
 | @property
 | sender_hash() -> str
```

Get the sender hash.

<a name="aea.helpers.transaction.base.Terms.counterparty_hash"></a>
#### counterparty`_`hash

```python
 | @property
 | counterparty_hash() -> str
```

Get the sender hash.

<a name="aea.helpers.transaction.base.Terms.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a name="aea.helpers.transaction.base.Terms.sender_address"></a>
#### sender`_`address

```python
 | @property
 | sender_address() -> Address
```

Get the sender address.

<a name="aea.helpers.transaction.base.Terms.counterparty_address"></a>
#### counterparty`_`address

```python
 | @property
 | counterparty_address() -> Address
```

Get the counterparty address.

<a name="aea.helpers.transaction.base.Terms.counterparty_address"></a>
#### counterparty`_`address

```python
 | @counterparty_address.setter
 | counterparty_address(counterparty_address: Address) -> None
```

Set the counterparty address.

<a name="aea.helpers.transaction.base.Terms.amount_by_currency_id"></a>
#### amount`_`by`_`currency`_`id

```python
 | @property
 | amount_by_currency_id() -> Dict[str, int]
```

Get the amount by currency id.

<a name="aea.helpers.transaction.base.Terms.is_sender_payable_tx_fee"></a>
#### is`_`sender`_`payable`_`tx`_`fee

```python
 | @property
 | is_sender_payable_tx_fee() -> bool
```

Bool indicating whether the tx fee is paid by sender or counterparty.

<a name="aea.helpers.transaction.base.Terms.is_single_currency"></a>
#### is`_`single`_`currency

```python
 | @property
 | is_single_currency() -> bool
```

Check whether a single currency is used for payment.

<a name="aea.helpers.transaction.base.Terms.is_empty_currency"></a>
#### is`_`empty`_`currency

```python
 | @property
 | is_empty_currency() -> bool
```

Check whether a single currency is used for payment.

<a name="aea.helpers.transaction.base.Terms.currency_id"></a>
#### currency`_`id

```python
 | @property
 | currency_id() -> str
```

Get the amount the sender must pay.

<a name="aea.helpers.transaction.base.Terms.sender_payable_amount"></a>
#### sender`_`payable`_`amount

```python
 | @property
 | sender_payable_amount() -> int
```

Get the amount the sender must pay.

<a name="aea.helpers.transaction.base.Terms.sender_payable_amount_incl_fee"></a>
#### sender`_`payable`_`amount`_`incl`_`fee

```python
 | @property
 | sender_payable_amount_incl_fee() -> int
```

Get the amount the sender must pay inclusive fee.

<a name="aea.helpers.transaction.base.Terms.counterparty_payable_amount"></a>
#### counterparty`_`payable`_`amount

```python
 | @property
 | counterparty_payable_amount() -> int
```

Get the amount the counterparty must pay.

<a name="aea.helpers.transaction.base.Terms.counterparty_payable_amount_incl_fee"></a>
#### counterparty`_`payable`_`amount`_`incl`_`fee

```python
 | @property
 | counterparty_payable_amount_incl_fee() -> int
```

Get the amount the counterparty must pay.

<a name="aea.helpers.transaction.base.Terms.quantities_by_good_id"></a>
#### quantities`_`by`_`good`_`id

```python
 | @property
 | quantities_by_good_id() -> Dict[str, int]
```

Get the quantities by good id.

<a name="aea.helpers.transaction.base.Terms.good_ids"></a>
#### good`_`ids

```python
 | @property
 | good_ids() -> List[str]
```

Get the (ordered) good ids.

<a name="aea.helpers.transaction.base.Terms.sender_supplied_quantities"></a>
#### sender`_`supplied`_`quantities

```python
 | @property
 | sender_supplied_quantities() -> List[int]
```

Get the (ordered) quantities supplied by the sender.

<a name="aea.helpers.transaction.base.Terms.counterparty_supplied_quantities"></a>
#### counterparty`_`supplied`_`quantities

```python
 | @property
 | counterparty_supplied_quantities() -> List[int]
```

Get the (ordered) quantities supplied by the counterparty.

<a name="aea.helpers.transaction.base.Terms.nonce"></a>
#### nonce

```python
 | @property
 | nonce() -> str
```

Get the nonce.

<a name="aea.helpers.transaction.base.Terms.has_fee"></a>
#### has`_`fee

```python
 | @property
 | has_fee() -> bool
```

Check if fee is set.

<a name="aea.helpers.transaction.base.Terms.fee"></a>
#### fee

```python
 | @property
 | fee() -> int
```

Get the fee.

<a name="aea.helpers.transaction.base.Terms.sender_fee"></a>
#### sender`_`fee

```python
 | @property
 | sender_fee() -> int
```

Get the sender fee.

<a name="aea.helpers.transaction.base.Terms.counterparty_fee"></a>
#### counterparty`_`fee

```python
 | @property
 | counterparty_fee() -> int
```

Get the counterparty fee.

<a name="aea.helpers.transaction.base.Terms.fee_by_currency_id"></a>
#### fee`_`by`_`currency`_`id

```python
 | @property
 | fee_by_currency_id() -> Dict[str, int]
```

Get fee by currency.

<a name="aea.helpers.transaction.base.Terms.kwargs"></a>
#### kwargs

```python
 | @property
 | kwargs() -> JSONLike
```

Get the kwargs.

<a name="aea.helpers.transaction.base.Terms.is_strict"></a>
#### is`_`strict

```python
 | @property
 | is_strict() -> bool
```

Get is_strict.

<a name="aea.helpers.transaction.base.Terms.get_hash"></a>
#### get`_`hash

```python
 | @staticmethod
 | get_hash(ledger_id: str, sender_address: str, counterparty_address: str, good_ids: List[str], sender_supplied_quantities: List[int], counterparty_supplied_quantities: List[int], sender_payable_amount: int, counterparty_payable_amount: int, nonce: str) -> str
```

Generate a hash from transaction information.

**Arguments**:

- `ledger_id`: the ledger id
- `sender_address`: the sender address
- `counterparty_address`: the counterparty address
- `good_ids`: the list of good ids
- `sender_supplied_quantities`: the quantities supplied by the sender (must all be positive)
- `counterparty_supplied_quantities`: the quantities supplied by the counterparty (must all be positive)
- `sender_payable_amount`: the amount payable by the sender
- `counterparty_payable_amount`: the amount payable by the counterparty
- `nonce`: the nonce of the transaction

**Returns**:

the hash

<a name="aea.helpers.transaction.base.Terms.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(terms_protobuf_object: Any, terms_object: "Terms") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the terms_protobuf_object argument must be matched with the instance of this class in the 'terms_object' argument.

**Arguments**:

- `terms_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `terms_object`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.transaction.base.Terms.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, terms_protobuf_object: Any) -> "Terms"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'terms_protobuf_object' argument.

**Arguments**:

- `terms_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'terms_protobuf_object' argument.

<a name="aea.helpers.transaction.base.Terms.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.transaction.base.Terms.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.helpers.transaction.base.TransactionDigest"></a>
## TransactionDigest Objects

```python
class TransactionDigest()
```

This class represents an instance of TransactionDigest.

<a name="aea.helpers.transaction.base.TransactionDigest.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_id: str, body: str) -> None
```

Initialise an instance of TransactionDigest.

<a name="aea.helpers.transaction.base.TransactionDigest.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a name="aea.helpers.transaction.base.TransactionDigest.body"></a>
#### body

```python
 | @property
 | body() -> str
```

Get the receipt.

<a name="aea.helpers.transaction.base.TransactionDigest.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(transaction_digest_protobuf_object: Any, transaction_digest_object: "TransactionDigest") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the transaction_digest_protobuf_object argument must be matched with the instance of this class in the 'transaction_digest_object' argument.

**Arguments**:

- `transaction_digest_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `transaction_digest_object`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.transaction.base.TransactionDigest.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, transaction_digest_protobuf_object: Any) -> "TransactionDigest"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'transaction_digest_protobuf_object' argument.

**Arguments**:

- `transaction_digest_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'transaction_digest_protobuf_object' argument.

<a name="aea.helpers.transaction.base.TransactionDigest.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.transaction.base.TransactionDigest.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.helpers.transaction.base.TransactionReceipt"></a>
## TransactionReceipt Objects

```python
class TransactionReceipt()
```

This class represents an instance of TransactionReceipt.

<a name="aea.helpers.transaction.base.TransactionReceipt.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_id: str, receipt: JSONLike, transaction: JSONLike) -> None
```

Initialise an instance of TransactionReceipt.

<a name="aea.helpers.transaction.base.TransactionReceipt.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a name="aea.helpers.transaction.base.TransactionReceipt.receipt"></a>
#### receipt

```python
 | @property
 | receipt() -> JSONLike
```

Get the receipt.

<a name="aea.helpers.transaction.base.TransactionReceipt.transaction"></a>
#### transaction

```python
 | @property
 | transaction() -> JSONLike
```

Get the transaction.

<a name="aea.helpers.transaction.base.TransactionReceipt.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(transaction_receipt_protobuf_object: Any, transaction_receipt_object: "TransactionReceipt") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the transaction_receipt_protobuf_object argument must be matched with the instance of this class in the 'transaction_receipt_object' argument.

**Arguments**:

- `transaction_receipt_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `transaction_receipt_object`: an instance of this class to be encoded in the protocol buffer object.

<a name="aea.helpers.transaction.base.TransactionReceipt.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, transaction_receipt_protobuf_object: Any) -> "TransactionReceipt"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'transaction_receipt_protobuf_object' argument.

**Arguments**:

- `transaction_receipt_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'transaction_receipt_protobuf_object' argument.

<a name="aea.helpers.transaction.base.TransactionReceipt.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Check equality.

<a name="aea.helpers.transaction.base.TransactionReceipt.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

