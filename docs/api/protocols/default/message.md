<a name="packages.fetchai.protocols.default.message"></a>
# packages.fetchai.protocols.default.message

This module contains default's message definition.

<a name="packages.fetchai.protocols.default.message.DefaultMessage"></a>
## DefaultMessage Objects

```python
class DefaultMessage(Message)
```

A protocol for exchanging any bytes message.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.Performative"></a>
## Performative Objects

```python
class Performative(Message.Performative)
```

Performatives for the default protocol.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.Performative.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.__init__"></a>
#### `__`init`__`

```python
 | __init__(performative: Performative, dialogue_reference: Tuple[str, str] = ("", ""), message_id: int = 1, target: int = 0, **kwargs: Any, ,)
```

Initialise an instance of DefaultMessage.

**Arguments**:

- `message_id`: the message id.
- `dialogue_reference`: the dialogue reference.
- `target`: the message target.
- `performative`: the message performative.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.valid_performatives"></a>
#### valid`_`performatives

```python
 | @property
 | valid_performatives() -> Set[str]
```

Get valid performatives.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.dialogue_reference"></a>
#### dialogue`_`reference

```python
 | @property
 | dialogue_reference() -> Tuple[str, str]
```

Get the dialogue_reference of the message.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.message_id"></a>
#### message`_`id

```python
 | @property
 | message_id() -> int
```

Get the message_id of the message.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.performative"></a>
#### performative

```python
 | @property
 | performative() -> Performative
```

Get the performative of the message.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.target"></a>
#### target

```python
 | @property
 | target() -> int
```

Get the target of the message.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.content"></a>
#### content

```python
 | @property
 | content() -> bytes
```

Get the 'content' content from the message.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.error_code"></a>
#### error`_`code

```python
 | @property
 | error_code() -> CustomErrorCode
```

Get the 'error_code' content from the message.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.error_data"></a>
#### error`_`data

```python
 | @property
 | error_data() -> Dict[str, bytes]
```

Get the 'error_data' content from the message.

<a name="packages.fetchai.protocols.default.message.DefaultMessage.error_msg"></a>
#### error`_`msg

```python
 | @property
 | error_msg() -> str
```

Get the 'error_msg' content from the message.

