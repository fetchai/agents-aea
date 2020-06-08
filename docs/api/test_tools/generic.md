<a name=".aea.test_tools.generic"></a>
# aea.test`_`tools.generic

This module contains generic tools for AEA end-to-end testing.

<a name=".aea.test_tools.generic.write_envelope_to_file"></a>
#### write`_`envelope`_`to`_`file

```python
write_envelope_to_file(envelope: Envelope, file_path: str) -> None
```

Write an envelope to a file.

**Arguments**:

- `envelope`: Envelope.
- `file_path`: the file path

**Returns**:

None

<a name=".aea.test_tools.generic.read_envelope_from_file"></a>
#### read`_`envelope`_`from`_`file

```python
read_envelope_from_file(file_path: str)
```

Read an envelope from a file.

:param file_path the file path.

**Returns**:

envelope

<a name=".aea.test_tools.generic.force_set_config"></a>
#### force`_`set`_`config

```python
force_set_config(dotted_path: str, value: Any) -> None
```

Set an AEA config without validation.
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

**Returns**:

None.

