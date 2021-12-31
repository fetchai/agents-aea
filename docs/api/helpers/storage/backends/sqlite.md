<a name="aea.helpers.storage.backends.sqlite"></a>
# aea.helpers.storage.backends.sqlite

This module contains sqlite storage backend implementation.

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend"></a>
## SqliteStorageBackend Objects

```python
class SqliteStorageBackend(AbstractStorageBackend)
```

Sqlite storage backend.

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.__init__"></a>
#### `__`init`__`

```python
 | __init__(uri: str) -> None
```

Init backend.

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.connect"></a>
#### connect

```python
 | async connect() -> None
```

Connect to backend.

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.disconnect"></a>
#### disconnect

```python
 | async disconnect() -> None
```

Disconnect the backend.

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.ensure_collection"></a>
#### ensure`_`collection

```python
 | async ensure_collection(collection_name: str) -> None
```

Create collection if not exits.

**Arguments**:

- `collection_name`: name of the collection.

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.put"></a>
#### put

```python
 | async put(collection_name: str, object_id: str, object_body: JSON_TYPES) -> None
```

Put object into collection.

**Arguments**:

- `collection_name`: str.
- `object_id`: str object id
- `object_body`: python dict, json compatible.

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.get"></a>
#### get

```python
 | async get(collection_name: str, object_id: str) -> Optional[JSON_TYPES]
```

Get object from the collection.

**Arguments**:

- `collection_name`: str.
- `object_id`: str object id

**Returns**:

dict if object exists in collection otherwise None

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.remove"></a>
#### remove

```python
 | async remove(collection_name: str, object_id: str) -> None
```

Remove object from the collection.

**Arguments**:

- `collection_name`: str.
- `object_id`: str object id

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.find"></a>
#### find

```python
 | async find(collection_name: str, field: str, equals: EQUALS_TYPE) -> List[OBJECT_ID_AND_BODY]
```

Get objects from the collection by filtering by field value.

**Arguments**:

- `collection_name`: str.
- `field`: field name to search: example "parent.field"
- `equals`: value field should be equal to

**Returns**:

list of object ids and body

<a name="aea.helpers.storage.backends.sqlite.SqliteStorageBackend.list"></a>
#### list

```python
 | async list(collection_name: str) -> List[OBJECT_ID_AND_BODY]
```

List all objects with keys from the collection.

**Arguments**:

- `collection_name`: str.

**Returns**:

Tuple of objects keys, bodies.

