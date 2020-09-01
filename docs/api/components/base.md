<a name="aea.components.base"></a>
# aea.components.base

This module contains definitions of agent components.

<a name="aea.components.base.Component"></a>
## Component Objects

```python
class Component(ABC,  WithLogger)
```

Abstract class for an agent component.

<a name="aea.components.base.Component.__init__"></a>
#### `__`init`__`

```python
 | __init__(configuration: Optional[ComponentConfiguration] = None, is_vendor: bool = False, **kwargs, ,)
```

Initialize a package.

**Arguments**:

- `configuration`: the package configuration.
- `is_vendor`: whether the package is vendorized.

<a name="aea.components.base.Component.component_type"></a>
#### component`_`type

```python
 | @property
 | component_type() -> ComponentType
```

Get the component type.

<a name="aea.components.base.Component.is_vendor"></a>
#### is`_`vendor

```python
 | @property
 | is_vendor() -> bool
```

Get whether the component is vendorized or not.

<a name="aea.components.base.Component.prefix_import_path"></a>
#### prefix`_`import`_`path

```python
 | @property
 | prefix_import_path()
```

Get the prefix import path for this component.

<a name="aea.components.base.Component.component_id"></a>
#### component`_`id

```python
 | @property
 | component_id() -> ComponentId
```

Ge the package id.

<a name="aea.components.base.Component.public_id"></a>
#### public`_`id

```python
 | @property
 | public_id() -> PublicId
```

Get the public id.

<a name="aea.components.base.Component.configuration"></a>
#### configuration

```python
 | @property
 | configuration() -> ComponentConfiguration
```

Get the component configuration.

<a name="aea.components.base.Component.directory"></a>
#### directory

```python
 | @property
 | directory() -> Path
```

Get the directory. Raise error if it has not been set yet.

<a name="aea.components.base.Component.directory"></a>
#### directory

```python
 | @directory.setter
 | directory(path: Path) -> None
```

Set the directory. Raise error if already set.

<a name="aea.components.base.load_aea_package"></a>
#### load`_`aea`_`package

```python
load_aea_package(configuration: ComponentConfiguration) -> None
```

Load the AEA package.

It adds all the __init__.py modules into `sys.modules`.

**Arguments**:

- `configuration`: the configuration object.

**Returns**:

None

