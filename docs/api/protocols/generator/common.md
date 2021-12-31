<a name="aea.protocols.generator.common"></a>
# aea.protocols.generator.common

This module contains utility code for generator modules.

<a name="aea.protocols.generator.common.is_installed"></a>
#### is`_`installed

```python
is_installed(programme: str) -> bool
```

Check whether a programme is installed on the system.

**Arguments**:

- `programme`: the name of the programme.

**Returns**:

True if installed, False otherwise

<a name="aea.protocols.generator.common.base_protolint_command"></a>
#### base`_`protolint`_`command

```python
base_protolint_command() -> str
```

Return the base protolint command.

**Returns**:

The base protolint command

<a name="aea.protocols.generator.common.check_prerequisites"></a>
#### check`_`prerequisites

```python
check_prerequisites() -> None
```

Check whether a programme is installed on the system.

<a name="aea.protocols.generator.common.get_protoc_version"></a>
#### get`_`protoc`_`version

```python
get_protoc_version() -> str
```

Get the protoc version used.

<a name="aea.protocols.generator.common.load_protocol_specification"></a>
#### load`_`protocol`_`specification

```python
load_protocol_specification(specification_path: str) -> ProtocolSpecification
```

Load a protocol specification.

**Arguments**:

- `specification_path`: path to the protocol specification yaml file.

**Returns**:

A ProtocolSpecification object

<a name="aea.protocols.generator.common.try_run_black_formatting"></a>
#### try`_`run`_`black`_`formatting

```python
try_run_black_formatting(path_to_protocol_package: str) -> None
```

Run Black code formatting via subprocess.

**Arguments**:

- `path_to_protocol_package`: a path where formatting should be applied.

<a name="aea.protocols.generator.common.try_run_isort_formatting"></a>
#### try`_`run`_`isort`_`formatting

```python
try_run_isort_formatting(path_to_protocol_package: str) -> None
```

Run Isort code formatting via subprocess.

**Arguments**:

- `path_to_protocol_package`: a path where formatting should be applied.

<a name="aea.protocols.generator.common.try_run_protoc"></a>
#### try`_`run`_`protoc

```python
try_run_protoc(path_to_generated_protocol_package: str, name: str, language: str = PROTOCOL_LANGUAGE_PYTHON) -> None
```

Run 'protoc' protocol buffer compiler via subprocess.

**Arguments**:

- `path_to_generated_protocol_package`: path to the protocol buffer schema file.
- `name`: name of the protocol buffer schema file.
- `language`: the target language in which to compile the protobuf schema file

<a name="aea.protocols.generator.common.try_run_protolint"></a>
#### try`_`run`_`protolint

```python
try_run_protolint(path_to_generated_protocol_package: str, name: str) -> None
```

Run 'protolint' linter via subprocess.

**Arguments**:

- `path_to_generated_protocol_package`: path to the protocol buffer schema file.
- `name`: name of the protocol buffer schema file.

<a name="aea.protocols.generator.common.check_protobuf_using_protoc"></a>
#### check`_`protobuf`_`using`_`protoc

```python
check_protobuf_using_protoc(path_to_generated_protocol_package: str, name: str) -> Tuple[bool, str]
```

Check whether a protocol buffer schema file is valid.

Validation is via trying to compile the schema file. If successfully compiled it is valid, otherwise invalid.
If valid, return True and a 'protobuf file is valid' message, otherwise return False and the error thrown by the compiler.

**Arguments**:

- `path_to_generated_protocol_package`: path to the protocol buffer schema file.
- `name`: name of the protocol buffer schema file.

**Returns**:

Boolean result and an accompanying message

<a name="aea.protocols.generator.common.compile_protobuf_using_protoc"></a>
#### compile`_`protobuf`_`using`_`protoc

```python
compile_protobuf_using_protoc(path_to_generated_protocol_package: str, name: str, language: str) -> Tuple[bool, str]
```

Compile a protocol buffer schema file using protoc.

If successfully compiled, return True and a success message,
otherwise return False and the error thrown by the compiler.

**Arguments**:

- `path_to_generated_protocol_package`: path to the protocol buffer schema file.
- `name`: name of the protocol buffer schema file.
- `language`: the target language in which to compile the protobuf schema file

**Returns**:

Boolean result and an accompanying message

<a name="aea.protocols.generator.common.apply_protolint"></a>
#### apply`_`protolint

```python
apply_protolint(path_to_proto_file: str, name: str) -> Tuple[bool, str]
```

Apply protolint linter to a protocol buffer schema file.

If no output, return True and a success message,
otherwise return False and the output shown by the linter
(minus the indentation suggestions which are automatically fixed by protolint).

**Arguments**:

- `path_to_proto_file`: path to the protocol buffer schema file.
- `name`: name of the protocol buffer schema file.

**Returns**:

Boolean result and an accompanying message

