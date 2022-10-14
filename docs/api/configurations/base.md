<a id="aea.configurations.base"></a>

# aea.configurations.base

Classes to handle AEA configurations.

<a id="aea.configurations.base.dependencies_from_json"></a>

#### dependencies`_`from`_`json

```python
def dependencies_from_json(obj: Dict[str, Dict]) -> Dependencies
```

Parse a JSON object to get an instance of Dependencies.

**Arguments**:

- `obj`: a dictionary whose keys are package names and values are dictionary with package specifications.

**Returns**:

a Dependencies object.

<a id="aea.configurations.base.dependencies_to_json"></a>

#### dependencies`_`to`_`json

```python
def dependencies_to_json(dependencies: Dependencies) -> Dict[str, Dict]
```

Transform a Dependencies object into a JSON object.

**Arguments**:

- `dependencies`: an instance of "Dependencies" type.

**Returns**:

a dictionary whose keys are package names and

<a id="aea.configurations.base.ProtocolSpecificationParseError"></a>

## ProtocolSpecificationParseError Objects

```python
class ProtocolSpecificationParseError(Exception)
```

Exception for parsing a protocol specification file.

<a id="aea.configurations.base.Configuration"></a>

## Configuration Objects

```python
class Configuration(JSONSerializable,  ABC)
```

Configuration class.

<a id="aea.configurations.base.Configuration.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize a configuration object.

<a id="aea.configurations.base.Configuration.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "Configuration"
```

Build from a JSON object.

<a id="aea.configurations.base.Configuration.ordered_json"></a>

#### ordered`_`json

```python
@property
def ordered_json() -> OrderedDict
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

<a id="aea.configurations.base.PackageConfiguration"></a>

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

<a id="aea.configurations.base.PackageConfiguration.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr, author: SimpleIdOrStr, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, build_entrypoint: Optional[str] = None) -> None
```

Initialize a package configuration.

**Arguments**:

- `name`: the name of the package.
- `author`: the author of the package.
- `version`: the version of the package (SemVer format).
- `license_`: the license.
- `aea_version`: either a fixed version, or a set of specifiers describing the AEA versions allowed. (default: empty string - no constraint). The fixed version is interpreted with the specifier '=='.
- `fingerprint`: the fingerprint.
- `fingerprint_ignore_patterns`: a list of file patterns to ignore files to fingerprint.
- `build_entrypoint`: path to a script to execute at build time.

<a id="aea.configurations.base.PackageConfiguration.name"></a>

#### name

```python
@property
def name() -> str
```

Get the name.

<a id="aea.configurations.base.PackageConfiguration.name"></a>

#### name

```python
@name.setter
def name(value: SimpleIdOrStr) -> None
```

Set the name.

<a id="aea.configurations.base.PackageConfiguration.author"></a>

#### author

```python
@property
def author() -> str
```

Get the author.

<a id="aea.configurations.base.PackageConfiguration.author"></a>

#### author

```python
@author.setter
def author(value: SimpleIdOrStr) -> None
```

Set the author.

<a id="aea.configurations.base.PackageConfiguration.aea_version"></a>

#### aea`_`version

```python
@property
def aea_version() -> str
```

Get the 'aea_version' attribute.

<a id="aea.configurations.base.PackageConfiguration.aea_version"></a>

#### aea`_`version

```python
@aea_version.setter
def aea_version(new_aea_version: str) -> None
```

Set the 'aea_version' attribute.

<a id="aea.configurations.base.PackageConfiguration.check_aea_version"></a>

#### check`_`aea`_`version

```python
def check_aea_version() -> None
```

Check that the AEA version matches the specifier set.

<a id="aea.configurations.base.PackageConfiguration.directory"></a>

#### directory

```python
@property
def directory() -> Optional[Path]
```

Get the path to the configuration file associated to this file, if any.

<a id="aea.configurations.base.PackageConfiguration.directory"></a>

#### directory

```python
@directory.setter
def directory(directory: Path) -> None
```

Set directory if not already set.

<a id="aea.configurations.base.PackageConfiguration.package_id"></a>

#### package`_`id

```python
@property
def package_id() -> PackageId
```

Get package id.

<a id="aea.configurations.base.PackageConfiguration.parse_aea_version_specifier"></a>

#### parse`_`aea`_`version`_`specifier

```python
@staticmethod
def parse_aea_version_specifier(aea_version_specifiers: str) -> SpecifierSet
```

Parse an 'aea_version' field.

If 'aea_version' is a version, then output the specifier set "==${version}"
Else, interpret it as specifier set.

**Arguments**:

- `aea_version_specifiers`: the AEA version, or a specifier set.

**Returns**:

A specifier set object.

<a id="aea.configurations.base.PackageConfiguration.aea_version_specifiers"></a>

#### aea`_`version`_`specifiers

```python
@property
def aea_version_specifiers() -> SpecifierSet
```

Get the AEA version set specifier.

<a id="aea.configurations.base.PackageConfiguration.public_id"></a>

#### public`_`id

```python
@property
def public_id() -> PublicId
```

Get the public id.

<a id="aea.configurations.base.PackageConfiguration.package_dependencies"></a>

#### package`_`dependencies

```python
@property
def package_dependencies() -> Set[ComponentId]
```

Get the package dependencies.

<a id="aea.configurations.base.PackageConfiguration.update"></a>

#### update

```python
def update(data: Dict, env_vars_friendly: bool = False) -> None
```

Update configuration with other data.

**Arguments**:

- `data`: the data to replace.
- `env_vars_friendly`: whether or not it is env vars friendly.

<a id="aea.configurations.base.PackageConfiguration.validate_config_data"></a>

#### validate`_`config`_`data

```python
@classmethod
def validate_config_data(cls, json_data: Dict, env_vars_friendly: bool = False) -> None
```

Perform config validation.

<a id="aea.configurations.base.PackageConfiguration.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "PackageConfiguration"
```

Initialize from a JSON object.

<a id="aea.configurations.base.PackageConfiguration.make_resulting_config_data"></a>

#### make`_`resulting`_`config`_`data

```python
def make_resulting_config_data(overrides: Dict) -> Dict
```

Make config data with overrides applied.

Does not update config, just creates json representation.

**Arguments**:

- `overrides`: the overrides

**Returns**:

config with overrides applied

<a id="aea.configurations.base.PackageConfiguration.check_overrides_valid"></a>

#### check`_`overrides`_`valid

```python
def check_overrides_valid(overrides: Dict, env_vars_friendly: bool = False) -> None
```

Check overrides is correct, return list of errors if present.

<a id="aea.configurations.base.PackageConfiguration.get_overridable"></a>

#### get`_`overridable

```python
def get_overridable() -> dict
```

Get dictionary of values that can be updated for this config.

<a id="aea.configurations.base.ComponentConfiguration"></a>

## ComponentConfiguration Objects

```python
class ComponentConfiguration(PackageConfiguration,  ABC)
```

Class to represent an agent component configuration.

<a id="aea.configurations.base.ComponentConfiguration.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr, author: SimpleIdOrStr, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, build_entrypoint: Optional[str] = None, build_directory: Optional[str] = None, dependencies: Optional[Dependencies] = None) -> None
```

Set component configuration.

<a id="aea.configurations.base.ComponentConfiguration.build_directory"></a>

#### build`_`directory

```python
@property
def build_directory() -> Optional[str]
```

Get the component type.

<a id="aea.configurations.base.ComponentConfiguration.build_directory"></a>

#### build`_`directory

```python
@build_directory.setter
def build_directory(value: Optional[str]) -> None
```

Get the component type.

<a id="aea.configurations.base.ComponentConfiguration.component_type"></a>

#### component`_`type

```python
@property
def component_type() -> ComponentType
```

Get the component type.

<a id="aea.configurations.base.ComponentConfiguration.component_id"></a>

#### component`_`id

```python
@property
def component_id() -> ComponentId
```

Get the component id.

<a id="aea.configurations.base.ComponentConfiguration.prefix_import_path"></a>

#### prefix`_`import`_`path

```python
@property
def prefix_import_path() -> str
```

Get the prefix import path for this component.

<a id="aea.configurations.base.ComponentConfiguration.is_abstract_component"></a>

#### is`_`abstract`_`component

```python
@property
def is_abstract_component() -> bool
```

Check whether the component is abstract.

<a id="aea.configurations.base.ComponentConfiguration.check_fingerprint"></a>

#### check`_`fingerprint

```python
def check_fingerprint(directory: Path) -> None
```

Check that the fingerprint are correct against a directory path.

**Arguments**:

- `directory`: the directory path.

**Raises**:

- `ValueError`: if
    - the argument is not a valid package directory
    - the fingerprints do not match.

<a id="aea.configurations.base.ComponentConfiguration.check_public_id_consistency"></a>

#### check`_`public`_`id`_`consistency

```python
def check_public_id_consistency(directory: Path) -> None
```

Check that the public ids in the init file match the config.

**Arguments**:

- `directory`: the directory path.

**Raises**:

- `ValueError`: if
    - the argument is not a valid package directory
    - the public ids do not match.

<a id="aea.configurations.base.ConnectionConfig"></a>

## ConnectionConfig Objects

```python
class ConnectionConfig(ComponentConfiguration)
```

Handle connection configuration.

<a id="aea.configurations.base.ConnectionConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr = "", author: SimpleIdOrStr = "", version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, build_entrypoint: Optional[str] = None, build_directory: Optional[str] = None, class_name: str = "", protocols: Optional[Set[PublicId]] = None, connections: Optional[Set[PublicId]] = None, restricted_to_protocols: Optional[Set[PublicId]] = None, excluded_protocols: Optional[Set[PublicId]] = None, dependencies: Optional[Dependencies] = None, description: str = "", connection_id: Optional[PublicId] = None, is_abstract: bool = False, cert_requests: Optional[List[CertRequest]] = None, **config: Any, ,) -> None
```

Initialize a connection configuration object.

<a id="aea.configurations.base.ConnectionConfig.package_dependencies"></a>

#### package`_`dependencies

```python
@property
def package_dependencies() -> Set[ComponentId]
```

Get the connection dependencies.

<a id="aea.configurations.base.ConnectionConfig.is_abstract_component"></a>

#### is`_`abstract`_`component

```python
@property
def is_abstract_component() -> bool
```

Check whether the component is abstract.

<a id="aea.configurations.base.ConnectionConfig.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.configurations.base.ProtocolConfig"></a>

## ProtocolConfig Objects

```python
class ProtocolConfig(ComponentConfiguration)
```

Handle protocol configuration.

<a id="aea.configurations.base.ProtocolConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr, author: SimpleIdOrStr, version: str = "", license_: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, build_entrypoint: Optional[str] = None, build_directory: Optional[str] = None, aea_version: str = "", dependencies: Optional[Dependencies] = None, description: str = "", protocol_specification_id: Optional[str] = None) -> None
```

Initialize a connection configuration object.

<a id="aea.configurations.base.ProtocolConfig.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.configurations.base.SkillComponentConfiguration"></a>

## SkillComponentConfiguration Objects

```python
class SkillComponentConfiguration()
```

This class represent a skill component configuration.

<a id="aea.configurations.base.SkillComponentConfiguration.__init__"></a>

#### `__`init`__`

```python
def __init__(class_name: str, file_path: Optional[str] = None, **args: Any) -> None
```

Initialize a skill component configuration.

**Arguments**:

- `class_name`: the class name of the component.
- `file_path`: the file path.
- `args`: keyword arguments.

<a id="aea.configurations.base.SkillComponentConfiguration.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.configurations.base.SkillComponentConfiguration.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "SkillComponentConfiguration"
```

Initialize from a JSON object.

<a id="aea.configurations.base.SkillConfig"></a>

## SkillConfig Objects

```python
class SkillConfig(ComponentConfiguration)
```

Class to represent a skill configuration file.

<a id="aea.configurations.base.SkillConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr, author: SimpleIdOrStr, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, build_entrypoint: Optional[str] = None, build_directory: Optional[str] = None, connections: Optional[Set[PublicId]] = None, protocols: Optional[Set[PublicId]] = None, contracts: Optional[Set[PublicId]] = None, skills: Optional[Set[PublicId]] = None, dependencies: Optional[Dependencies] = None, description: str = "", is_abstract: bool = False) -> None
```

Initialize a skill configuration.

<a id="aea.configurations.base.SkillConfig.package_dependencies"></a>

#### package`_`dependencies

```python
@property
def package_dependencies() -> Set[ComponentId]
```

Get the skill dependencies.

<a id="aea.configurations.base.SkillConfig.is_abstract_component"></a>

#### is`_`abstract`_`component

```python
@property
def is_abstract_component() -> bool
```

Check whether the component is abstract.

<a id="aea.configurations.base.SkillConfig.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.configurations.base.SkillConfig.get_overridable"></a>

#### get`_`overridable

```python
def get_overridable() -> dict
```

Get overridable configuration data.

<a id="aea.configurations.base.AgentConfig"></a>

## AgentConfig Objects

```python
class AgentConfig(PackageConfiguration)
```

Class to represent the agent configuration file.

<a id="aea.configurations.base.AgentConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(agent_name: SimpleIdOrStr, author: SimpleIdOrStr, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, build_entrypoint: Optional[str] = None, description: str = "", logging_config: Optional[Dict] = None, period: Optional[float] = None, execution_timeout: Optional[float] = None, max_reactions: Optional[int] = None, error_handler: Optional[Dict] = None, decision_maker_handler: Optional[Dict] = None, skill_exception_policy: Optional[str] = None, connection_exception_policy: Optional[str] = None, default_ledger: Optional[str] = None, required_ledgers: Optional[List[str]] = None, currency_denominations: Optional[Dict[str, str]] = None, default_connection: Optional[str] = None, default_routing: Optional[Dict[str, str]] = None, loop_mode: Optional[str] = None, runtime_mode: Optional[str] = None, task_manager_mode: Optional[str] = None, storage_uri: Optional[str] = None, data_dir: Optional[str] = None, component_configurations: Optional[Dict[ComponentId, Dict]] = None, dependencies: Optional[Dependencies] = None) -> None
```

Instantiate the agent configuration object.

<a id="aea.configurations.base.AgentConfig.component_configurations"></a>

#### component`_`configurations

```python
@property
def component_configurations() -> Dict[ComponentId, Dict]
```

Get the custom component configurations.

<a id="aea.configurations.base.AgentConfig.component_configurations"></a>

#### component`_`configurations

```python
@component_configurations.setter
def component_configurations(d: Dict[ComponentId, Dict]) -> None
```

Set the component configurations.

<a id="aea.configurations.base.AgentConfig.package_dependencies"></a>

#### package`_`dependencies

```python
@property
def package_dependencies() -> Set[ComponentId]
```

Get the package dependencies.

<a id="aea.configurations.base.AgentConfig.private_key_paths_dict"></a>

#### private`_`key`_`paths`_`dict

```python
@property
def private_key_paths_dict() -> Dict[str, str]
```

Get dictionary version of private key paths.

<a id="aea.configurations.base.AgentConfig.connection_private_key_paths_dict"></a>

#### connection`_`private`_`key`_`paths`_`dict

```python
@property
def connection_private_key_paths_dict() -> Dict[str, str]
```

Get dictionary version of connection private key paths.

<a id="aea.configurations.base.AgentConfig.component_configurations_json"></a>

#### component`_`configurations`_`json

```python
def component_configurations_json() -> List[OrderedDict]
```

Get the component configurations in JSON format.

<a id="aea.configurations.base.AgentConfig.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.configurations.base.AgentConfig.all_components_id"></a>

#### all`_`components`_`id

```python
@property
def all_components_id() -> List[ComponentId]
```

Get list of the all components for this agent config.

<a id="aea.configurations.base.AgentConfig.update"></a>

#### update

```python
def update(data: Dict, env_vars_friendly: bool = False, dict_overrides: Optional[Dict] = None) -> None
```

Update configuration with other data.

To update the component parts, populate the field "component_configurations" as a
mapping from ComponentId to configurations.

**Arguments**:

- `data`: the data to replace.
- `env_vars_friendly`: whether or not it is env vars friendly.
- `dict_overrides`: A dictionary containing mapping for Component ID -> List of paths

<a id="aea.configurations.base.SpeechActContentConfig"></a>

## SpeechActContentConfig Objects

```python
class SpeechActContentConfig(Configuration)
```

Handle a speech_act content configuration.

<a id="aea.configurations.base.SpeechActContentConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(**args: Any) -> None
```

Initialize a speech_act content configuration.

<a id="aea.configurations.base.SpeechActContentConfig.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.configurations.base.SpeechActContentConfig.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict) -> "SpeechActContentConfig"
```

Initialize from a JSON object.

<a id="aea.configurations.base.ProtocolSpecification"></a>

## ProtocolSpecification Objects

```python
class ProtocolSpecification(ProtocolConfig)
```

Handle protocol specification.

<a id="aea.configurations.base.ProtocolSpecification.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr, author: SimpleIdOrStr, version: str = "", license_: str = "", aea_version: str = "", description: str = "", protocol_specification_id: Optional[str] = None) -> None
```

Initialize a protocol specification configuration object.

<a id="aea.configurations.base.ProtocolSpecification.protobuf_snippets"></a>

#### protobuf`_`snippets

```python
@property
def protobuf_snippets() -> Dict
```

Get the protobuf snippets.

<a id="aea.configurations.base.ProtocolSpecification.protobuf_snippets"></a>

#### protobuf`_`snippets

```python
@protobuf_snippets.setter
def protobuf_snippets(protobuf_snippets: Dict) -> None
```

Set the protobuf snippets.

<a id="aea.configurations.base.ProtocolSpecification.dialogue_config"></a>

#### dialogue`_`config

```python
@property
def dialogue_config() -> Dict
```

Get the dialogue config.

<a id="aea.configurations.base.ProtocolSpecification.dialogue_config"></a>

#### dialogue`_`config

```python
@dialogue_config.setter
def dialogue_config(dialogue_config: Dict) -> None
```

Set the dialogue config.

<a id="aea.configurations.base.ProtocolSpecification.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.configurations.base.ContractConfig"></a>

## ContractConfig Objects

```python
class ContractConfig(ComponentConfiguration)
```

Handle contract configuration.

<a id="aea.configurations.base.ContractConfig.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr, author: SimpleIdOrStr, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, build_entrypoint: Optional[str] = None, build_directory: Optional[str] = None, dependencies: Optional[Dependencies] = None, description: str = "", contract_interface_paths: Optional[Dict[str, str]] = None, class_name: str = "", contracts: Optional[Set[PublicId]] = None) -> None
```

Initialize a protocol configuration object.

<a id="aea.configurations.base.ContractConfig.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.configurations.base.ContractConfig.package_dependencies"></a>

#### package`_`dependencies

```python
@property
def package_dependencies() -> Set[ComponentId]
```

Get the contract dependencies.

<a id="aea.configurations.base.AEAVersionError"></a>

## AEAVersionError Objects

```python
class AEAVersionError(ValueError)
```

Special Exception for version error.

<a id="aea.configurations.base.AEAVersionError.__init__"></a>

#### `__`init`__`

```python
def __init__(package_id: PublicId, aea_version_specifiers: SpecifierSet) -> None
```

Init exception.

