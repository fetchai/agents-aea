<a name="aea.crypto.registries.base"></a>
# aea.crypto.registries.base

This module implements the base registry.

<a name="aea.crypto.registries.base.ItemId"></a>
## ItemId Objects

```python
class ItemId(RegexConstrainedString)
```

The identifier of an item class.

<a name="aea.crypto.registries.base.ItemId.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the id name.

<a name="aea.crypto.registries.base.EntryPoint"></a>
## EntryPoint Objects

```python
class EntryPoint(Generic[ItemType],  RegexConstrainedString)
```

The entry point for a resource.

The regular expression matches the strings in the following format:

    path.to.module:className

<a name="aea.crypto.registries.base.EntryPoint.__init__"></a>
#### `__`init`__`

```python
 | __init__(seq: Union["EntryPoint", str]) -> None
```

Initialize the entrypoint.

<a name="aea.crypto.registries.base.EntryPoint.import_path"></a>
#### import`_`path

```python
 | @property
 | import_path() -> str
```

Get the import path.

<a name="aea.crypto.registries.base.EntryPoint.class_name"></a>
#### class`_`name

```python
 | @property
 | class_name() -> str
```

Get the class name.

<a name="aea.crypto.registries.base.EntryPoint.load"></a>
#### load

```python
 | load() -> Type[ItemType]
```

Load the item object.

**Returns**:

the crypto object, loaded following the spec.

<a name="aea.crypto.registries.base.ItemSpec"></a>
## ItemSpec Objects

```python
class ItemSpec(Generic[ItemType])
```

A specification for a particular instance of an object.

<a name="aea.crypto.registries.base.ItemSpec.__init__"></a>
#### `__`init`__`

```python
 | __init__(id_: ItemId, entry_point: EntryPoint[ItemType], class_kwargs: Optional[Dict[str, Any]] = None, **kwargs: Dict, ,) -> None
```

Initialize an item specification.

**Arguments**:

- `id_`: the id associated to this specification
- `entry_point`: The Python entry_point of the environment class (e.g. module.name:Class).
- `class_kwargs`: keyword arguments to be attached on the class as class variables.
- `kwargs`: other custom keyword arguments.

<a name="aea.crypto.registries.base.ItemSpec.make"></a>
#### make

```python
 | make(**kwargs: Any) -> ItemType
```

Instantiate an instance of the item object with appropriate arguments.

**Arguments**:

- `kwargs`: the key word arguments

**Returns**:

an item

<a name="aea.crypto.registries.base.ItemSpec.get_class"></a>
#### get`_`class

```python
 | get_class() -> Type[ItemType]
```

Get the class of the item with class variables instantiated.

**Returns**:

an item class

<a name="aea.crypto.registries.base.Registry"></a>
## Registry Objects

```python
class Registry(Generic[ItemType])
```

Registry for generic classes.

<a name="aea.crypto.registries.base.Registry.__init__"></a>
#### `__`init`__`

```python
 | __init__() -> None
```

Initialize the registry.

<a name="aea.crypto.registries.base.Registry.supported_ids"></a>
#### supported`_`ids

```python
 | @property
 | supported_ids() -> Set[str]
```

Get the supported item ids.

<a name="aea.crypto.registries.base.Registry.register"></a>
#### register

```python
 | register(id_: Union[ItemId, str], entry_point: Union[EntryPoint[ItemType], str], class_kwargs: Optional[Dict[str, Any]] = None, **kwargs: Any, ,) -> None
```

Register an item type.

**Arguments**:

- `id_`: the identifier for the crypto type.
- `entry_point`: the entry point to load the crypto object.
- `class_kwargs`: keyword arguments to be attached on the class as class variables.
- `kwargs`: arguments to provide to the crypto class.

<a name="aea.crypto.registries.base.Registry.make"></a>
#### make

```python
 | make(id_: Union[ItemId, str], module: Optional[str] = None, **kwargs: Any) -> ItemType
```

Create an instance of the associated type item id.

**Arguments**:

- `id_`: the id of the item class. Make sure it has been registered earlier
    before calling this function.
- `module`: dotted path to a module.
    whether a module should be loaded before creating the object.
    this argument is useful when the item might not be registered
    beforehand, and loading the specified module will make the registration.
    E.g. suppose the call to 'register' for a custom object
    is located in some_package/__init__.py. By providing module="some_package",
    the call to 'register' in such module gets triggered and
    the make can then find the identifier.
- `kwargs`: keyword arguments to be forwarded to the object.

**Returns**:

the new item instance.

<a name="aea.crypto.registries.base.Registry.make_cls"></a>
#### make`_`cls

```python
 | make_cls(id_: Union[ItemId, str], module: Optional[str] = None) -> Type[ItemType]
```

Load a class of the associated type item id.

**Arguments**:

- `id_`: the id of the item class. Make sure it has been registered earlier
    before calling this function.
- `module`: dotted path to a module.
    whether a module should be loaded before creating the object.
    this argument is useful when the item might not be registered
    beforehand, and loading the specified module will make the registration.
    E.g. suppose the call to 'register' for a custom object
    is located in some_package/__init__.py. By providing module="some_package",
    the call to 'register' in such module gets triggered and
    the make can then find the identifier.

**Returns**:

the new item class.

<a name="aea.crypto.registries.base.Registry.has_spec"></a>
#### has`_`spec

```python
 | has_spec(item_id: ItemId) -> bool
```

Check whether there exist a spec associated with an item id.

**Arguments**:

- `item_id`: the item identifier.

**Returns**:

True if it is registered, False otherwise.

