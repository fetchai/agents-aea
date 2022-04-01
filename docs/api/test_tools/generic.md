<a id="aea.test_tools.generic"></a>

# aea.test`_`tools.generic

This module contains generic tools for AEA end-to-end testing.

<a id="aea.test_tools.generic.write_envelope_to_file"></a>

#### write`_`envelope`_`to`_`file

```python
def write_envelope_to_file(envelope: Envelope, file_path: str) -> None
```

Write an envelope to a file.

**Arguments**:

- `envelope`: Envelope.
- `file_path`: the file path

<a id="aea.test_tools.generic.read_envelope_from_file"></a>

#### read`_`envelope`_`from`_`file

```python
def read_envelope_from_file(file_path: str) -> Envelope
```

Read an envelope from a file.

**Arguments**:

- `file_path`: the file path.

**Returns**:

envelope

<a id="aea.test_tools.generic.nested_set_config"></a>

#### nested`_`set`_`config

```python
def nested_set_config(dotted_path: str,
                      value: Any,
                      author: str = DEFAULT_AUTHOR) -> None
```

Set an AEA config with nested values.

Run from agent's directory.

Allowed dotted_path:
    'agent.an_attribute_name'
    'protocols.my_protocol.an_attribute_name'
    'connections.my_connection.an_attribute_name'
    'contracts.my_contract.an_attribute_name'
    'skills.my_skill.an_attribute_name'
    'vendor.author.[protocols|connections|skills].package_name.attribute_name

**Arguments**:

- `dotted_path`: dotted path to a setting.
- `value`: a value to assign. Must be of yaml serializable type.
- `author`: the author name, used to parse the dotted path.

