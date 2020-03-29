<a name=".aea.decision_maker.messages.base"></a>
## aea.decision`_`maker.messages.base

This module contains the base message and serialization definition.

<a name=".aea.decision_maker.messages.base.InternalMessage"></a>
### InternalMessage

```python
class InternalMessage()
```

This class implements a message.

<a name=".aea.decision_maker.messages.base.InternalMessage.__init__"></a>
#### `__`init`__`

```python
 | __init__(body: Optional[Dict] = None, **kwargs)
```

Initialize a Message object.

**Arguments**:

- `body`: the dictionary of values to hold.
- `kwargs`: any additional value to add to the body. It will overwrite the body values.

<a name=".aea.decision_maker.messages.base.InternalMessage.body"></a>
#### body

```python
 | @body.setter
 | body(body: Dict) -> None
```

Set the body of hte message.

**Arguments**:

- `body`: the body.

**Returns**:

None

<a name=".aea.decision_maker.messages.base.InternalMessage.set"></a>
#### set

```python
 | set(key: str, value: Any) -> None
```

Set key and value pair.

**Arguments**:

- `key`: the key.
- `value`: the value.

**Returns**:

None

<a name=".aea.decision_maker.messages.base.InternalMessage.get"></a>
#### get

```python
 | get(key: str) -> Optional[Any]
```

Get value for key.

<a name=".aea.decision_maker.messages.base.InternalMessage.unset"></a>
#### unset

```python
 | unset(key: str) -> None
```

Unset value for key.

**Arguments**:

- `key`: the key to unset the value of

<a name=".aea.decision_maker.messages.base.InternalMessage.is_set"></a>
#### is`_`set

```python
 | is_set(key: str) -> bool
```

Check value is set for key.

**Arguments**:

- `key`: the key to check

<a name=".aea.decision_maker.messages.base.InternalMessage.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.decision_maker.messages.base.InternalMessage.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation of the message.

