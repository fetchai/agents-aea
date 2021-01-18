<a name="aea.helpers.storage.backends.base"></a>
# aea.helpers.storage.backends.base

This module contains storage abstract backend class.

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend"></a>
## AbstractStorageBackend Objects

```python
class AbstractStorageBackend(ABC)
```

Abstract base class for storage backend.

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.__init__"></a>
#### `__`init`__`

```python
 | __init__(uri: str) -> None
```

Init backend.

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.connect"></a>
#### connect

```python
 | @abstractmethod
 | async connect() -> None
```

Connect to backend.

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.disconnect"></a>
#### disconnect

```python
 | @abstractmethod
 | async disconnect() -> None
```

Disconnect the backend.

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.ensure_collection"></a>
#### ensure`_`collection

```python
 | @abstractmethod
 | async ensure_collection(collection_name: str) -> None
```

Create collection if not exits.

**Arguments**:

- `collection_name`: str.

**Returns**:

None

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.put"></a>
#### put

```python
 | @abstractmethod
 | async put(collection_name: str, object_id: str, object_body: JSON_TYPES) -> None
```

Put object into collection.

**Arguments**:

- `collection_name`: str.
- `object_id`: str object id
- `object_body`: python dict, json compatible.

**Returns**:

None

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.get"></a>
#### get

```python
 | @abstractmethod
 | async get(collection_name: str, object_id: str) -> Optional[JSON_TYPES]
```

Get object from the collection.

**Arguments**:

- `collection_name`: str.
- `object_id`: str object id

**Returns**:

dict if object exists in collection otherwise None

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.remove"></a>
#### remove

```python
 | @abstractmethod
 | async remove(collection_name: str, object_id: str) -> None
```

Remove object from the collection.

**Arguments**:

- `collection_name`: str.
- `object_id`: str object id

**Returns**:

None

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.find"></a>
#### find

```python
 | @abstractmethod
 | async find(collection_name: str, field: str, equals: EQUALS_TYPE) -> List[OBJECT_ID_AND_BODY]
```

Get objects from the collection by filtering by field value.

**Arguments**:

- `collection_name`: str.
- `field`: field name to search: example "parent.field"
- `equals`: value field should be equal to

**Returns**:

list of objects bodies

<a name="aea.helpers.storage.backends.base.AbstractStorageBackend.list"></a>
#### list

```python
 | @abstractmethod
 | async list(collection_name: str) -> List[OBJECT_ID_AND_BODY]
```

List all objects with keys from the collection.

**Arguments**:

- `collection_name`: str.

**Returns**:

Tuple of objects keys, bodies.

