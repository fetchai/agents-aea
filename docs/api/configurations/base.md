<a name=".aea.configurations.base"></a>
## aea.configurations.base

Classes to handle AEA configurations.

<a name=".aea.configurations.base.Dependency"></a>
#### Dependency

A dependency is a dictionary with the following (optional) keys:
    - version: a version specifier(s) (e.g. '==0.1.0').
    - index: the PyPI index where to download the package from (default: https://pypi.org)
    - git: the URL to the Git repository (e.g. https://github.com/fetchai/agents-aea.git)
    - ref: either the branch name, the tag, the commit number or a Git reference (default: 'master'.)
If the 'git' field is set, the 'version' field will be ignored.
They are supposed to be forwarded to the 'pip' command.

<a name=".aea.configurations.base.Dependencies"></a>
#### Dependencies

A dictionary from package name to dependency data structure (see above).
The package name must satisfy the constraints on Python packages names.
For details, see https://www.python.org/dev/peps/pep-0426/`name`.

The main advantage of having a dictionary is that we implicitly filter out dependency duplicates.
We cannot have two items with the same package name since the keys of a YAML object form a set.

<a name=".aea.configurations.base.ConfigurationType"></a>
### ConfigurationType

```python
class ConfigurationType(Enum)
```

Configuration types.

<a name=".aea.configurations.base.ProtocolSpecificationParseError"></a>
### ProtocolSpecificationParseError

```python
class ProtocolSpecificationParseError(Exception)
```

Exception for parsing a protocol specification file.

<a name=".aea.configurations.base.JSONSerializable"></a>
### JSONSerializable

```python
class JSONSerializable(ABC)
```

Interface for JSON-serializable objects.

<a name=".aea.configurations.base.JSONSerializable.json"></a>
#### json

```python
 | @property
 | @abstractmethod
 | json() -> Dict
```

Compute the JSON representation.

<a name=".aea.configurations.base.JSONSerializable.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Build from a JSON object.

<a name=".aea.configurations.base.Configuration"></a>
### Configuration

```python
class Configuration(JSONSerializable,  ABC)
```

Configuration class.

<a name=".aea.configurations.base.CRUDCollection"></a>
### CRUDCollection

```python
class CRUDCollection(Generic[T])
```

Interface of a CRUD collection.

<a name=".aea.configurations.base.CRUDCollection.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate a CRUD collection.

<a name=".aea.configurations.base.CRUDCollection.create"></a>
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

<a name=".aea.configurations.base.CRUDCollection.read"></a>
#### read

```python
 | read(item_id: str) -> Optional[T]
```

Get an item by its name.

**Arguments**:

- `item_id`: the item id.

**Returns**:

the associated item, or None if the item id is not present.

<a name=".aea.configurations.base.CRUDCollection.update"></a>
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

<a name=".aea.configurations.base.CRUDCollection.delete"></a>
#### delete

```python
 | delete(item_id: str) -> None
```

Delete an item.

<a name=".aea.configurations.base.CRUDCollection.read_all"></a>
#### read`_`all

```python
 | read_all() -> List[Tuple[str, T]]
```

Read all the items.

<a name=".aea.configurations.base.PublicId"></a>
### PublicId

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

<a name=".aea.configurations.base.PublicId.__init__"></a>
#### `__`init`__`

```python
 | __init__(author: str, name: str, version: str)
```

Initialize the public identifier.

<a name=".aea.configurations.base.PublicId.author"></a>
#### author

```python
 | @property
 | author()
```

Get the author.

<a name=".aea.configurations.base.PublicId.name"></a>
#### name

```python
 | @property
 | name()
```

Get the name.

<a name=".aea.configurations.base.PublicId.version"></a>
#### version

```python
 | @property
 | version()
```

Get the version.

<a name=".aea.configurations.base.PublicId.from_str"></a>
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

<a name=".aea.configurations.base.PublicId.from_uri_path"></a>
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

<a name=".aea.configurations.base.PublicId.to_uri_path"></a>
#### to`_`uri`_`path

```python
 | @property
 | to_uri_path() -> str
```

Turn the public id into a uri path string.

**Returns**:

uri path string

<a name=".aea.configurations.base.PublicId.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Compute the JSON representation.

<a name=".aea.configurations.base.PublicId.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Build from a JSON object.

<a name=".aea.configurations.base.PublicId.__hash__"></a>
#### `__`hash`__`

```python
 | __hash__()
```

Get the hash.

<a name=".aea.configurations.base.PublicId.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name=".aea.configurations.base.PublicId.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.configurations.base.PublicId.__lt__"></a>
#### `__`lt`__`

```python
 | __lt__(other)
```

Compare two public ids.

<a name=".aea.configurations.base.PackageConfiguration"></a>
### PackageConfiguration

```python
class PackageConfiguration(Configuration,  ABC)
```

This class represent a package configuration.

<a name=".aea.configurations.base.PackageConfiguration.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, author: str, version: str, license: str, aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None)
```

Initialize a package configuration.

<a name=".aea.configurations.base.PackageConfiguration.public_id"></a>
#### public`_`id

```python
 | @property
 | public_id() -> PublicId
```

Get the public id.

<a name=".aea.configurations.base.ConnectionConfig"></a>
### ConnectionConfig

```python
class ConnectionConfig(PackageConfiguration)
```

Handle connection configuration.

<a name=".aea.configurations.base.ConnectionConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str = "", author: str = "", version: str = "", license: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, class_name: str = "", protocols: Optional[Set[PublicId]] = None, restricted_to_protocols: Optional[Set[PublicId]] = None, excluded_protocols: Optional[Set[PublicId]] = None, dependencies: Optional[Dependencies] = None, description: str = "", **config)
```

Initialize a connection configuration object.

<a name=".aea.configurations.base.ConnectionConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.ConnectionConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name=".aea.configurations.base.ProtocolConfig"></a>
### ProtocolConfig

```python
class ProtocolConfig(PackageConfiguration)
```

Handle protocol configuration.

<a name=".aea.configurations.base.ProtocolConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str = "", author: str = "", version: str = "", license: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, dependencies: Optional[Dependencies] = None, description: str = "")
```

Initialize a connection configuration object.

<a name=".aea.configurations.base.ProtocolConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.ProtocolConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name=".aea.configurations.base.HandlerConfig"></a>
### HandlerConfig

```python
class HandlerConfig(Configuration)
```

Handle a skill handler configuration.

<a name=".aea.configurations.base.HandlerConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(class_name: str = "", **args)
```

Initialize a handler configuration.

<a name=".aea.configurations.base.HandlerConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.HandlerConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name=".aea.configurations.base.BehaviourConfig"></a>
### BehaviourConfig

```python
class BehaviourConfig(Configuration)
```

Handle a skill behaviour configuration.

<a name=".aea.configurations.base.BehaviourConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(class_name: str = "", **args)
```

Initialize a behaviour configuration.

<a name=".aea.configurations.base.BehaviourConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.BehaviourConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name=".aea.configurations.base.ModelConfig"></a>
### ModelConfig

```python
class ModelConfig(Configuration)
```

Handle a skill model configuration.

<a name=".aea.configurations.base.ModelConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(class_name: str = "", **args)
```

Initialize a model configuration.

<a name=".aea.configurations.base.ModelConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.ModelConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name=".aea.configurations.base.SkillConfig"></a>
### SkillConfig

```python
class SkillConfig(PackageConfiguration)
```

Class to represent a skill configuration file.

<a name=".aea.configurations.base.SkillConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str = "", author: str = "", version: str = "", license: str = "", fingerprint: Optional[Dict[str, str]] = None, aea_version: str = "", protocols: List[PublicId] = None, dependencies: Optional[Dependencies] = None, description: str = "")
```

Initialize a skill configuration.

<a name=".aea.configurations.base.SkillConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.SkillConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name=".aea.configurations.base.AgentConfig"></a>
### AgentConfig

```python
class AgentConfig(PackageConfiguration)
```

Class to represent the agent configuration file.

<a name=".aea.configurations.base.AgentConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_name: str = "", aea_version: str = "", author: str = "", version: str = "", license: str = "", fingerprint: Optional[Dict[str, str]] = None, registry_path: str = "", description: str = "", logging_config: Optional[Dict] = None)
```

Instantiate the agent configuration object.

<a name=".aea.configurations.base.AgentConfig.private_key_paths_dict"></a>
#### private`_`key`_`paths`_`dict

```python
 | @property
 | private_key_paths_dict() -> Dict[str, str]
```

Dictionary version of private key paths.

<a name=".aea.configurations.base.AgentConfig.ledger_apis_dict"></a>
#### ledger`_`apis`_`dict

```python
 | @property
 | ledger_apis_dict() -> Dict[str, Dict[str, Union[str, int]]]
```

Dictionary version of ledger apis.

<a name=".aea.configurations.base.AgentConfig.default_connection"></a>
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

<a name=".aea.configurations.base.AgentConfig.default_ledger"></a>
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

<a name=".aea.configurations.base.AgentConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.AgentConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name=".aea.configurations.base.SpeechActContentConfig"></a>
### SpeechActContentConfig

```python
class SpeechActContentConfig(Configuration)
```

Handle a speech_act content configuration.

<a name=".aea.configurations.base.SpeechActContentConfig.__init__"></a>
#### `__`init`__`

```python
 | __init__(**args)
```

Initialize a speech_act content configuration.

<a name=".aea.configurations.base.SpeechActContentConfig.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.SpeechActContentConfig.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

<a name=".aea.configurations.base.ProtocolSpecification"></a>
### ProtocolSpecification

```python
class ProtocolSpecification(ProtocolConfig)
```

Handle protocol specification.

<a name=".aea.configurations.base.ProtocolSpecification.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str = "", author: str = "", version: str = "", license: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, description: str = "")
```

Initialize a protocol specification configuration object.

<a name=".aea.configurations.base.ProtocolSpecification.protobuf_snippets"></a>
#### protobuf`_`snippets

```python
 | @protobuf_snippets.setter
 | protobuf_snippets(protobuf_snippets: Optional[Dict])
```

Set the protobuf snippets.

<a name=".aea.configurations.base.ProtocolSpecification.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.configurations.base.ProtocolSpecification.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict)
```

Initialize from a JSON object.

