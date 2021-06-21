<a name="aea.helpers.storage.generic_storage"></a>
# aea.helpers.storage.generic`_`storage

This module contains the storage implementation.

<a name="aea.helpers.storage.generic_storage.AsyncCollection"></a>
## AsyncCollection Objects

```python
class AsyncCollection()
```

Async collection.

<a name="aea.helpers.storage.generic_storage.AsyncCollection.__init__"></a>
#### `__`init`__`

```python
 | __init__(storage_backend: AbstractStorageBackend, collection_name: str) -> None
```

Init collection object.

**Arguments**:

- `storage_backend`: storage backed to use.
- `collection_name`: str

<a name="aea.helpers.storage.generic_storage.AsyncCollection.put"></a>
#### put

```python
 | async put(object_id: str, object_body: JSON_TYPES) -> None
```

Put object into collection.

**Arguments**:

- `object_id`: str object id
- `object_body`: python dict, json compatible.

**Returns**:

None

<a name="aea.helpers.storage.generic_storage.AsyncCollection.get"></a>
#### get

```python
 | async get(object_id: str) -> Optional[JSON_TYPES]
```

Get object from the collection.

**Arguments**:

- `object_id`: str object id

**Returns**:

dict if object exists in collection otherwise None

<a name="aea.helpers.storage.generic_storage.AsyncCollection.remove"></a>
#### remove

```python
 | async remove(object_id: str) -> None
```

Remove object from the collection.

**Arguments**:

- `object_id`: str object id

**Returns**:

None

<a name="aea.helpers.storage.generic_storage.AsyncCollection.find"></a>
#### find

```python
 | async find(field: str, equals: EQUALS_TYPE) -> List[OBJECT_ID_AND_BODY]
```

Get objects from the collection by filtering by field value.

**Arguments**:

- `field`: field name to search: example "parent.field"
- `equals`: value field should be equal to

**Returns**:

None

<a name="aea.helpers.storage.generic_storage.AsyncCollection.list"></a>
#### list

```python
 | async list() -> List[OBJECT_ID_AND_BODY]
```

List all objects with keys from the collection.

**Returns**:

Tuple of objects keys, bodies.

<a name="aea.helpers.storage.generic_storage.SyncCollection"></a>
## SyncCollection Objects

```python
class SyncCollection()
```

Async collection.

<a name="aea.helpers.storage.generic_storage.SyncCollection.__init__"></a>
#### `__`init`__`

```python
 | __init__(async_collection_coro: Coroutine, loop: asyncio.AbstractEventLoop) -> None
```

Init collection object.

**Arguments**:

- `async_collection_coro`: coroutine returns async collection.
- `loop`: abstract event loop where storage is running.

<a name="aea.helpers.storage.generic_storage.SyncCollection.put"></a>
#### put

```python
 | put(object_id: str, object_body: JSON_TYPES) -> None
```

Put object into collection.

**Arguments**:

- `object_id`: str object id
- `object_body`: python dict, json compatible.

**Returns**:

None

<a name="aea.helpers.storage.generic_storage.SyncCollection.get"></a>
#### get

```python
 | get(object_id: str) -> Optional[JSON_TYPES]
```

Get object from the collection.

**Arguments**:

- `object_id`: str object id

**Returns**:

dict if object exists in collection otherwise None

<a name="aea.helpers.storage.generic_storage.SyncCollection.remove"></a>
#### remove

```python
 | remove(object_id: str) -> None
```

Remove object from the collection.

**Arguments**:

- `object_id`: str object id

**Returns**:

None

<a name="aea.helpers.storage.generic_storage.SyncCollection.find"></a>
#### find

```python
 | find(field: str, equals: EQUALS_TYPE) -> List[OBJECT_ID_AND_BODY]
```

Get objects from the collection by filtering by field value.

**Arguments**:

- `field`: field name to search: example "parent.field"
- `equals`: value field should be equal to

**Returns**:

List of object bodies

<a name="aea.helpers.storage.generic_storage.SyncCollection.list"></a>
#### list

```python
 | list() -> List[OBJECT_ID_AND_BODY]
```

List all objects with keys from the collection.

**Returns**:

Tuple of objects keys, bodies.

<a name="aea.helpers.storage.generic_storage.Storage"></a>
## Storage Objects

```python
class Storage(Runnable)
```

Generic storage.

<a name="aea.helpers.storage.generic_storage.Storage.__init__"></a>
#### `__`init`__`

```python
 | __init__(storage_uri: str, loop: asyncio.AbstractEventLoop = None, threaded: bool = False) -> None
```

Init storage.

**Arguments**:

- `storage_uri`: configuration string for storage.
- `loop`: asyncio event loop to use.
- `threaded`: bool. start in thread if True.

<a name="aea.helpers.storage.generic_storage.Storage.wait_connected"></a>
#### wait`_`connected

```python
 | async wait_connected() -> None
```

Wait generic storage is connected.

<a name="aea.helpers.storage.generic_storage.Storage.is_connected"></a>
#### is`_`connected

```python
 | @property
 | is_connected() -> bool
```

Get running state of the storage.

<a name="aea.helpers.storage.generic_storage.Storage.run"></a>
#### run

```python
 | async run() -> None
```

Connect storage.

<a name="aea.helpers.storage.generic_storage.Storage.get_collection"></a>
#### get`_`collection

```python
 | async get_collection(collection_name: str) -> AsyncCollection
```

Get async collection.

<a name="aea.helpers.storage.generic_storage.Storage.get_sync_collection"></a>
#### get`_`sync`_`collection

```python
 | get_sync_collection(collection_name: str) -> SyncCollection
```

Get sync collection.

<a name="aea.helpers.storage.generic_storage.Storage.__repr__"></a>
#### `__`repr`__`

```python
 | __repr__() -> str
```

Get string representation of the storage.

