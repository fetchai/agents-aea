<a name="aea.components.loader"></a>
# aea.components.loader

This module contains utilities for loading components.

<a name="aea.components.loader.component_type_to_class"></a>
#### component`_`type`_`to`_`class

```python
component_type_to_class(component_type: ComponentType) -> Type[Component]
```

Get the component class from the component type.

**Arguments**:

- `component_type`: the component type

**Returns**:

the component class

<a name="aea.components.loader.load_component_from_config"></a>
#### load`_`component`_`from`_`config

```python
load_component_from_config(configuration: ComponentConfiguration, *args, **kwargs) -> Component
```

Load a component from a directory.

**Arguments**:

- `configuration`: the component configuration.
- `args`: the positional arguments.
- `kwargs`: the keyword arguments.

**Returns**:

the component instance.

<a name="aea.components.loader.AEAPackageNotFound"></a>
## AEAPackageNotFound Objects

```python
class AEAPackageNotFound(Exception)
```

Exception when failed to import package, cause not exists.

