<a name="aea.error_handler.base"></a>
# aea.error`_`handler.base

This module contains the abstract error handler class.

<a name="aea.error_handler.base.AbstractErrorHandler"></a>
## AbstractErrorHandler Objects

```python
class AbstractErrorHandler(ABC)
```

Error handler class for handling problematic envelopes.

<a name="aea.error_handler.base.AbstractErrorHandler.send_unsupported_protocol"></a>
#### send`_`unsupported`_`protocol

```python
 | @classmethod
 | @abstractmethod
 | send_unsupported_protocol(cls, envelope: Envelope, logger: Logger) -> None
```

Handle the received envelope in case the protocol is not supported.

**Arguments**:

- `envelope`: the envelope
- `logger`: the logger

**Returns**:

None

<a name="aea.error_handler.base.AbstractErrorHandler.send_decoding_error"></a>
#### send`_`decoding`_`error

```python
 | @classmethod
 | @abstractmethod
 | send_decoding_error(cls, envelope: Envelope, exception: Exception, logger: Logger) -> None
```

Handle a decoding error.

**Arguments**:

- `envelope`: the envelope
- `exception`: the exception raised during decoding
- `logger`: the logger

**Returns**:

None

<a name="aea.error_handler.base.AbstractErrorHandler.send_no_active_handler"></a>
#### send`_`no`_`active`_`handler

```python
 | @classmethod
 | @abstractmethod
 | send_no_active_handler(cls, envelope: Envelope, reason: str, logger: Logger) -> None
```

Handle the received envelope in case the handler is not supported.

**Arguments**:

- `envelope`: the envelope
- `reason`: the reason for the failure
- `logger`: the logger

**Returns**:

None

