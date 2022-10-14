<a id="aea.configurations.data_types"></a>

# aea.configurations.data`_`types

Base config data types.

<a id="aea.configurations.data_types.JSONSerializable"></a>

## JSONSerializable Objects

```python
class JSONSerializable(ABC)
```

Interface for JSON-serializable objects.

<a id="aea.configurations.data_types.JSONSerializable.json"></a>

#### json

```python
@property
@abstractmethod
def json() -> Dict
```

Compute the JSON representation.

<a id="aea.configurations.data_types.JSONSerializable.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "JSONSerializable"
```

Build from a JSON object.

<a id="aea.configurations.data_types.PackageVersion"></a>

## PackageVersion Objects

```python
@functools.total_ordering
class PackageVersion()
```

A package version.

<a id="aea.configurations.data_types.PackageVersion.__init__"></a>

#### `__`init`__`

```python
def __init__(version_like: PackageVersionLike) -> None
```

Initialize a package version.

**Arguments**:

- `version_like`: a string, os a semver.VersionInfo object.

<a id="aea.configurations.data_types.PackageVersion.is_latest"></a>

#### is`_`latest

```python
@property
def is_latest() -> bool
```

Check whether the version is 'latest'.

<a id="aea.configurations.data_types.PackageVersion.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="aea.configurations.data_types.PackageVersion.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="aea.configurations.data_types.PackageVersion.__lt__"></a>

#### `__`lt`__`

```python
def __lt__(other: Any) -> bool
```

Compare with another object.

<a id="aea.configurations.data_types.PackageType"></a>

## PackageType Objects

```python
class PackageType(Enum)
```

Package types.

<a id="aea.configurations.data_types.PackageType.to_plural"></a>

#### to`_`plural

```python
def to_plural() -> str
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

**Returns**:

pluralised package type

<a id="aea.configurations.data_types.PackageType.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Convert to string.

<a id="aea.configurations.data_types.ComponentType"></a>

## ComponentType Objects

```python
class ComponentType(Enum)
```

Enum of component types supported.

<a id="aea.configurations.data_types.ComponentType.to_package_type"></a>

#### to`_`package`_`type

```python
def to_package_type() -> PackageType
```

Get package type for component type.

<a id="aea.configurations.data_types.ComponentType.plurals"></a>

#### plurals

```python
@staticmethod
def plurals() -> Collection[str]
```

Get the collection of type names, plural.

>>> ComponentType.plurals()
['protocols', 'connections', 'skills', 'contracts']

**Returns**:

list of all pluralised component types

<a id="aea.configurations.data_types.ComponentType.to_plural"></a>

#### to`_`plural

```python
def to_plural() -> str
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

**Returns**:

pluralised component type

<a id="aea.configurations.data_types.ComponentType.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="aea.configurations.data_types.PublicId"></a>

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

<a id="aea.configurations.data_types.PublicId.__init__"></a>

#### `__`init`__`

```python
def __init__(author: SimpleIdOrStr, name: SimpleIdOrStr, version: Optional[PackageVersionLike] = None, package_hash: Optional[IPFSHashOrStr] = None) -> None
```

Initialize the public identifier.

<a id="aea.configurations.data_types.PublicId.author"></a>

#### author

```python
@property
def author() -> str
```

Get the author.

<a id="aea.configurations.data_types.PublicId.name"></a>

#### name

```python
@property
def name() -> str
```

Get the name.

<a id="aea.configurations.data_types.PublicId.version"></a>

#### version

```python
@property
def version() -> str
```

Get the version string.

<a id="aea.configurations.data_types.PublicId.package_version"></a>

#### package`_`version

```python
@property
def package_version() -> PackageVersion
```

Get the package version object.

<a id="aea.configurations.data_types.PublicId.hash"></a>

#### hash

```python
@property
def hash() -> str
```

Returns the hash for the package.

<a id="aea.configurations.data_types.PublicId.same_prefix"></a>

#### same`_`prefix

```python
def same_prefix(other: "PublicId") -> bool
```

Check if the other public id has the same author and name of this.

<a id="aea.configurations.data_types.PublicId.to_any"></a>

#### to`_`any

```python
def to_any() -> "PublicId"
```

Return the same public id, but with any version.

<a id="aea.configurations.data_types.PublicId.to_latest"></a>

#### to`_`latest

```python
def to_latest() -> "PublicId"
```

Return the same public id, but with latest version.

<a id="aea.configurations.data_types.PublicId.is_valid_str"></a>

#### is`_`valid`_`str

```python
@classmethod
def is_valid_str(cls, public_id_string: str) -> bool
```

Check if a string is a public id.

**Arguments**:

- `public_id_string`: the public id in string format.

**Returns**:

bool indicating validity

<a id="aea.configurations.data_types.PublicId.from_str"></a>

#### from`_`str

```python
@classmethod
def from_str(cls, public_id_string: str) -> "PublicId"
```

Initialize the public id from the string.

>>> str(PublicId.from_str("author/package_name:0.1.0"))
'author/package_name:0.1.0'

>>> str(PublicId.from_str("author/package_name:0.1.0:QmYAXgX8ARiriupMQsbGXtKdDyGzWry1YV3sycKw1qqmgH"))
'author/package_name:0.1.0:QmYAXgX8ARiriupMQsbGXtKdDyGzWry1YV3sycKw1qqmgH'

A bad formatted input raises value error:
>>> PublicId.from_str("bad/formatted:input")
Traceback (most recent call last):
...
ValueError: Input 'bad/formatted:input' is not well formatted.

>>> PublicId.from_str("bad/formatted:0.1.0:Qmbadhash")
Traceback (most recent call last):
...
ValueError: Input 'bad/formatted:0.1.0:Qmbadhash' is not well formatted.

**Arguments**:

- `public_id_string`: the public id in string format.

**Returns**:

the public id object.

**Raises**:

- `ValueError`: if the string in input is not well formatted.

<a id="aea.configurations.data_types.PublicId.try_from_str"></a>

#### try`_`from`_`str

```python
@classmethod
def try_from_str(cls, public_id_string: str) -> Optional["PublicId"]
```

Safely try to get public id from string.

**Arguments**:

- `public_id_string`: the public id in string format.

**Returns**:

the public id object or None

<a id="aea.configurations.data_types.PublicId.from_uri_path"></a>

#### from`_`uri`_`path

```python
@classmethod
def from_uri_path(cls, public_id_uri_path: str) -> "PublicId"
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

<a id="aea.configurations.data_types.PublicId.to_uri_path"></a>

#### to`_`uri`_`path

```python
@property
def to_uri_path() -> str
```

Turn the public id into a uri path string.

**Returns**:

uri path string

<a id="aea.configurations.data_types.PublicId.json"></a>

#### json

```python
@property
def json() -> Dict
```

Compute the JSON representation.

<a id="aea.configurations.data_types.PublicId.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "PublicId"
```

Build from a JSON object.

<a id="aea.configurations.data_types.PublicId.__hash__"></a>

#### `__`hash`__`

```python
def __hash__() -> int
```

Get the hash.

<a id="aea.configurations.data_types.PublicId.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Get the representation.

<a id="aea.configurations.data_types.PublicId.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Compare with another object.

<a id="aea.configurations.data_types.PublicId.__lt__"></a>

#### `__`lt`__`

```python
def __lt__(other: Any) -> bool
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

**Arguments**:

- `other`: the object to compate to

**Raises**:

- `ValueError`: if the public ids cannot be confirmed

**Returns**:

whether or not the inequality is satisfied

<a id="aea.configurations.data_types.PublicId.without_hash"></a>

#### without`_`hash

```python
def without_hash() -> "PublicId"
```

Returns a `PublicId` object with same parameters.

<a id="aea.configurations.data_types.PublicId.with_hash"></a>

#### with`_`hash

```python
def with_hash(package_hash: str) -> "PublicId"
```

Returns a `PublicId` object with same parameters.

<a id="aea.configurations.data_types.PublicId.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="aea.configurations.data_types.PackageId"></a>

## PackageId Objects

```python
class PackageId()
```

A package identifier.

<a id="aea.configurations.data_types.PackageId.__init__"></a>

#### `__`init`__`

```python
def __init__(package_type: Union[PackageType, str], public_id: PublicId) -> None
```

Initialize the package id.

**Arguments**:

- `package_type`: the package type.
- `public_id`: the public id.

<a id="aea.configurations.data_types.PackageId.package_type"></a>

#### package`_`type

```python
@property
def package_type() -> PackageType
```

Get the package type.

<a id="aea.configurations.data_types.PackageId.public_id"></a>

#### public`_`id

```python
@property
def public_id() -> PublicId
```

Get the public id.

<a id="aea.configurations.data_types.PackageId.author"></a>

#### author

```python
@property
def author() -> str
```

Get the author of the package.

<a id="aea.configurations.data_types.PackageId.name"></a>

#### name

```python
@property
def name() -> str
```

Get the name of the package.

<a id="aea.configurations.data_types.PackageId.version"></a>

#### version

```python
@property
def version() -> str
```

Get the version of the package.

<a id="aea.configurations.data_types.PackageId.package_hash"></a>

#### package`_`hash

```python
@property
def package_hash() -> str
```

Get the version of the package.

<a id="aea.configurations.data_types.PackageId.package_prefix"></a>

#### package`_`prefix

```python
@property
def package_prefix() -> Tuple[PackageType, str, str]
```

Get the package identifier without the version.

<a id="aea.configurations.data_types.PackageId.from_uri_path"></a>

#### from`_`uri`_`path

```python
@classmethod
def from_uri_path(cls, package_id_uri_path: str) -> "PackageId"
```

Initialize the package id from the string.

>>> str(PackageId.from_uri_path("skill/author/package_name/0.1.0"))
'(skill, author/package_name:0.1.0)'

A bad formatted input raises value error:
>>> PackageId.from_uri_path("very/bad/formatted:input")
Traceback (most recent call last):
...
ValueError: Input 'very/bad/formatted:input' is not well formatted.

**Arguments**:

- `package_id_uri_path`: the package id in uri path string format.

**Returns**:

the package id object.

**Raises**:

- `ValueError`: if the string in input is not well formatted.

<a id="aea.configurations.data_types.PackageId.to_uri_path"></a>

#### to`_`uri`_`path

```python
@property
def to_uri_path() -> str
```

Turn the package id into a uri path string.

**Returns**:

uri path string

<a id="aea.configurations.data_types.PackageId.without_hash"></a>

#### without`_`hash

```python
def without_hash() -> "PackageId"
```

Returns PackageId object without hash

<a id="aea.configurations.data_types.PackageId.with_hash"></a>

#### with`_`hash

```python
def with_hash(package_hash: str) -> "PackageId"
```

Returns PackageId object without hash

<a id="aea.configurations.data_types.PackageId.__hash__"></a>

#### `__`hash`__`

```python
def __hash__() -> int
```

Get the hash.

<a id="aea.configurations.data_types.PackageId.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="aea.configurations.data_types.PackageId.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Get the object representation in string.

<a id="aea.configurations.data_types.PackageId.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Compare with another object.

<a id="aea.configurations.data_types.PackageId.__lt__"></a>

#### `__`lt`__`

```python
def __lt__(other: Any) -> bool
```

Compare two public ids.

<a id="aea.configurations.data_types.ComponentId"></a>

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

<a id="aea.configurations.data_types.ComponentId.__init__"></a>

#### `__`init`__`

```python
def __init__(component_type: Union[ComponentType, str], public_id: PublicId) -> None
```

Initialize the component id.

**Arguments**:

- `component_type`: the component type.
- `public_id`: the public id.

<a id="aea.configurations.data_types.ComponentId.component_type"></a>

#### component`_`type

```python
@property
def component_type() -> ComponentType
```

Get the component type.

<a id="aea.configurations.data_types.ComponentId.component_prefix"></a>

#### component`_`prefix

```python
@property
def component_prefix() -> PackageIdPrefix
```

Get the component identifier without the version.

<a id="aea.configurations.data_types.ComponentId.same_prefix"></a>

#### same`_`prefix

```python
def same_prefix(other: "ComponentId") -> bool
```

Check if the other component id has the same type, author and name of this.

<a id="aea.configurations.data_types.ComponentId.prefix_import_path"></a>

#### prefix`_`import`_`path

```python
@property
def prefix_import_path() -> str
```

Get the prefix import path for this component.

<a id="aea.configurations.data_types.ComponentId.json"></a>

#### json

```python
@property
def json() -> Dict
```

Get the JSON representation.

<a id="aea.configurations.data_types.ComponentId.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, json_data: Dict) -> "ComponentId"
```

Create  component id from json data.

<a id="aea.configurations.data_types.ComponentId.without_hash"></a>

#### without`_`hash

```python
def without_hash() -> "ComponentId"
```

Returns PackageId object without hash

<a id="aea.configurations.data_types.PyPIPackageName"></a>

## PyPIPackageName Objects

```python
class PyPIPackageName(RegexConstrainedString)
```

A PyPI Package name.

<a id="aea.configurations.data_types.GitRef"></a>

## GitRef Objects

```python
class GitRef(RegexConstrainedString)
```

A Git reference.

It can be a branch name, a commit hash or a tag.

<a id="aea.configurations.data_types.Dependency"></a>

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

<a id="aea.configurations.data_types.Dependency.__init__"></a>

#### `__`init`__`

```python
def __init__(name: Union[PyPIPackageName, str], version: Union[str, SpecifierSet] = "", index: Optional[str] = None, git: Optional[str] = None, ref: Optional[Union[GitRef, str]] = None) -> None
```

Initialize a PyPI dependency.

**Arguments**:

- `name`: the package name.
- `version`: the specifier set object
- `index`: the URL to the PyPI server.
- `git`: the URL to a git repository.
- `ref`: the Git reference (branch/commit/tag).

<a id="aea.configurations.data_types.Dependency.name"></a>

#### name

```python
@property
def name() -> str
```

Get the name.

<a id="aea.configurations.data_types.Dependency.version"></a>

#### version

```python
@property
def version() -> str
```

Get the version.

<a id="aea.configurations.data_types.Dependency.index"></a>

#### index

```python
@property
def index() -> Optional[str]
```

Get the index.

<a id="aea.configurations.data_types.Dependency.git"></a>

#### git

```python
@property
def git() -> Optional[str]
```

Get the git.

<a id="aea.configurations.data_types.Dependency.ref"></a>

#### ref

```python
@property
def ref() -> Optional[str]
```

Get the ref.

<a id="aea.configurations.data_types.Dependency.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict[str, Dict[str, str]]) -> "Dependency"
```

Parse a dependency object from a dictionary.

<a id="aea.configurations.data_types.Dependency.to_json"></a>

#### to`_`json

```python
def to_json() -> Dict[str, Dict[str, str]]
```

Transform the object to JSON.

<a id="aea.configurations.data_types.Dependency.get_pip_install_args"></a>

#### get`_`pip`_`install`_`args

```python
def get_pip_install_args() -> List[str]
```

Get 'pip install' arguments.

<a id="aea.configurations.data_types.Dependency.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="aea.configurations.data_types.Dependency.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Compare with another object.

<a id="aea.configurations.data_types.Dependencies"></a>

#### Dependencies

A dictionary from package name to dependency data structure (see above).
The package name must satisfy  <a href="https://www.python.org/dev/peps/pep-0426/`name`">the constraints on Python packages names</a>.

The main advantage of having a dictionary is that we implicitly filter out dependency duplicates.
We cannot have two items with the same package name since the keys of a YAML object form a set.

<a id="aea.configurations.data_types.CRUDCollection"></a>

## CRUDCollection Objects

```python
class CRUDCollection(Generic[T])
```

Interface of a CRUD collection.

<a id="aea.configurations.data_types.CRUDCollection.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Instantiate a CRUD collection.

<a id="aea.configurations.data_types.CRUDCollection.create"></a>

#### create

```python
def create(item_id: str, item: T) -> None
```

Add an item.

**Arguments**:

- `item_id`: the item id.
- `item`: the item to be added.

**Raises**:

- `ValueError`: if the item with the same id is already in the collection.

<a id="aea.configurations.data_types.CRUDCollection.read"></a>

#### read

```python
def read(item_id: str) -> Optional[T]
```

Get an item by its name.

**Arguments**:

- `item_id`: the item id.

**Returns**:

the associated item, or None if the item id is not present.

<a id="aea.configurations.data_types.CRUDCollection.update"></a>

#### update

```python
def update(item_id: str, item: T) -> None
```

Update an existing item.

**Arguments**:

- `item_id`: the item id.
- `item`: the item to be added.

<a id="aea.configurations.data_types.CRUDCollection.delete"></a>

#### delete

```python
def delete(item_id: str) -> None
```

Delete an item.

<a id="aea.configurations.data_types.CRUDCollection.read_all"></a>

#### read`_`all

```python
def read_all() -> List[Tuple[str, T]]
```

Read all the items.

<a id="aea.configurations.data_types.CRUDCollection.keys"></a>

#### keys

```python
def keys() -> Set[str]
```

Get the set of keys.

