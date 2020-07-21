<a name="aea.skills.error.handlers"></a>
# aea.skills.error.handlers

This package contains the implementation of the handler for the 'default' protocol.

<a name="aea.skills.error.handlers.ErrorHandler"></a>
## ErrorHandler Objects

```python
class ErrorHandler(Handler)
```

This class implements the error handler.

<a name="aea.skills.error.handlers.ErrorHandler.setup"></a>
#### setup

```python
 | setup() -> None
```

Implement the setup.

**Returns**:

None

<a name="aea.skills.error.handlers.ErrorHandler.handle"></a>
#### handle

```python
 | handle(message: Message) -> None
```

Implement the reaction to an envelope.

**Arguments**:

- `message`: the message

<a name="aea.skills.error.handlers.ErrorHandler.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Implement the handler teardown.

**Returns**:

None

<a name="aea.skills.error.handlers.ErrorHandler.send_unsupported_protocol"></a>
#### send`_`unsupported`_`protocol

```python
 | send_unsupported_protocol(envelope: Envelope) -> None
```

Handle the received envelope in case the protocol is not supported.

**Arguments**:

- `envelope`: the envelope

**Returns**:

None

<a name="aea.skills.error.handlers.ErrorHandler.send_decoding_error"></a>
#### send`_`decoding`_`error

```python
 | send_decoding_error(envelope: Envelope) -> None
```

Handle a decoding error.

**Arguments**:

- `envelope`: the envelope

**Returns**:

None

<a name="aea.skills.error.handlers.ErrorHandler.send_unsupported_skill"></a>
#### send`_`unsupported`_`skill

```python
 | send_unsupported_skill(envelope: Envelope) -> None
```

Handle the received envelope in case the skill is not supported.

**Arguments**:

- `envelope`: the envelope

**Returns**:

None

