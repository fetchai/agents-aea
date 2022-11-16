<a id="aea.package_manager.base"></a>

# aea.package`_`manager.base

Base manager class.

<a id="aea.package_manager.base.load_configuration"></a>

#### load`_`configuration

```python
def load_configuration(package_type: PackageType, package_path: Path) -> PackageConfiguration
```

Load a configuration, knowing the type and the path to the package root.

**Arguments**:

- `package_type`: the package type.
- `package_path`: the path to the package root.

**Returns**:

the configuration object.

<a id="aea.package_manager.base.BasePackageManager"></a>

## BasePackageManager Objects

```python
class BasePackageManager()
```

AEA package manager

<a id="aea.package_manager.base.BasePackageManager.__init__"></a>

#### `__`init`__`

```python
def __init__(path: Path) -> None
```

Initialize object.

<a id="aea.package_manager.base.BasePackageManager.add_package"></a>

#### add`_`package

```python
def add_package(package_id: PackageId) -> "BasePackageManager"
```

Add packages.

<a id="aea.package_manager.base.BasePackageManager.package_path_from_package_id"></a>

#### package`_`path`_`from`_`package`_`id

```python
def package_path_from_package_id(package_id: PackageId) -> Path
```

Get package path from the package id.

<a id="aea.package_manager.base.BasePackageManager.update_package"></a>

#### update`_`package

```python
def update_package(package_id: PackageId) -> "BasePackageManager"
```

Update package.

<a id="aea.package_manager.base.BasePackageManager.get_available_package_hashes"></a>

#### get`_`available`_`package`_`hashes

```python
def get_available_package_hashes() -> PackageIdToHashMapping
```

Returns a mapping object between available packages and their hashes

<a id="aea.package_manager.base.BasePackageManager.sync"></a>

#### sync

```python
@abstractmethod
def sync(dev: bool = False, third_party: bool = True, update_packages: bool = False, update_hashes: bool = False) -> "BasePackageManager"
```

Sync local packages to the remote registry.

<a id="aea.package_manager.base.BasePackageManager.update_package_hashes"></a>

#### update`_`package`_`hashes

```python
@abstractmethod
def update_package_hashes() -> "BasePackageManager"
```

Update package.json file.

<a id="aea.package_manager.base.BasePackageManager.verify"></a>

#### verify

```python
@abstractmethod
def verify(config_loader: Callable[
            [PackageType, Path], PackageConfiguration
        ] = load_configuration) -> int
```

Verify fingerprints and outer hash of all available packages.

<a id="aea.package_manager.base.BasePackageManager.json"></a>

#### json

```python
@property
@abstractmethod
def json() -> OrderedDictType
```

Json representation

<a id="aea.package_manager.base.BasePackageManager.dump"></a>

#### dump

```python
def dump(file: Optional[Path] = None) -> None
```

Dump package data to file.

<a id="aea.package_manager.base.BasePackageManager.from_dir"></a>

#### from`_`dir

```python
@classmethod
@abstractmethod
def from_dir(cls, packages_dir: Path) -> "BasePackageManager"
```

Initialize from packages directory.

<a id="aea.package_manager.base.PackageHashDoesNotMatch"></a>

## PackageHashDoesNotMatch Objects

```python
class PackageHashDoesNotMatch(Exception)
```

Package hash does not match error.

<a id="aea.package_manager.base.PackageUpdateError"></a>

## PackageUpdateError Objects

```python
class PackageUpdateError(Exception)
```

Package update error.

<a id="aea.package_manager.base.PackageNotValid"></a>

## PackageNotValid Objects

```python
class PackageNotValid(Exception)
```

Package not valid.

<a id="aea.package_manager.base.PackageFileNotValid"></a>

## PackageFileNotValid Objects

```python
class PackageFileNotValid(Exception)
```

Package file not valid.

