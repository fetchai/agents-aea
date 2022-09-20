<a id="aea.components.base"></a>

# aea.components.base

This module contains definitions of agent components.

<a id="aea.components.base.Component"></a>

## Component Objects

```python
class Component(ABC, WithLogger)
```

Abstract class for an agent component.

<a id="aea.components.base.Component.__init__"></a>

#### `__`init`__`

```python
def __init__(configuration: Optional[ComponentConfiguration] = None,
             is_vendor: bool = False,
             **kwargs: Any) -> None
```

Initialize a package.

**Arguments**:

- `configuration`: the package configuration.
- `is_vendor`: whether the package is vendorized.
- `kwargs`: the keyword arguments for the logger.

<a id="aea.components.base.Component.component_type"></a>

#### component`_`type

```python
@property
def component_type() -> ComponentType
```

Get the component type.

<a id="aea.components.base.Component.is_vendor"></a>

#### is`_`vendor

```python
@property
def is_vendor() -> bool
```

Get whether the component is vendorized or not.

<a id="aea.components.base.Component.prefix_import_path"></a>

#### prefix`_`import`_`path

```python
@property
def prefix_import_path() -> str
```

Get the prefix import path for this component.

<a id="aea.components.base.Component.component_id"></a>

#### component`_`id

```python
@property
def component_id() -> ComponentId
```

Ge the package id.

<a id="aea.components.base.Component.public_id"></a>

#### public`_`id

```python
@property
def public_id() -> PublicId
```

Get the public id.

<a id="aea.components.base.Component.configuration"></a>

#### configuration

```python
@property
def configuration() -> ComponentConfiguration
```

Get the component configuration.

<a id="aea.components.base.Component.directory"></a>

#### directory

```python
@property
def directory() -> Path
```

Get the directory. Raise error if it has not been set yet.

<a id="aea.components.base.Component.directory"></a>

#### directory

```python
@directory.setter
def directory(path: Path) -> None
```

Set the directory. Raise error if already set.

<a id="aea.components.base.Component.build_directory"></a>

#### build`_`directory

```python
@property
def build_directory() -> Optional[str]
```

Get build directory for the component.

<a id="aea.components.base.load_aea_package"></a>

#### load`_`aea`_`package

```python
def load_aea_package(configuration: ComponentConfiguration) -> None
```

Load the AEA package from configuration.

It adds all the __init__.py modules into `sys.modules`.

**Arguments**:

- `configuration`: the configuration object.

<a id="aea.components.base._CheckUsedDependencies"></a>

## `_`CheckUsedDependencies Objects

```python
class _CheckUsedDependencies()
```

Auxiliary class to keep track of used packages in import statements of package modules.

<a id="aea.components.base._CheckUsedDependencies.__init__"></a>

#### `__`init`__`

```python
def __init__(configuration: ComponentConfiguration) -> None
```

Initialize the instance.

<a id="aea.components.base._CheckUsedDependencies.run_check"></a>

#### run`_`check

```python
def run_check() -> None
```

Run the check.

<a id="aea.components.base._CheckUsedDependencies.package_id_prefix_to_str"></a>

#### package`_`id`_`prefix`_`to`_`str

```python
@classmethod
def package_id_prefix_to_str(cls, package_id_prefix: PackageIdPrefix) -> str
```

Get string from package id prefix.

<a id="aea.components.base.perform_load_aea_package"></a>

#### perform`_`load`_`aea`_`package

```python
def perform_load_aea_package(dir_: Path, author: str, package_type_plural: str,
                             package_name: str) -> None
```

Load the AEA package from values provided.

It adds all the __init__.py modules into `sys.modules`.

This function also checks that:
 - all packages declared as dependencies are used in package modules;
 - all imports correspond to a package declared as dependency.

**Arguments**:

- `dir_`: path of the component.
- `author`: str
- `package_type_plural`: str
- `package_name`: str

