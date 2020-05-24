<a name=".aea.crypto.registry"></a>
## aea.crypto.registry

This module implements the crypto registry.

<a name=".aea.crypto.registry.CryptoId"></a>
### CryptoId

```python
class CryptoId(RegexConstrainedString)
```

The identifier of a crypto class.

<a name=".aea.crypto.registry.CryptoId.__init__"></a>
#### `__`init`__`

```python
 | __init__(seq)
```

Initialize the crypto id.

<a name=".aea.crypto.registry.CryptoId.name"></a>
#### name

```python
 | @property
 | name()
```

Get the id name.

<a name=".aea.crypto.registry.EntryPoint"></a>
### EntryPoint

```python
class EntryPoint(RegexConstrainedString)
```

The entry point for a Crypto resource.

The regular expression matches the strings in the following format:

    path.to.module:className

<a name=".aea.crypto.registry.EntryPoint.__init__"></a>
#### `__`init`__`

```python
 | __init__(seq)
```

Initialize the entrypoint.

<a name=".aea.crypto.registry.EntryPoint.import_path"></a>
#### import`_`path

```python
 | @property
 | import_path() -> str
```

Get the import path.

<a name=".aea.crypto.registry.EntryPoint.class_name"></a>
#### class`_`name

```python
 | @property
 | class_name() -> str
```

Get the class name.

<a name=".aea.crypto.registry.EntryPoint.load"></a>
#### load

```python
 | load() -> Type[Crypto]
```

Load the crypto object.

**Returns**:

the cyrpto object, loaded following the spec.

<a name=".aea.crypto.registry.CryptoSpec"></a>
### CryptoSpec

```python
class CryptoSpec(object)
```

A specification for a particular instance of a crypto object.

<a name=".aea.crypto.registry.CryptoSpec.__init__"></a>
#### `__`init`__`

```python
 | __init__(id: CryptoId, entry_point: EntryPoint, **kwargs: Dict, ,)
```

Initialize a crypto specification.

**Arguments**:

- `id`: the id associated to this specification
- `entry_point`: The Python entry_point of the environment class (e.g. module.name:Class).
- `kwargs`: other custom keyword arguments.

<a name=".aea.crypto.registry.CryptoSpec.make"></a>
#### make

```python
 | make(**kwargs) -> Crypto
```

Instantiates an instance of the crypto object with appropriate arguments.

<a name=".aea.crypto.registry.CryptoRegistry"></a>
### CryptoRegistry

```python
class CryptoRegistry(object)
```

Registry for Crypto classes.

<a name=".aea.crypto.registry.CryptoRegistry.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Initialize the Crypto registry.

<a name=".aea.crypto.registry.CryptoRegistry.supported_crypto_ids"></a>
#### supported`_`crypto`_`ids

```python
 | @property
 | supported_crypto_ids() -> Set[str]
```

Get the supported crypto ids.

<a name=".aea.crypto.registry.CryptoRegistry.register"></a>
#### register

```python
 | register(id: CryptoId, entry_point: EntryPoint, **kwargs)
```

Register a Crypto module.

**Arguments**:

- `id`: the Cyrpto identifier (e.g. 'fetchai', 'ethereum' etc.)
- `entry_point`: the entry point, i.e. 'path.to.module:ClassName'

**Returns**:

None

<a name=".aea.crypto.registry.CryptoRegistry.make"></a>
#### make

```python
 | make(id: CryptoId, module: Optional[str] = None, **kwargs) -> Crypto
```

Make an instance of the crypto class associated to the given id.

**Arguments**:

- `id`: the id of the crypto class.
- `module`: see 'module' parameter to 'make'.
- `kwargs`: keyword arguments to be forwarded to the Crypto object.

**Returns**:

the new Crypto instance.

<a name=".aea.crypto.registry.CryptoRegistry.has_spec"></a>
#### has`_`spec

```python
 | has_spec(id: CryptoId) -> bool
```

Check whether there exist a spec associated with a crypto id.

**Arguments**:

- `id`: the crypto identifier.

**Returns**:

True if it is registered, False otherwise.

<a name=".aea.crypto.registry.register"></a>
#### register

```python
register(id: Union[CryptoId, str], entry_point: Union[EntryPoint, str], **kwargs) -> None
```

Register a crypto type.

**Arguments**:

- `id`: the identifier for the crypto type.
- `entry_point`: the entry point to load the crypto object.
- `kwargs`: arguments to provide to the crypto class.

**Returns**:

None.

<a name=".aea.crypto.registry.make"></a>
#### make

```python
make(id: Union[CryptoId, str], module: Optional[str] = None, **kwargs) -> Crypto
```

Create a crypto instance.

**Arguments**:

- `id`: the id of the crypto object. Make sure it has been registered earlier
before calling this function.
- `module`: dotted path to a module.
whether a module should be loaded before creating the object.
this argument is useful when the item might not be registered
beforehand, and loading the specified module will make the
registration.
E.g. suppose the call to 'register' for a custom crypto object
is located in some_package/__init__.py. By providing module="some_package",
the call to 'register' in such module gets triggered and
the make can then find the identifier.
- `kwargs`: keyword arguments to be forwarded to the Crypto object.

**Returns**:



