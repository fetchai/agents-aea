<a name=".aea.decision_maker.messages.transaction"></a>
# aea.decision`_`maker.messages.transaction

The transaction message module.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage"></a>
## TransactionMessage Objects

```python
class TransactionMessage(InternalMessage)
```

The transaction message class.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.Performative"></a>
## Performative Objects

```python
class Performative(Enum)
```

Transaction performative.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.__init__"></a>
#### `__`init`__`

```python
 | __init__(performative: Performative, skill_callback_ids: Sequence[PublicId], tx_id: TransactionId, tx_sender_addr: Address, tx_counterparty_addr: Address, tx_amount_by_currency_id: Dict[str, int], tx_sender_fee: int, tx_counterparty_fee: int, tx_quantities_by_good_id: Dict[str, int], ledger_id: LedgerId, info: Dict[str, Any], **kwargs)
```

Instantiate transaction message.

**Arguments**:

- `performative`: the performative
- `skill_callback_ids`: the list public ids of skills to receive the transaction message response
- `tx_id`: the id of the transaction.
- `tx_sender_addr`: the sender address of the transaction.
- `tx_counterparty_addr`: the counterparty address of the transaction.
- `tx_amount_by_currency_id`: the amount by the currency of the transaction.
- `tx_sender_fee`: the part of the tx fee paid by the sender
- `tx_counterparty_fee`: the part of the tx fee paid by the counterparty
- `tx_quantities_by_good_id`: a map from good id to the quantity of that good involved in the transaction.
- `ledger_id`: the ledger id
- `info`: a dictionary for arbitrary information

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.performative"></a>
#### performative

```python
 | @property
 | performative() -> Performative
```

Get the performative of the message.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.skill_callback_ids"></a>
#### skill`_`callback`_`ids

```python
 | @property
 | skill_callback_ids() -> List[PublicId]
```

Get the list of skill_callback_ids from the message.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_id"></a>
#### tx`_`id

```python
 | @property
 | tx_id() -> str
```

Get the transaction id.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_sender_addr"></a>
#### tx`_`sender`_`addr

```python
 | @property
 | tx_sender_addr() -> Address
```

Get the address of the sender.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_counterparty_addr"></a>
#### tx`_`counterparty`_`addr

```python
 | @property
 | tx_counterparty_addr() -> Address
```

Get the counterparty of the message.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_amount_by_currency_id"></a>
#### tx`_`amount`_`by`_`currency`_`id

```python
 | @property
 | tx_amount_by_currency_id() -> Dict[str, int]
```

Get the currency id.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_sender_fee"></a>
#### tx`_`sender`_`fee

```python
 | @property
 | tx_sender_fee() -> int
```

Get the fee for the sender from the messgae.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_counterparty_fee"></a>
#### tx`_`counterparty`_`fee

```python
 | @property
 | tx_counterparty_fee() -> int
```

Get the fee for the counterparty from the messgae.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_quantities_by_good_id"></a>
#### tx`_`quantities`_`by`_`good`_`id

```python
 | @property
 | tx_quantities_by_good_id() -> Dict[str, int]
```

Get the quantities by good ids.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> LedgerId
```

Get the ledger_id.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.info"></a>
#### info

```python
 | @property
 | info() -> Dict[str, Any]
```

Get the infos from the message.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_nonce"></a>
#### tx`_`nonce

```python
 | @property
 | tx_nonce() -> str
```

Get the tx_nonce from the message.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.tx_digest"></a>
#### tx`_`digest

```python
 | @property
 | tx_digest() -> str
```

Get the transaction digest.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.signing_payload"></a>
#### signing`_`payload

```python
 | @property
 | signing_payload() -> Dict[str, Any]
```

Get the signing payload.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.signed_payload"></a>
#### signed`_`payload

```python
 | @property
 | signed_payload() -> Dict[str, Any]
```

Get the signed payload.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.amount"></a>
#### amount

```python
 | @property
 | amount() -> int
```

Get the amount.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.currency_id"></a>
#### currency`_`id

```python
 | @property
 | currency_id() -> str
```

Get the currency id.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.sender_amount"></a>
#### sender`_`amount

```python
 | @property
 | sender_amount() -> int
```

Get the amount which the sender gets/pays as part of the tx.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.counterparty_amount"></a>
#### counterparty`_`amount

```python
 | @property
 | counterparty_amount() -> int
```

Get the amount which the counterparty gets/pays as part of the tx.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.fees"></a>
#### fees

```python
 | @property
 | fees() -> int
```

Get the tx fees.

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.respond_settlement"></a>
#### respond`_`settlement

```python
 | @classmethod
 | respond_settlement(cls, other: "TransactionMessage", performative: Performative, tx_digest: Optional[str] = None) -> "TransactionMessage"
```

Create response message.

**Arguments**:

- `other`: TransactionMessage
- `performative`: the performative
- `tx_digest`: the transaction digest

**Returns**:

a transaction message object

<a name=".aea.decision_maker.messages.transaction.TransactionMessage.respond_signing"></a>
#### respond`_`signing

```python
 | @classmethod
 | respond_signing(cls, other: "TransactionMessage", performative: Performative, signed_payload: Optional[Dict[str, Any]] = None) -> "TransactionMessage"
```

Create response message.

**Arguments**:

- `other`: TransactionMessage
- `performative`: the performative
- `signed_payload`: the signed payload

**Returns**:

a transaction message object

