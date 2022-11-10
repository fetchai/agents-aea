<a id="aea.helpers.async_friendly_queue"></a>

# aea.helpers.async`_`friendly`_`queue

This module contains the implementation of AsyncFriendlyQueue.

<a id="aea.helpers.async_friendly_queue.AsyncFriendlyQueue"></a>

## AsyncFriendlyQueue Objects

```python
class AsyncFriendlyQueue(queue.Queue)
```

queue.Queue with async_get method.

<a id="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Init queue.

<a id="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.put"></a>

#### put

```python
def put(item: Any, *args: Any, **kwargs: Any) -> None
```

Put an item into the queue.

**Arguments**:

- `item`: item to put in the queue
- `args`: similar to queue.Queue.put
- `kwargs`: similar to queue.Queue.put

<a id="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.get"></a>

#### get

```python
def get(*args: Any, **kwargs: Any) -> Any
```

Get an item into the queue.

**Arguments**:

- `args`: similar to queue.Queue.get
- `kwargs`: similar to queue.Queue.get

**Returns**:

similar to queue.Queue.get

<a id="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.async_wait"></a>

#### async`_`wait

```python
async def async_wait() -> None
```

Wait an item appears in the queue.

**Returns**:

None

<a id="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.async_get"></a>

#### async`_`get

```python
async def async_get() -> Any
```

Wait and get an item from the queue.

**Returns**:

item from queue

