<a name="aea.error_handler.default"></a>
# aea.error`_`handler.default

This module contains the default error handler class.

<a name="aea.error_handler.default.ErrorHandler"></a>
## ErrorHandler Objects

```python
class ErrorHandler(AbstractErrorHandler)
```

Error handler class for handling problematic envelopes.

<a name="aea.error_handler.default.ErrorHandler.send_unsupported_protocol"></a>
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

<a name="aea.error_handler.default.ErrorHandler.send_decoding_error"></a>
#### send`_`decoding`_`error

```python
 | @classmethod
 | send_decoding_error(cls, envelope: Envelope, exception: Exception, logger: Logger) -> None
```

Handle a decoding error.

**Arguments**:

- `envelope`: the envelope
- `exception`: the exception raised during decoding
- `logger`: the logger

**Returns**:

None

<a name="aea.error_handler.default.ErrorHandler.send_no_active_handler"></a>
#### send`_`no`_`active`_`handler

```python
 | @classmethod
 | send_no_active_handler(cls, envelope: Envelope, reason: str, logger: Logger) -> None
```

Handle the received envelope in case the handler is not supported.

**Arguments**:

- `envelope`: the envelope
- `reason`: the reason for the failure

**Returns**:

None

