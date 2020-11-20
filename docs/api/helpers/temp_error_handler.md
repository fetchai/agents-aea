<a name="aea.helpers.temp_error_handler"></a>
# aea.helpers.temp`_`error`_`handler

Temporary error handler.

<a name="aea.helpers.temp_error_handler.ErrorHandler"></a>
## ErrorHandler Objects

```python
class ErrorHandler()
```

Error handler class for handling problematic envelopes.

<a name="aea.helpers.temp_error_handler.ErrorHandler.send_unsupported_protocol"></a>
#### send`_`unsupported`_`protocol

```python
 | @classmethod
 | send_unsupported_protocol(cls, envelope: Envelope, logger: Logger) -> None
```

Handle the received envelope in case the protocol is not supported.

**Arguments**:

- `envelope`: the envelope

**Returns**:

None

<a name="aea.helpers.temp_error_handler.ErrorHandler.send_decoding_error"></a>
#### send`_`decoding`_`error

```python
 | @classmethod
 | send_decoding_error(cls, envelope: Envelope, logger: Logger) -> None
```

Handle a decoding error.

**Arguments**:

- `envelope`: the envelope

**Returns**:

None

<a name="aea.helpers.temp_error_handler.ErrorHandler.send_unsupported_skill"></a>
#### send`_`unsupported`_`skill

```python
 | @classmethod
 | send_unsupported_skill(cls, envelope: Envelope, logger: Logger) -> None
```

Handle the received envelope in case the skill is not supported.

**Arguments**:

- `envelope`: the envelope

**Returns**:

None

