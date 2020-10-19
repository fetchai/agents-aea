<a name="aea.protocols.generator.base"></a>
# aea.protocols.generator.base

This module contains the protocol generator.

<a name="aea.protocols.generator.base.ProtocolGenerator"></a>
## ProtocolGenerator Objects

```python
class ProtocolGenerator()
```

This class generates a protocol_verification package from a ProtocolTemplate object.

<a name="aea.protocols.generator.base.ProtocolGenerator.__init__"></a>
#### `__`init`__`

```python
 | __init__(path_to_protocol_specification: str, output_path: str = ".", dotted_path_to_protocol_package: Optional[str] = None) -> None
```

Instantiate a protocol generator.

**Arguments**:

- `path_to_protocol_specification`: path to protocol specification file
- `output_path`: the path to the location in which the protocol module is to be generated.
- `dotted_path_to_protocol_package`: the path to the protocol package

**Returns**:

None

<a name="aea.protocols.generator.base.ProtocolGenerator.generate_protobuf_only_mode"></a>
#### generate`_`protobuf`_`only`_`mode

```python
 | generate_protobuf_only_mode() -> None
```

Run the generator in "protobuf only" mode:

a) validate the protocol specification.
b) create the protocol buffer schema file.

**Returns**:

None

<a name="aea.protocols.generator.base.ProtocolGenerator.generate_full_mode"></a>
#### generate`_`full`_`mode

```python
 | generate_full_mode() -> Optional[str]
```

Run the generator in "full" mode:

a) validates the protocol specification.
b) creates the protocol buffer schema file.
c) generates python modules.
d) applies black formatting
e) applies isort formatting

**Returns**:

optional warning message

<a name="aea.protocols.generator.base.ProtocolGenerator.generate"></a>
#### generate

```python
 | generate(protobuf_only: bool = False) -> Optional[str]
```

Run the generator. If in "full" mode (protobuf_only is False), it:

a) validates the protocol specification.
b) creates the protocol buffer schema file.
c) generates python modules.
d) applies black formatting
e) applies isort formatting

If in "protobuf only" mode (protobuf_only is True), it only does a) and b).

**Arguments**:

- `protobuf_only`: mode of running the generator.

**Returns**:

optional warning message.

