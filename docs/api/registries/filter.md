<a name="aea.registries.filter"></a>
# aea.registries.filter

This module contains registries.

<a name="aea.registries.filter.Filter"></a>
## Filter Objects

```python
class Filter(WithLogger)
```

This class implements the filter of an AEA.

<a name="aea.registries.filter.Filter.__init__"></a>
#### `__`init`__`

```python
 | __init__(resources: Resources, decision_maker_out_queue: AsyncFriendlyQueue) -> None
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
 | decision_maker_out_queue() -> AsyncFriendlyQueue
```

Get decision maker (out) queue.

<a name="aea.registries.filter.Filter.get_active_handlers"></a>
#### get`_`active`_`handlers

```python
 | get_active_handlers(protocol_id: PublicId, skill_id: Optional[PublicId] = None) -> List[Handler]
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

<a name="aea.registries.filter.Filter.handle_new_handlers_and_behaviours"></a>
#### handle`_`new`_`handlers`_`and`_`behaviours

```python
 | handle_new_handlers_and_behaviours() -> None
```

Handle the messages from the decision maker.

<a name="aea.registries.filter.Filter.get_internal_message"></a>
#### get`_`internal`_`message

```python
 | async get_internal_message() -> Optional[Message]
```

Get a message from decision_maker_out_queue.

<a name="aea.registries.filter.Filter.handle_internal_message"></a>
#### handle`_`internal`_`message

```python
 | handle_internal_message(internal_message: Optional[Message]) -> None
```

Handle internal message.

