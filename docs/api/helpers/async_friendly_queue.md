<a name="aea.helpers.async_friendly_queue"></a>
# aea.helpers.async`_`friendly`_`queue

This module contains the implementation of AsyncFriendlyQueue.

<a name="aea.helpers.async_friendly_queue.AsyncFriendlyQueue"></a>
## AsyncFriendlyQueue Objects

```python
class AsyncFriendlyQueue(queue.Queue)
```

queue.Queue with async_get method.

<a name="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.__init__"></a>
#### `__`init`__`

```python
 | __init__(*args, **kwargs)
```

Init queue.

<a name="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.put"></a>
#### put

```python
 | put(item: Any, *args, **kwargs) -> None
```

Put an item into the queue.

**Arguments**:

- `item`: item to put in the queue
:param args, kwargs: similar to queue.Queue.put

<a name="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.get"></a>
#### get

```python
 | get(*args, **kwargs) -> Any
```

Get an item into the queue.

:param args, kwargs: similar to queue.Queue.get

<a name="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.async_wait"></a>
#### async`_`wait

```python
 | async async_wait() -> None
```

Wait an item appears in the queue.

**Returns**:

None

<a name="aea.helpers.async_friendly_queue.AsyncFriendlyQueue.async_get"></a>
#### async`_`get

```python
 | async async_get() -> Any
```

Wait and get an item from the queue.

**Returns**:

item from queue

