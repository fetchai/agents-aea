<a id="aea.crypto.registries.base"></a>

# aea.crypto.registries.base

This module implements the base registry.

<a id="aea.crypto.registries.base.ItemId"></a>

## ItemId Objects

```python
class ItemId(RegexConstrainedString)
```

The identifier of an item class.

<a id="aea.crypto.registries.base.ItemId.name"></a>

#### name

```python
@property
def name() -> str
```

Get the id name.

<a id="aea.crypto.registries.base.EntryPoint"></a>

## EntryPoint Objects

```python
class EntryPoint(Generic[ItemType], RegexConstrainedString)
```

The entry point for a resource.

The regular expression matches the strings in the following format:

    path.to.module:className

<a id="aea.crypto.registries.base.EntryPoint.__init__"></a>

#### `__`init`__`

```python
def __init__(seq: Union["EntryPoint", str]) -> None
```

Initialize the entrypoint.

<a id="aea.crypto.registries.base.EntryPoint.import_path"></a>

#### import`_`path

```python
@property
def import_path() -> str
```

Get the import path.

<a id="aea.crypto.registries.base.EntryPoint.class_name"></a>

#### class`_`name

```python
@property
def class_name() -> str
```

Get the class name.

<a id="aea.crypto.registries.base.EntryPoint.load"></a>

#### load

```python
def load() -> Type[ItemType]
```

Load the item object.

**Returns**:

the crypto object, loaded following the spec.

<a id="aea.crypto.registries.base.ItemSpec"></a>

## ItemSpec Objects

```python
class ItemSpec(Generic[ItemType])
```

A specification for a particular instance of an object.

<a id="aea.crypto.registries.base.ItemSpec.__init__"></a>

#### `__`init`__`

