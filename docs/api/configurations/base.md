<a name="aea.configurations.base"></a>
# aea.configurations.base

Classes to handle AEA configurations.

<a name="aea.configurations.base.PyPIPackageName"></a>
## PyPIPackageName Objects

```python
class PyPIPackageName(RegexConstrainedString)
```

A PyPI Package name.

<a name="aea.configurations.base.GitRef"></a>
## GitRef Objects

```python
class GitRef(RegexConstrainedString)
```

A Git reference.

It can be a branch name, a commit hash or a tag.

<a name="aea.configurations.base.Dependency"></a>
## Dependency Objects

```python
class Dependency()
```

This class represents a PyPI dependency.

It contains the following information:
- version: a version specifier(s) (e.g. '==0.1.0').
- index: the PyPI index where to download the package from (default: https://pypi.org)
- git: the URL to the Git repository (e.g. https://github.com/fetchai/agents-aea.git)
- ref: either the branch name, the tag, the commit number or a Git reference (default: 'master'.)

If the 'git' field is set, the 'version' field will be ignored.
These fields will be forwarded to the 'pip' command.

<a name="aea.configurations.base.Dependency.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: Union[PyPIPackageName, str], version: Union[str, SpecifierSet] = "", index: Optional[Union[str, Url]] = None, git: Optional[Union[str, Url]] = None, ref: Optional[Union[GitRef, str]] = None)
```

Initialize a PyPI dependency.

**Arguments**:

- `name`: the package name.
- `version`: the specifier set object
- `index`: the URL to the PyPI server.
- `git`: the URL to a git repository.
- `ref`: the Git reference (branch/commit/tag).

<a name="aea.configurations.base.Dependency.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the name.

<a name="aea.configurations.base.Dependency.version"></a>
#### version

```python
 | @property
 | version() -> str
```

Get the version.

<a name="aea.configurations.base.Dependency.index"></a>
#### index

```python
 | @property
 | index() -> Optional[str]
```

Get the index.

<a name="aea.configurations.base.Dependency.git"></a>
#### git

```python
 | @property
 | git() -> Optional[str]
```

Get the git.

<a name="aea.configurations.base.Dependency.ref"></a>
#### ref

```python
 | @property
 | ref() -> Optional[str]
```

Get the ref.

<a name="aea.configurations.base.Dependency.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict[str, Dict[str, str]]) -> "Dependency"
```

Parse a dependency object from a dictionary.

<a name="aea.configurations.base.Dependency.to_json"></a>
#### to`_`json

```python
 | to_json() -> Dict[str, Dict[str, str]]
```

Transform the object to JSON.

<a name="aea.configurations.base.Dependency.get_pip_install_args"></a>
#### get`_`pip`_`install`_`args

```python
 | get_pip_install_args() -> List[str]
```

Get 'pip install' arguments.

<a name="aea.configurations.base.Dependency.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="aea.configurations.base.Dependency.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name="aea.configurations.base.Dependencies"></a>
#### Dependencies

A dictionary from package name to dependency data structure (see above).
The package name must satisfy  <a href="https://www.python.org/dev/peps/pep-0426/`name`">the constraints on Python packages names</a>.

The main advantage of having a dictionary is that we implicitly filter out dependency duplicates.
We cannot have two items with the same package name since the keys of a YAML object form a set.

<a name="aea.configurations.base.dependencies_from_json"></a>
#### dependencies`_`from`_`json

```python
dependencies_from_json(obj: Dict[str, Dict]) -> Dependencies
```

Parse a JSON object to get an instance of Dependencies.

**Arguments**:

- `obj`: a dictionary whose keys are package names and values are dictionary with package specifications.

**Returns**:

a Dependencies object.

<a name="aea.configurations.base.dependencies_to_json"></a>
#### dependencies`_`to`_`json

```python
dependencies_to_json(dependencies: Dependencies) -> Dict[str, Dict]
```

Transform a Dependencies object into a JSON object.

**Arguments**:

- `dependencies`: an instance of "Dependencies" type.

**Returns**:

a dictionary whose keys are package names and
values are the JSON version of a Dependency object.

<a name="aea.configurations.base.PackageVersion"></a>
## PackageVersion Objects

```python
@functools.total_ordering
class PackageVersion()
```

A package version.

<a name="aea.configurations.base.PackageVersion.__init__"></a>
#### `__`init`__`

```python
 | __init__(version_like: PackageVersionLike)
```

Initialize a package version.

**Arguments**:

- `version_like`: a string, os a semver.VersionInfo object.

<a name="aea.configurations.base.PackageVersion.is_latest"></a>
#### is`_`latest

```python
 | @property
 | is_latest() -> bool
```

Check whether the version is 'latest'.

<a name="aea.configurations.base.PackageVersion.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="aea.configurations.base.PackageVersion.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other) -> bool
```

Check equality.

<a name="aea.configurations.base.PackageVersion.__lt__"></a>
#### `__`lt`__`

```python
 | __lt__(other)
```

Compare with another object.

<a name="aea.configurations.base.PackageType"></a>
## PackageType Objects

```python
class PackageType(Enum)
```

Package types.

<a name="aea.configurations.base.PackageType.to_plural"></a>
#### to`_`plural

```python
 | to_plural() -> str
```

Get the plural name.

>>> PackageType.AGENT.to_plural()
'agents'
>>> PackageType.PROTOCOL.to_plural()
'protocols'
>>> PackageType.CONNECTION.to_plural()
'connections'
>>> PackageType.SKILL.to_plural()
'skills'
>>> PackageType.CONTRACT.to_plural()
'contracts'

<a name="aea.configurations.base.PackageType.configuration_class"></a>
#### configuration`_`class

```python
 | configuration_class() -> Type["PackageConfiguration"]
```

Get the configuration class.

<a name="aea.configurations.base.PackageType.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Convert to string.

<a name="aea.configurations.base.ComponentType"></a>
## ComponentType Objects

```python
class ComponentType(Enum)
```

Enum of component types supported.

<a name="aea.configurations.base.ComponentType.to_configuration_type"></a>
#### to`_`configuration`_`type

```python
 | to_configuration_type() -> PackageType
```

Get package type for component type.

<a name="aea.configurations.base.ComponentType.plurals"></a>
#### plurals

```python
 | @staticmethod
 | plurals() -> Collection[str]
```

Get the collection of type names, plural.

>>> ComponentType.plurals()
['protocols', 'connections', 'skills', 'contracts']

<a name="aea.configurations.base.ComponentType.to_plural"></a>
#### to`_`plural

```python
 | to_plural() -> str
```

Get the plural version of the component type.

>>> ComponentType.PROTOCOL.to_plural()
'protocols'
>>> ComponentType.CONNECTION.to_plural()
'connections'
>>> ComponentType.SKILL.to_plural()
'skills'
>>> ComponentType.CONTRACT.to_plural()
'contracts'

<a name="aea.configurations.base.ComponentType.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="aea.configurations.base.ProtocolSpecificationParseError"></a>
## ProtocolSpecificationParseError Objects

```python
class ProtocolSpecificationParseError(Exception)
```

Exception for parsing a protocol specification file.

<a name="aea.configurations.base.JSONSerializable"></a>
## JSONSerializable Objects

```python
class JSONSerializable(ABC)
```

Interface for JSON-serializable objects.

<a name="aea.configurations.base.JSONSerializable.json"></a>
#### json

```python
 | @property
 | @abstractmethod
 | json() -> Dict
```

Compute the JSON representation.

<a name="aea.configurations.base.JSONSerializable.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Build from a JSON object.

<a name="aea.configurations.base.Configuration"></a>
## Configuration Objects

```python
class Configuration(JSONSerializable,  ABC)
```

Configuration class.

<a name="aea.configurations.base.Configuration.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Initialize a configuration object.

<a name="aea.configurations.base.Configuration.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict) -> "Configuration"
```

Build from a JSON object.

<a name="aea.configurations.base.Configuration.ordered_json"></a>
#### ordered`_`json

```python
 | @property
 | ordered_json() -> OrderedDict
```

Reorder the dictionary according to a key ordering.

This method takes all the keys in the key_order list and
get the associated value in the dictionary (if present).
For the remaining keys not considered in the order,
it will use alphanumerical ordering.

In particular, if key_order is an empty sequence, this reduces to
alphanumerical sorting.

It does not do side-effect.

**Returns**:

the ordered dictionary.

<a name="aea.configurations.base.CRUDCollection"></a>
## CRUDCollection Objects

```python
class CRUDCollection(Generic[T])
```

Interface of a CRUD collection.

<a name="aea.configurations.base.CRUDCollection.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate a CRUD collection.

<a name="aea.configurations.base.CRUDCollection.create"></a>
#### create

```python
 | create(item_id: str, item: T) -> None
```

Add an item.

**Arguments**:

- `item_id`: the item id.
- `item`: the item to be added.

**Returns**:

None

**Raises**:

- `ValueError`: if the item with the same id is already in the collection.

<a name="aea.configurations.base.CRUDCollection.read"></a>
#### read

```python
 | read(item_id: str) -> Optional[T]
```

Get an item by its name.

**Arguments**:

- `item_id`: the item id.

**Returns**:

the associated item, or None if the item id is not present.

<a name="aea.configurations.base.CRUDCollection.update"></a>
#### update

```python
 | update(item_id: str, item: T) -> None
```

Update an existing item.

**Arguments**:

- `item_id`: the item id.
- `item`: the item to be added.

**Returns**:

None

<a name="aea.configurations.base.CRUDCollection.delete"></a>
#### delete

```python
 | delete(item_id: str) -> None
```

Delete an item.

<a name="aea.configurations.base.CRUDCollection.read_all"></a>
#### read`_`all

```python
 | read_all() -> List[Tuple[str, T]]
```

Read all the items.

<a name="aea.configurations.base.PublicId"></a>
## PublicId Objects

```python
class PublicId(JSONSerializable)
```

This class implement a public identifier.

A public identifier is composed of three elements:
- author
- name
- version

The concatenation of those three elements gives the public identifier:

    author/name:version

>>> public_id = PublicId("author", "my_package", "0.1.0")
>>> assert public_id.author == "author"
>>> assert public_id.name == "my_package"
>>> assert public_id.version == "0.1.0"
>>> another_public_id = PublicId("author", "my_package", "0.1.0")
>>> assert hash(public_id) == hash(another_public_id)
>>> assert public_id == another_public_id
>>> latest_public_id = PublicId("author", "my_package", "latest")
>>> latest_public_id
<author/my_package:latest>
>>> latest_public_id.package_version.is_latest
True

<a name="aea.configurations.base.PublicId.__init__"></a>
#### `__`init`__`

```python
 | __init__(author: str, name: str, version: Optional[PackageVersionLike] = None)
```

Initialize the public identifier.

<a name="aea.configurations.base.PublicId.author"></a>
#### author

```python
 | @property
 | author() -> str
```

Get the author.

<a name="aea.configurations.base.PublicId.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the name.

<a name="aea.configurations.base.PublicId.version"></a>
#### version

```python
 | @property
 | version() -> str
```

Get the version string.

<a name="aea.configurations.base.PublicId.package_version"></a>
#### package`_`version

```python
 | @property
 | package_version() -> PackageVersion
```

Get the package version object.

<a name="aea.configurations.base.PublicId.latest"></a>
#### latest

```python
 | @property
 | latest() -> str
```

Get the public id in `latest` form.

<a name="aea.configurations.base.PublicId.same_prefix"></a>
#### same`_`prefix

```python
 | same_prefix(other: "PublicId") -> bool
```

Check if the other public id has the same author and name of this.

<a name="aea.configurations.base.PublicId.to_latest"></a>
#### to`_`latest

```python
 | to_latest() -> "PublicId"
```

Return the same public id, but with latest version.

<a name="aea.configurations.base.PublicId.is_valid_str"></a>
#### is`_`valid`_`str

```python
 | @classmethod
 | is_valid_str(cls, public_id_string: str) -> bool
```

Check if a string is a public id.

**Arguments**:

- `public_id_string`: the public id in string format.

**Returns**:

bool indicating validity

<a name="aea.configurations.base.PublicId.from_str"></a>
#### from`_`str

```python
 | @classmethod
 | from_str(cls, public_id_string: str) -> "PublicId"
```

Initialize the public id from the string.

>>> str(PublicId.from_str("author/package_name:0.1.0"))
'author/package_name:0.1.0'

A bad formatted input raises value error:
>>> PublicId.from_str("bad/formatted:input")
Traceback (most recent call last):
...
ValueError: Input 'bad/formatted:input' is not well formatted.

**Arguments**:

- `public_id_string`: the public id in string format.

**Returns**:

the public id object.

**Raises**:

- `ValueError`: if the string in input is not well formatted.

<a name="aea.configurations.base.PublicId.from_uri_path"></a>
#### from`_`uri`_`path

```python
 | @classmethod
 | from_uri_path(cls, public_id_uri_path: str) -> "PublicId"
```

Initialize the public id from the string.

>>> str(PublicId.from_uri_path("author/package_name/0.1.0"))
'author/package_name:0.1.0'

A bad formatted input raises value error:
>>> PublicId.from_uri_path("bad/formatted:input")
Traceback (most recent call last):
...
ValueError: Input 'bad/formatted:input' is not well formatted.

**Arguments**:

- `public_id_uri_path`: the public id in uri path string format.

**Returns**:

the public id object.

**Raises**:

- `ValueError`: if the string in input is not well formatted.

<a name="aea.configurations.base.PublicId.to_uri_path"></a>
#### to`_`uri`_`path

```python
 | @property
 | to_uri_path() -> str
```

Turn the public id into a uri path string.

**Returns**:

uri path string

<a name="aea.configurations.base.PublicId.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Compute the JSON representation.

<a name="aea.configurations.base.PublicId.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Build from a JSON object.

<a name="aea.configurations.base.PublicId.__hash__"></a>
#### `__`hash`__`

```python
 | __hash__()
```

Get the hash.

<a name="aea.configurations.base.PublicId.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name="aea.configurations.base.PublicId.__repr__"></a>
#### `__`repr`__`

```python
 | __repr__()
```

Get the representation.

<a name="aea.configurations.base.PublicId.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name="aea.configurations.base.PublicId.__lt__"></a>
#### `__`lt`__`

```python
 | __lt__(other)
```

Compare two public ids.

>>> public_id_1 = PublicId("author_1", "name_1", "0.1.0")
>>> public_id_2 = PublicId("author_1", "name_1", "0.1.1")
>>> public_id_3 = PublicId("author_1", "name_2", "0.1.0")
>>> public_id_1 > public_id_2
False
>>> public_id_1 < public_id_2
True

>>> public_id_1 < public_id_3
Traceback (most recent call last):
...
ValueError: The public IDs author_1/name_1:0.1.0 and author_1/name_2:0.1.0 cannot be compared. Their author or name attributes are different.

<a name="aea.configurations.base.PackageId"></a>
## PackageId Objects

```python
class PackageId()
```

A package identifier.

<a name="aea.configurations.base.PackageId.__init__"></a>
#### `__`init`__`

```python
 | __init__(package_type: Union[PackageType, str], public_id: PublicId)
```

Initialize the package id.

**Arguments**:

- `package_type`: the package type.
- `public_id`: the public id.

<a name="aea.configurations.base.PackageId.package_type"></a>
#### package`_`type

```python
 | @property
 | package_type() -> PackageType
```

Get the package type.

<a name="aea.configurations.base.PackageId.public_id"></a>
#### public`_`id

```python
 | @property
 | public_id() -> PublicId
```

Get the public id.

<a name="aea.configurations.base.PackageId.author"></a>
#### author

```python
 | @property
 | author() -> str
```

Get the author of the package.

<a name="aea.configurations.base.PackageId.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the name of the package.

<a name="aea.configurations.base.PackageId.version"></a>
#### version

```python
 | @property
 | version() -> str
```

Get the version of the package.

<a name="aea.configurations.base.PackageId.package_prefix"></a>
#### package`_`prefix

```python
 | @property
 | package_prefix() -> Tuple[PackageType, str, str]
```

Get the package identifier without the version.

<a name="aea.configurations.base.PackageId.from_uri_path"></a>
#### from`_`uri`_`path

```python
 | @classmethod
 | from_uri_path(cls, package_id_uri_path: str) -> "PackageId"
```

Initialize the public id from the string.

>>> str(PackageId.from_uri_path("skill/author/package_name/0.1.0"))
'(skill, author/package_name:0.1.0)'

A bad formatted input raises value error:
>>> PackageId.from_uri_path("very/bad/formatted:input")
Traceback (most recent call last):
...
ValueError: Input 'very/bad/formatted:input' is not well formatted.

**Arguments**:

- `public_id_uri_path`: the public id in uri path string format.

**Returns**:

the public id object.

**Raises**:

- `ValueError`: if the string in input is not well formatted.

<a name="aea.configurations.base.PackageId.to_uri_path"></a>
#### to`_`uri`_`path

```python
 | @property
 | to_uri_path() -> str
```

Turn the package id into a uri path string.

**Returns**:

uri path string

<a name="aea.configurations.base.PackageId.__hash__"></a>
#### `__`hash`__`

```python
 | __hash__()
```

Get the hash.

<a name="aea.configurations.base.PackageId.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name="aea.configurations.base.PackageId.__repr__"></a>
#### `__`repr`__`

```python
 | __repr__()
```

Get the object representation in string.

<a name="aea.configurations.base.PackageId.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name="aea.configurations.base.PackageId.__lt__"></a>
#### `__`lt`__`

```python
 | __lt__(other)
```

Compare two public ids.

<a name="aea.configurations.base.ComponentId"></a>
## ComponentId Objects

```python
class ComponentId(PackageId)
```

Class to represent a component identifier.

A component id is a package id, but excludes the case when the package is an agent.
>>> pacakge_id = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.1.0"))
>>> component_id = ComponentId(ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0"))
>>> pacakge_id == component_id
True

>>> component_id2 = ComponentId(ComponentType.PROTOCOL, PublicId("author", "name", "0.1.1"))
>>> pacakge_id == component_id2
False

<a name="aea.configurations.base.ComponentId.__init__"></a>
#### `__`init`__`

```python
 | __init__(component_type: Union[ComponentType, str], public_id: PublicId)
```

Initialize the component id.

**Arguments**:

- `component_type`: the component type.
- `public_id`: the public id.

<a name="aea.configurations.base.ComponentId.component_type"></a>
#### component`_`type

```python
 | @property
 | component_type() -> ComponentType
```

Get the component type.

<a name="aea.configurations.base.ComponentId.component_prefix"></a>
#### component`_`prefix

```python
 | @property
 | component_prefix() -> Tuple[ComponentType, str, str]
```

Get the component identifier without the version.

<a name="aea.configurations.base.ComponentId.prefix_import_path"></a>
#### prefix`_`import`_`path

```python
 | @property
 | prefix_import_path() -> str
```

Get the prefix import path for this component.

<a name="aea.configurations.base.ComponentId.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Get the JSON representation.

<a name="aea.configurations.base.PackageConfiguration"></a>
## PackageConfiguration Objects

```python
class PackageConfiguration(Configuration,  ABC)
```

This class represent a package configuration.

A package can be one of:
- agents
- protocols
- connections
- skills
- contracts

<a name="aea.configurations.base.PackageConfiguration.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, author: str, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None)
```

Initialize a package configuration.

**Arguments**:

- `name`: the name of the package.
- `author`: the author of the package.
- `version`: the version of the package (SemVer format).
- `license_`: the license.
- `aea_version`: either a fixed version, or a set of specifiers
describing the AEA versions allowed.
(default: empty string - no constraint).
The fixed version is interpreted with the specifier '=='.
- `fingerprint`: the fingerprint.
- `fingerprint_ignore_patterns`: a list of file patterns to ignore files to fingerprint.

<a name="aea.configurations.base.PackageConfiguration.directory"></a>
#### directory

```python
 | @property
 | directory() -> Optional[Path]
```

Get the path to the configuration file associated to this file, if any.

<a name="aea.configurations.base.PackageConfiguration.directory"></a>
#### directory

```python
 | @directory.setter
 | directory(directory: Path) -> None
```

Set directory if not already set.

<a name="aea.configurations.base.PackageConfiguration.aea_version_specifiers"></a>
#### aea`_`version`_`specifiers

```python
 | @property
 | aea_version_specifiers() -> SpecifierSet
```

Get the AEA version set specifier.

<a name="aea.configurations.base.PackageConfiguration.public_id"></a>
#### public`_`id

```python
 | @property
 | public_id() -> PublicId
```

Get the public id.

<a name="aea.configurations.base.PackageConfiguration.package_dependencies"></a>
#### package`_`dependencies

```python
 | @property
 | package_dependencies() -> Set[ComponentId]
```

Get the package dependencies.

<a name="aea.configurations.base.PackageConfiguration.update"></a>
#### update

```python
 | update(data: Dict) -> None
```

Update configuration with other data.

**Arguments**:

- `data`: the data to replace.

**Returns**:

None

<a name="aea.configurations.base.ComponentConfiguration"></a>
## ComponentConfiguration Objects

```python
class ComponentConfiguration(PackageConfiguration,  ABC)
```

Class to represent an agent component configuration.

<a name="aea.configurations.base.ComponentConfiguration.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, author: str, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, dependencies: Optional[Dependencies] = None)
```

Set component configuration.

<a name="aea.configurations.base.ComponentConfiguration.component_type"></a>
#### component`_`type

```python
 | @property
 | component_type() -> ComponentType
```

Get the component type.

<a name="aea.configurations.base.ComponentConfiguration.component_id"></a>
#### component`_`id

```python
 | @property
 | component_id() -> ComponentId
```

Get the component id.

<a name="aea.configurations.base.ComponentConfiguration.prefix_import_path"></a>
#### prefix`_`import`_`path

```python
 | @property
 | prefix_import_path() -> str
```

Get the prefix import path for this component.

<a name="aea.configurations.base.ComponentConfiguration.is_abstract_component"></a>
#### is`_`abstract`_`component

```python
 | @property
 | is_abstract_component() -> bool
```

Check whether the component is abstract.

<a name="aea.configurations.base.ComponentConfiguration.check_fingerprint"></a>
#### check`_`fingerprint

```python
 | check_fingerprint(directory: Path) -> None
```

Check that the fingerprint are correct against a directory path.

:raises ValueError if:
- the argument is not a valid package directory
- the fingerprints do not match.

<a name="aea.configurations.base.ComponentConfiguration.check_aea_version"></a>
#### check`_`aea`_`version

```python
 | check_aea_version()
```

Check that the AEA version matches the specifier set.

:raises ValueError if the version of the aea framework falls within a specifier.

<a name="aea.configurations.base.ConnectionConfig"></a>
## ConnectionConfig Objects

```python
class ConnectionConfig(ComponentConfiguration)
```

Handle connection configuration.

<a name="aea.configurations.base.ConnectionConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str = "", author: str = "", version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, class_name: str = "", protocols: Optional[Set[PublicId]] = None, restricted_to_protocols: Optional[Set[PublicId]] = None, excluded_protocols: Optional[Set[PublicId]] = None, dependencies: Optional[Dependencies] = None, description: str = "", connection_id: Optional[PublicId] = None, **config, ,)
```

Initialize a connection configuration object.

<a name="aea.configurations.base.ConnectionConfig.package_dependencies"></a>
#### package`_`dependencies

```python
 | @property
 | package_dependencies() -> Set[ComponentId]
```

Get the connection dependencies.

<a name="aea.configurations.base.ConnectionConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.configurations.base.ConnectionConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name="aea.configurations.base.ConnectionConfig.update"></a>
#### update

```python
 | update(data: Dict) -> None
```

Update configuration with other data.

This method does side-effect on the configuration object.

**Arguments**:

- `data`: the data to populate or replace.

**Returns**:

None

<a name="aea.configurations.base.ProtocolConfig"></a>
## ProtocolConfig Objects

```python
class ProtocolConfig(ComponentConfiguration)
```

Handle protocol configuration.

<a name="aea.configurations.base.ProtocolConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, author: str, version: str = "", license_: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, aea_version: str = "", dependencies: Optional[Dependencies] = None, description: str = "")
```

Initialize a connection configuration object.

<a name="aea.configurations.base.ProtocolConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.configurations.base.ProtocolConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name="aea.configurations.base.SkillComponentConfiguration"></a>
## SkillComponentConfiguration Objects

```python
class SkillComponentConfiguration()
```

This class represent a skill component configuration.

<a name="aea.configurations.base.SkillComponentConfiguration.__init__"></a>
#### `__`init`__`

```python
 | __init__(class_name: str, **args)
```

Initialize a skill component configuration.

**Arguments**:

- `skill_component_type`: the skill component type.
- `class_name`: the class name of the component.
- `args`: keyword arguments.

<a name="aea.configurations.base.SkillComponentConfiguration.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.configurations.base.SkillComponentConfiguration.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name="aea.configurations.base.SkillConfig"></a>
## SkillConfig Objects

```python
class SkillConfig(ComponentConfiguration)
```

Class to represent a skill configuration file.

<a name="aea.configurations.base.SkillConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, author: str, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, protocols: List[PublicId] = None, contracts: List[PublicId] = None, skills: List[PublicId] = None, dependencies: Optional[Dependencies] = None, description: str = "", is_abstract: bool = False)
```

Initialize a skill configuration.

<a name="aea.configurations.base.SkillConfig.package_dependencies"></a>
#### package`_`dependencies

```python
 | @property
 | package_dependencies() -> Set[ComponentId]
```

Get the skill dependencies.

<a name="aea.configurations.base.SkillConfig.is_abstract_component"></a>
#### is`_`abstract`_`component

```python
 | @property
 | is_abstract_component() -> bool
```

Check whether the component is abstract.

<a name="aea.configurations.base.SkillConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.configurations.base.SkillConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name="aea.configurations.base.SkillConfig.update"></a>
#### update

```python
 | update(data: Dict) -> None
```

Update configuration with other data.

**Arguments**:

- `data`: the data to replace.

**Returns**:

None

<a name="aea.configurations.base.AgentConfig"></a>
## AgentConfig Objects

```python
class AgentConfig(PackageConfiguration)
```

Class to represent the agent configuration file.

<a name="aea.configurations.base.AgentConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_name: str, author: str, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, registry_path: str = DEFAULT_REGISTRY_PATH, description: str = "", logging_config: Optional[Dict] = None, period: Optional[float] = None, execution_timeout: Optional[float] = None, max_reactions: Optional[int] = None, decision_maker_handler: Optional[Dict] = None, skill_exception_policy: Optional[str] = None, connection_exception_policy: Optional[str] = None, default_routing: Optional[Dict] = None, loop_mode: Optional[str] = None, runtime_mode: Optional[str] = None, component_configurations: Optional[Dict[ComponentId, Dict]] = None)
```

Instantiate the agent configuration object.

<a name="aea.configurations.base.AgentConfig.component_configurations"></a>
#### component`_`configurations

```python
 | @property
 | component_configurations() -> Dict[ComponentId, Dict]
```

Get the custom component configurations.

<a name="aea.configurations.base.AgentConfig.component_configurations"></a>
#### component`_`configurations

```python
 | @component_configurations.setter
 | component_configurations(d: Dict[ComponentId, Dict]) -> None
```

Set the component configurations.

<a name="aea.configurations.base.AgentConfig.package_dependencies"></a>
#### package`_`dependencies

```python
 | @property
 | package_dependencies() -> Set[ComponentId]
```

Get the package dependencies.

<a name="aea.configurations.base.AgentConfig.private_key_paths_dict"></a>
#### private`_`key`_`paths`_`dict

```python
 | @property
 | private_key_paths_dict() -> Dict[str, str]
```

Get dictionary version of private key paths.

<a name="aea.configurations.base.AgentConfig.connection_private_key_paths_dict"></a>
#### connection`_`private`_`key`_`paths`_`dict

```python
 | @property
 | connection_private_key_paths_dict() -> Dict[str, str]
```

Get dictionary version of connection private key paths.

<a name="aea.configurations.base.AgentConfig.default_connection"></a>
#### default`_`connection

```python
 | @property
 | default_connection() -> str
```

Get the default connection.

<a name="aea.configurations.base.AgentConfig.default_connection"></a>
#### default`_`connection

```python
 | @default_connection.setter
 | default_connection(connection_id: Optional[Union[str, PublicId]])
```

Set the default connection.

**Arguments**:

- `connection_id`: the name of the default connection.

**Returns**:

None

<a name="aea.configurations.base.AgentConfig.default_ledger"></a>
#### default`_`ledger

```python
 | @property
 | default_ledger() -> str
```

Get the default ledger.

<a name="aea.configurations.base.AgentConfig.default_ledger"></a>
#### default`_`ledger

```python
 | @default_ledger.setter
 | default_ledger(ledger_id: str)
```

Set the default ledger.

**Arguments**:

- `ledger_id`: the id of the default ledger.

**Returns**:

None

<a name="aea.configurations.base.AgentConfig.component_configurations_json"></a>
#### component`_`configurations`_`json

```python
 | component_configurations_json() -> List[OrderedDict]
```

Get the component configurations in JSON format.

<a name="aea.configurations.base.AgentConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.configurations.base.AgentConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name="aea.configurations.base.AgentConfig.update"></a>
#### update

```python
 | update(data: Dict) -> None
```

Update configuration with other data.

To update the component parts, populate the field "component_configurations" as a
mapping from ComponentId to configurations.

**Arguments**:

- `data`: the data to replace.

**Returns**:

None

<a name="aea.configurations.base.SpeechActContentConfig"></a>
## SpeechActContentConfig Objects

```python
class SpeechActContentConfig(Configuration)
```

Handle a speech_act content configuration.

<a name="aea.configurations.base.SpeechActContentConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(**args)
```

Initialize a speech_act content configuration.

<a name="aea.configurations.base.SpeechActContentConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.configurations.base.SpeechActContentConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name="aea.configurations.base.ProtocolSpecification"></a>
## ProtocolSpecification Objects

```python
class ProtocolSpecification(ProtocolConfig)
```

Handle protocol specification.

<a name="aea.configurations.base.ProtocolSpecification.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, author: str, version: str = "", license_: str = "", aea_version: str = "", description: str = "")
```

Initialize a protocol specification configuration object.

<a name="aea.configurations.base.ProtocolSpecification.protobuf_snippets"></a>
#### protobuf`_`snippets

```python
 | @property
 | protobuf_snippets() -> Dict
```

Get the protobuf snippets.

<a name="aea.configurations.base.ProtocolSpecification.protobuf_snippets"></a>
#### protobuf`_`snippets

```python
 | @protobuf_snippets.setter
 | protobuf_snippets(protobuf_snippets: Dict)
```

Set the protobuf snippets.

<a name="aea.configurations.base.ProtocolSpecification.dialogue_config"></a>
#### dialogue`_`config

```python
 | @property
 | dialogue_config() -> Dict
```

Get the dialogue config.

<a name="aea.configurations.base.ProtocolSpecification.dialogue_config"></a>
#### dialogue`_`config

```python
 | @dialogue_config.setter
 | dialogue_config(dialogue_config: Dict)
```

Set the dialogue config.

<a name="aea.configurations.base.ProtocolSpecification.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.configurations.base.ProtocolSpecification.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name="aea.configurations.base.ContractConfig"></a>
## ContractConfig Objects

```python
class ContractConfig(ComponentConfiguration)
```

Handle contract configuration.

<a name="aea.configurations.base.ContractConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, author: str, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, dependencies: Optional[Dependencies] = None, description: str = "", contract_interface_paths: Optional[Dict[str, str]] = None, class_name: str = "")
```

Initialize a protocol configuration object.

<a name="aea.configurations.base.ContractConfig.contract_interfaces"></a>
#### contract`_`interfaces

```python
 | @property
 | contract_interfaces() -> Dict[str, str]
```

Get the contract interfaces.

<a name="aea.configurations.base.ContractConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.configurations.base.ContractConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

