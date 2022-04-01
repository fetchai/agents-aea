<a id="aea.registries.filter"></a>

# aea.registries.filter

This module contains registries.

<a id="aea.registries.filter.Filter"></a>

## Filter Objects

```python
class Filter(WithLogger)
```

This class implements the filter of an AEA.

<a id="aea.registries.filter.Filter.__init__"></a>

#### `__`init`__`

```python
def __init__(resources: Resources,
             decision_maker_out_queue: AsyncFriendlyQueue) -> None
```

Instantiate the filter.

**Arguments**:

- `resources`: the resources
- `decision_maker_out_queue`: the decision maker queue

<a id="aea.registries.filter.Filter.resources"></a>

#### resources

```python
@property
def resources() -> Resources
```

Get resources.

<a id="aea.registries.filter.Filter.decision_maker_out_queue"></a>

#### decision`_`maker`_`out`_`queue

```python
@property
def decision_maker_out_queue() -> AsyncFriendlyQueue
```

Get decision maker (out) queue.

<a id="aea.registries.filter.Filter.get_active_handlers"></a>

#### get`_`active`_`handlers

```python
def get_active_handlers(protocol_id: PublicId,
                        skill_id: Optional[PublicId] = None) -> List[Handler]
```

Get active handlers based on protocol id and optional skill id.

**Arguments**:

- `protocol_id`: the protocol id
- `skill_id`: the skill id

**Returns**:

the list of handlers currently active

<a id="aea.registries.filter.Filter.get_active_behaviours"></a>

#### get`_`active`_`behaviours

```python
def get_active_behaviours() -> List[Behaviour]
```

Get the active behaviours.

**Returns**:

the list of behaviours currently active

<a id="aea.registries.filter.Filter.handle_new_handlers_and_behaviours"></a>

#### handle`_`new`_`handlers`_`and`_`behaviours

```python
def handle_new_handlers_and_behaviours() -> None
```

Handle the messages from the decision maker.

<a id="aea.registries.filter.Filter.get_internal_message"></a>

#### get`_`internal`_`message

```python
async def get_internal_message() -> Optional[Message]
```

Get a message from decision_maker_out_queue.

<a id="aea.registries.filter.Filter.handle_internal_message"></a>

#### handle`_`internal`_`message

```python
def handle_internal_message(internal_message: Optional[Message]) -> None
```

Handle internal message.

