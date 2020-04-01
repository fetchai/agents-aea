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
 | __init__(configuration: ComponentConfiguration, is_vendor: bool = False)
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

<a name=".aea.configurations.components.Component.load"></a>
#### load

```python
 | load() -> None
```

Set the component up.

This method is called by the framework before running the agent.
The implementation varies depending on the type of component.
Please check the concrete component classes.

<a name=".aea.configurations.components.Component.load_from_directory"></a>
#### load`_`from`_`directory

```python
 | @classmethod
 | load_from_directory(cls, component_type: ComponentType, directory: Path, skip_consistency_check: bool = False) -> "Component"
```

Load a component from the directory.

**Arguments**:

- `component_type`: the component type.
- `directory`: the directory of the package.
- `skip_consistency_check`: if True, the consistency check are skipped.

**Returns**:

the loaded component.

