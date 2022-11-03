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

<a id="aea.package_manager.base.PackageManager"></a>

## PackageManager Objects

```python
class PackageManager()
```

AEA package manager

<a id="aea.package_manager.base.PackageManager.__init__"></a>

#### `__`init`__`

```python
def __init__(path: Path, packages: Optional[OrderedDictType[PackageId, str]] = None) -> None
```

Initialize object.

<a id="aea.package_manager.base.PackageManager.packages"></a>

#### packages

```python
@property
def packages() -> OrderedDictType[PackageId, str]
```

Returns mappings of package ids -> package hash

<a id="aea.package_manager.base.PackageManager.sync"></a>

#### sync

```python
def sync(update_packages: bool = False, update_hashes: bool = False) -> "PackageManager"
```

Sync local packages to the remote registry.

**Arguments**:

                        package does not match the one in the packages.json.
                      hash for a package does not match the one in the
                      packages.json.
- `update_packages`: Update packages if the calculated hash for a
- `update_hashes`: Update hashes in the packages.json if the calculated

**Returns**:

PackageManager object

<a id="aea.package_manager.base.PackageManager.add_package"></a>

#### add`_`package

```python
def add_package(package_id: PackageId) -> "PackageManager"
```

Add packages.

<a id="aea.package_manager.base.PackageManager.update_package"></a>

#### update`_`package

```python
def update_package(package_path: Path, package_id: PackageId) -> "PackageManager"
```

Update package.

<a id="aea.package_manager.base.PackageManager.get_available_package_hashes"></a>

#### get`_`available`_`package`_`hashes

```python
def get_available_package_hashes() -> OrderedDictType[PackageId, str]
```

Returns a mapping object between available packages and their hashes

<a id="aea.package_manager.base.PackageManager.update_package_hashes"></a>

#### update`_`package`_`hashes

```python
def update_package_hashes() -> "PackageManager"
```

Initialize package.json file.

<a id="aea.package_manager.base.PackageManager.package_path_from_package_id"></a>

#### package`_`path`_`from`_`package`_`id

```python
def package_path_from_package_id(package_id: PackageId) -> Path
```

Get package path from the package id.

<a id="aea.package_manager.base.PackageManager.verify"></a>

#### verify

```python
def verify(config_loader: Callable[
            [PackageType, Path], PackageConfiguration
        ] = load_configuration) -> int
```

Verify fingerprints and outer hash of all available packages.

<a id="aea.package_manager.base.PackageManager.dump"></a>

#### dump

```python
def dump(file: Optional[Path] = None) -> None
```

Dump package data to file.

<a id="aea.package_manager.base.PackageManager.json"></a>

#### json

```python
@property
def json() -> OrderedDictType
```

Json representation

<a id="aea.package_manager.base.PackageManager.from_dir"></a>

#### from`_`dir

```python
@classmethod
def from_dir(cls, packages_dir: Path) -> "PackageManager"
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

