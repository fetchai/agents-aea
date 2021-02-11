<a name="packages.fetchai.protocols.default.custom_types"></a>
# packages.fetchai.protocols.default.custom`_`types

This module contains class representations corresponding to every custom type in the protocol specification.

<a name="packages.fetchai.protocols.default.custom_types.ErrorCode"></a>
## ErrorCode Objects

```python
class ErrorCode(Enum)
```

This class represents an instance of ErrorCode.

<a name="packages.fetchai.protocols.default.custom_types.ErrorCode.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(error_code_protobuf_object: Any, error_code_object: "ErrorCode") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the error_code_protobuf_object argument is matched with the instance of this class in the 'error_code_object' argument.

**Arguments**:

- `error_code_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `error_code_object`: an instance of this class to be encoded in the protocol buffer object.

**Returns**:

None

<a name="packages.fetchai.protocols.default.custom_types.ErrorCode.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, error_code_protobuf_object: Any) -> "ErrorCode"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class is created that matches the protocol buffer object in the 'error_code_protobuf_object' argument.

**Arguments**:

- `error_code_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'error_code_protobuf_object' argument.

