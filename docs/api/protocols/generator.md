<a name=".aea.protocols.generator"></a>
# aea.protocols.generator

This module contains the protocol generator.

<a name=".aea.protocols.generator.ProtocolGenerator"></a>
## ProtocolGenerator Objects

```python
class ProtocolGenerator()
```

This class generates a protocol_verification package from a ProtocolTemplate object.

<a name=".aea.protocols.generator.ProtocolGenerator.__init__"></a>
#### `__`init`__`

```python
 | __init__(protocol_specification: ProtocolSpecification, output_path: str = ".", path_to_protocol_package: Optional[str] = None) -> None
```

Instantiate a protocol generator.

**Arguments**:

- `protocol_specification`: the protocol specification object
- `output_path`: the path to the location in which the protocol module is to be generated.

**Returns**:

None

<a name=".aea.protocols.generator.ProtocolGenerator.generate"></a>
#### generate

```python
 | generate() -> None
```

Create the protocol package with Message, Serialization, __init__, protocol.yaml files.

**Returns**:

None

