<a name="packages.fetchai.protocols.signing.message"></a>
# packages.fetchai.protocols.signing.message

This module contains signing's message definition.

<a name="packages.fetchai.protocols.signing.message.SigningMessage"></a>
## SigningMessage Objects

```python
class SigningMessage(Message)
```

A protocol for communication between skills and decision maker.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.Performative"></a>
## Performative Objects

```python
class Performative(Message.Performative)
```

Performatives for the signing protocol.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.Performative.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.__init__"></a>
#### `__`init`__`

```python
 | __init__(performative: Performative, dialogue_reference: Tuple[str, str] = ("", ""), message_id: int = 1, target: int = 0, **kwargs: Any, ,)
```

Initialise an instance of SigningMessage.

**Arguments**:

- `message_id`: the message id.
- `dialogue_reference`: the dialogue reference.
- `target`: the message target.
- `performative`: the message performative.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.valid_performatives"></a>
#### valid`_`performatives

```python
 | @property
 | valid_performatives() -> Set[str]
```

Get valid performatives.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.dialogue_reference"></a>
#### dialogue`_`reference

```python
 | @property
 | dialogue_reference() -> Tuple[str, str]
```

Get the dialogue_reference of the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.message_id"></a>
#### message`_`id

```python
 | @property
 | message_id() -> int
```

Get the message_id of the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.performative"></a>
#### performative

```python
 | @property
 | performative() -> Performative
```

Get the performative of the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.target"></a>
#### target

```python
 | @property
 | target() -> int
```

Get the target of the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.error_code"></a>
#### error`_`code

```python
 | @property
 | error_code() -> CustomErrorCode
```

Get the 'error_code' content from the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.raw_message"></a>
#### raw`_`message

```python
 | @property
 | raw_message() -> CustomRawMessage
```

Get the 'raw_message' content from the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.raw_transaction"></a>
#### raw`_`transaction

```python
 | @property
 | raw_transaction() -> CustomRawTransaction
```

Get the 'raw_transaction' content from the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.signed_message"></a>
#### signed`_`message

```python
 | @property
 | signed_message() -> CustomSignedMessage
```

Get the 'signed_message' content from the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.signed_transaction"></a>
#### signed`_`transaction

```python
 | @property
 | signed_transaction() -> CustomSignedTransaction
```

Get the 'signed_transaction' content from the message.

<a name="packages.fetchai.protocols.signing.message.SigningMessage.terms"></a>
#### terms

```python
 | @property
 | terms() -> CustomTerms
```

Get the 'terms' content from the message.

