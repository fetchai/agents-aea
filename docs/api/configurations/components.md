<a name=".aea.configurations.components"></a>
## aea.configurations.components

This module contains definitions of agent components.

<a name=".aea.configurations.components.Component"></a>
### Component

```python
class Component(ABC)
```

Abstract class for an agent component.

<a name=".aea.configurations.components.Component.__init__"></a>
#### `__`init`__`

```python
 | __init__(configuration: Optional[ComponentConfiguration] = None, is_vendor: bool = False)
```

Initialize a package.

**Arguments**:

- `configuration`: the package configuration.
- `is_vendor`: whether the package is vendorized.

<a name=".aea.configurations.components.Component.component_type"></a>
#### component`_`type

```python
 | @property
 | component_type() -> ComponentType
```

Get the component type.

<a name=".aea.configurations.components.Component.is_vendor"></a>
#### is`_`vendor

```python
 | @property
 | is_vendor() -> bool
```

Get whether the component is vendorized or not.

<a name=".aea.configurations.components.Component.prefix_import_path"></a>
#### prefix`_`import`_`path

```python
 | @property
 | prefix_import_path()
```

Get the prefix import path for this component.

<a name=".aea.configurations.components.Component.component_id"></a>
#### component`_`id

```python
 | @property
 | component_id() -> ComponentId
```

Ge the package id.

<a name=".aea.configurations.components.Component.public_id"></a>
#### public`_`id

```python
 | @property
 | public_id() -> PublicId
```

Get the public id.

<a name=".aea.configurations.components.Component.configuration"></a>
#### configuration

```python
 | @property
 | configuration() -> ComponentConfiguration
```

Get the component configuration.

<a name=".aea.configurations.components.Component.directory"></a>
#### directory

```python
 | @directory.setter
 | directory(path: Path) -> None
```

Set the directory. Raise error if already set.

