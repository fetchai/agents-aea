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

:raises FileNotFoundError if any prerequisite application is not installed
:raises yaml.YAMLError if yaml parser encounters an error condition
:raises ProtocolSpecificationParseError if specification fails generator's validation

<a name="aea.protocols.generator.base.ProtocolGenerator.generate_protobuf_only_mode"></a>
#### generate`_`protobuf`_`only`_`mode

```python
 | generate_protobuf_only_mode(language: str = PROTOCOL_LANGUAGE_PYTHON, run_protolint: bool = True) -> Optional[str]
```

Run the generator in "protobuf only" mode:

a) validate the protocol specification.
b) create the protocol buffer schema file.
c) create the protocol buffer implementation file via 'protoc'.

**Arguments**:

- `language`: the target language in which to generate the package.
- `run_protolint`: whether to run protolint or not.

**Returns**:

None

<a name="aea.protocols.generator.base.ProtocolGenerator.generate_full_mode"></a>
#### generate`_`full`_`mode

```python
 | generate_full_mode(language: str) -> Optional[str]
```

Run the generator in "full" mode:

Runs the generator in protobuf only mode:
    a) validate the protocol specification.
    b) create the protocol buffer schema file.
    c) create the protocol buffer implementation file via 'protoc'.
Additionally:
d) generates python modules.
e) applies black formatting
f) applies isort formatting

**Arguments**:

- `language`: the language for which to create protobuf files

**Returns**:

optional warning message

<a name="aea.protocols.generator.base.ProtocolGenerator.generate"></a>
#### generate

```python
 | generate(protobuf_only: bool = False, language: str = PROTOCOL_LANGUAGE_PYTHON) -> Optional[str]
```

Run the generator either in "full" or "protobuf only" mode.

**Arguments**:

- `protobuf_only`: mode of running the generator.
- `language`: the target language in which to generate the protocol package.

**Returns**:

optional warning message.

<a name="aea.protocols.generator.base.public_id_to_package_name"></a>
#### public`_`id`_`to`_`package`_`name

```python
public_id_to_package_name(public_id: PublicId) -> str
```

Make package name string from public_id provided.

