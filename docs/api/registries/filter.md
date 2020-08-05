<a name="aea.registries.filter"></a>
# aea.registries.filter

This module contains registries.

<a name="aea.registries.filter.Filter"></a>
## Filter Objects

```python
class Filter()
```

This class implements the filter of an AEA.

<a name="aea.registries.filter.Filter.__init__"></a>
#### `__`init`__`

```python
 | __init__(resources: Resources, decision_maker_out_queue: Queue)
```

Instantiate the filter.

**Arguments**:

- `resources`: the resources
- `decision_maker_out_queue`: the decision maker queue

<a name="aea.registries.filter.Filter.resources"></a>
#### resources

```python
 | @property
 | resources() -> Resources
```

Get resources.

<a name="aea.registries.filter.Filter.decision_maker_out_queue"></a>
#### decision`_`maker`_`out`_`queue

```python
 | @property
 | decision_maker_out_queue() -> Queue
```

Get decision maker (out) queue.

<a name="aea.registries.filter.Filter.get_active_handlers"></a>
#### get`_`active`_`handlers

```python
 | get_active_handlers(protocol_id: PublicId, skill_id: Optional[SkillId] = None) -> List[Handler]
```

Get active handlers based on protocol id and optional skill id.

**Arguments**:

- `protocol_id`: the protocol id
- `skill_id`: the skill id

**Returns**:

the list of handlers currently active

<a name="aea.registries.filter.Filter.get_active_behaviours"></a>
#### get`_`active`_`behaviours

```python
 | get_active_behaviours() -> List[Behaviour]
```

Get the active behaviours.

**Returns**:

the list of behaviours currently active

<a name="aea.registries.filter.Filter.handle_internal_messages"></a>
#### handle`_`internal`_`messages

```python
 | handle_internal_messages() -> None
```

Handle the messages from the decision maker.

**Returns**:

None

