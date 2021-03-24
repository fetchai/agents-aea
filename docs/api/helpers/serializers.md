<a name="aea.helpers.serializers"></a>
# aea.helpers.serializers

This module contains Serializers that can be used for custom types.

<a name="aea.helpers.serializers.DictProtobufStructSerializer"></a>
## DictProtobufStructSerializer Objects

```python
class DictProtobufStructSerializer()
```

Serialize python dictionaries of type DictType = Dict[str, ValueType] recursively conserving their dynamic type, using google.protobuf.Struct

ValueType = PrimitiveType | DictType | List[ValueType]]
PrimitiveType = bool | int | float | str | bytes

<a name="aea.helpers.serializers.DictProtobufStructSerializer.encode"></a>
#### encode

```python
 | @classmethod
 | encode(cls, dictionary: Dict[str, Any]) -> bytes
```

Serialize compatible dictionary to bytes.

Copies entire dictionary in the process.

**Arguments**:

- `dictionary`: the dictionary to serialize

**Returns**:

serialized bytes string

<a name="aea.helpers.serializers.DictProtobufStructSerializer.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, buffer: bytes) -> Dict[str, Any]
```

Deserialize a compatible dictionary

