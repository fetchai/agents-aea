# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Classes to handle AEA configurations."""
import re
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union, cast


DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
DEFAULT_SKILL_CONFIG_FILE = "skill.yaml"
DEFAULT_CONNECTION_CONFIG_FILE = "connection.yaml"
DEFAULT_PROTOCOL_CONFIG_FILE = "protocol.yaml"
DEFAULT_PRIVATE_KEY_PATHS = {"fetchai": "", "ethereum": ""}
T = TypeVar("T")

"""
A dependency is a dictionary with the following (optional) keys:
    - version: a version specifier(s) (e.g. '==0.1.0').
    - index: the PyPI index where to download the package from (default: https://pypi.org)
    - git: the URL to the Git repository (e.g. https://github.com/fetchai/agents-aea.git)
    - ref: either the branch name, the tag, the commit number or a Git reference (default: 'master'.)
If the 'git' field is set, the 'version' field will be ignored.
They are supposed to be forwarded to the 'pip' command.
"""
Dependency = dict
"""
A dictionary from package name to dependency data structure (see above).
The package name must satisfy the constraints on Python packages names.
For details, see https://www.python.org/dev/peps/pep-0426/#name.

The main advantage of having a dictionary is that we implicitly filter out dependency duplicates.
We cannot have two items with the same package name since the keys of a YAML object form a set.
"""
Dependencies = Dict[str, Dependency]


# TODO rename this to "PackageType"
class ConfigurationType(Enum):
    """Configuration types."""

    AGENT = "agent"
    PROTOCOL = "protocol"
    CONNECTION = "connection"
    SKILL = "skill"
    CONTRACT = "contract"


def _get_default_configuration_file_name_from_type(
    item_type: Union[str, ConfigurationType]
) -> str:
    """Get the default configuration file name from item type."""
    item_type = ConfigurationType(item_type)
    if item_type == ConfigurationType.AGENT:
        return DEFAULT_AEA_CONFIG_FILE
    elif item_type == ConfigurationType.PROTOCOL:
        return DEFAULT_PROTOCOL_CONFIG_FILE
    elif item_type == ConfigurationType.CONNECTION:
        return DEFAULT_CONNECTION_CONFIG_FILE
    elif item_type == ConfigurationType.SKILL:
        return DEFAULT_SKILL_CONFIG_FILE
    else:
        raise ValueError(
            "Item type not valid: {}".format(str(item_type))
        )  # pragma: no cover


class ComponentType(Enum):
    PROTOCOL = "protocol"
    CONNECTION = "connection"
    SKILL = "skill"
    CONTRACT = "contract"

    def to_configuration_type(self) -> ConfigurationType:
        return ConfigurationType(self.value)


class ProtocolSpecificationParseError(Exception):
    """Exception for parsing a protocol specification file."""


class JSONSerializable(ABC):
    """Interface for JSON-serializable objects."""

    @property
    @abstractmethod
    def json(self) -> Dict:
        """Compute the JSON representation."""

    @classmethod
    def from_json(cls, obj: Dict):
        """Build from a JSON object."""


class Configuration(JSONSerializable, ABC):
    """Configuration class."""


class CRUDCollection(Generic[T]):
    """Interface of a CRUD collection."""

    def __init__(self):
        """Instantiate a CRUD collection."""
        self._items_by_id = {}  # type: Dict[str, T]

    def create(self, item_id: str, item: T) -> None:
        """
        Add an item.

        :param item_id: the item id.
        :param item: the item to be added.
        :return: None
        :raises ValueError: if the item with the same id is already in the collection.
        """
        if item_id in self._items_by_id:
            raise ValueError("Item with name {} already present!".format(item_id))
        else:
            self._items_by_id[item_id] = item

    def read(self, item_id: str) -> Optional[T]:
        """
        Get an item by its name.

        :param item_id: the item id.
        :return: the associated item, or None if the item id is not present.
        """
        return self._items_by_id.get(item_id, None)

    def update(self, item_id: str, item: T) -> None:
        """
        Update an existing item.

        :param item_id: the item id.
        :param item: the item to be added.
        :return: None
        """
        self._items_by_id[item_id] = item

    def delete(self, item_id: str) -> None:
        """Delete an item."""
        if item_id in self._items_by_id.keys():
            del self._items_by_id[item_id]

    def read_all(self) -> List[Tuple[str, T]]:
        """Read all the items."""
        return [(k, v) for k, v in self._items_by_id.items()]


class PublicId(JSONSerializable):
    """This class implement a public identifier.

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
    """

    AUTHOR_REGEX = r"[a-zA-Z_][a-zA-Z0-9_]*"
    PACKAGE_NAME_REGEX = r"[a-zA-Z_][a-zA-Z0-9_]*"
    VERSION_REGEX = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
    PUBLIC_ID_REGEX = r"^({})/({}):({})$".format(
        AUTHOR_REGEX, PACKAGE_NAME_REGEX, VERSION_REGEX
    )

    def __init__(self, author: str, name: str, version: str):
        """Initialize the public identifier."""
        self._author = author
        self._name = name
        self._version = version

    @property
    def author(self):
        """Get the author."""
        return self._author

    @property
    def name(self):
        """Get the name."""
        return self._name

    @property
    def version(self):
        """Get the version."""
        return self._version

    @classmethod
    def from_str(cls, public_id_string: str) -> "PublicId":
        """
        Initialize the public id from the string.

        >>> str(PublicId.from_str("author/package_name:0.1.0"))
        'author/package_name:0.1.0'

        A bad formatted input raises value error:
        >>> PublicId.from_str("bad/formatted:input")
        Traceback (most recent call last):
        ...
        ValueError: Input 'bad/formatted:input' is not well formatted.

        :param public_id_string: the public id in string format.
        :return: the public id object.
        :raises ValueError: if the string in input is not well formatted.
        """
        if not re.match(cls.PUBLIC_ID_REGEX, public_id_string):
            raise ValueError(
                "Input '{}' is not well formatted.".format(public_id_string)
            )
        else:
            username, package_name, version = re.findall(
                cls.PUBLIC_ID_REGEX, public_id_string
            )[0][:3]
            return PublicId(username, package_name, version)

    @property
    def json(self) -> Dict:
        """Compute the JSON representation."""
        return {"author": self.author, "name": self.name, "version": self.version}

    @classmethod
    def from_json(cls, obj: Dict):
        """Build from a JSON object."""
        return PublicId(obj["author"], obj["name"], obj["version"],)

    def __hash__(self):
        """Get the hash."""
        return hash((self.author, self.name, self.version))

    def __str__(self):
        """Get the string representation."""
        return "{author}/{name}:{version}".format(
            author=self.author, name=self.name, version=self.version
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, PublicId)
            and self.author == other.author
            and self.name == other.name
            and self.version == other.version
        )

    def __lt__(self, other):
        """Compare two public ids."""
        return str(self) < str(other)


class PackageId:
    """A component identifier."""

    def __init__(self, package_type: ConfigurationType, public_id: PublicId):
        """
        Initialize the package id.

        :param package_type: the package type.
        :param public_id: the public id.
        """
        self._package_type = package_type
        self._public_id = public_id

    @property
    def package_type(self) -> ConfigurationType:
        """Get the package type."""
        return self._package_type

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return self._public_id

    def __hash__(self):
        """Get the hash."""
        return hash((self.package_type, self.public_id))

    def __str__(self):
        """Get the string representation."""
        return "({package_type}, {public_id})".format(
            package_type=self.package_type.value, public_id=self.public_id,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, PackageId)
            and self.package_type == other.package_type
            and self.public_id == other.public_id
        )

    def __lt__(self, other):
        """Compare two public ids."""
        return str(self) < str(other)


class ComponentId(PackageId):
    """
    Class to represent a component identifier.

    A component id is a package id, but excludes the case when the package is an agent.
    >>> component_id = PackageId(ConfigurationType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    >>> component_id = ComponentId(ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    >>> component_id == component_id
    True

    >>> component_id2 = ComponentId(ComponentType.PROTOCOL, PublicId("author", "name", "0.1.1"))
    >>> component_id == component_id2
    False
    """

    def __init__(self, component_type: ComponentType, public_id: PublicId):
        """
        Initialize the component id.

        :param component_type: the component type.
        :param public_id: the public id.
        """
        super().__init__(component_type.to_configuration_type(), public_id)


ProtocolId = PublicId
SkillId = PublicId


class PackageConfiguration(Configuration, ABC):
    """
    This class represent a package configuration.

    A package can be one of:
    - agents
    - protocols
    - connections
    - skills
    - contracts
    """

    def __init__(
        self,
        name: str,
        author: str,
        version: str,
        license: str,
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
    ):
        """Initialize a package configuration."""
        self.name = name
        self.author = author
        self.version = version
        self.license = license
        self.fingerprint = fingerprint if fingerprint is not None else {}
        self.aea_version = aea_version

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return PublicId(self.author, self.name, self.version)

    @property
    @abstractmethod
    def default_configuration_filename(self) -> str:
        """Get the default configuration filename."""

    @property
    def package_dependencies(self) -> Set[ComponentId]:
        """Get the package dependencies."""
        return set()


class ComponentConfiguration(PackageConfiguration, ABC):
    """Class to represent an agent component configuration."""

    @staticmethod
    def load(
        component_type: ComponentType, directory: Path
    ) -> "ComponentConfiguration":
        """
        Load configuration.

        :param component_type: the component type.
        :param directory: the root of the package
        :return: the configuration object.
        """
        from aea.configurations.loader import ConfigLoader

        configuration_loader = ConfigLoader.from_configuration_type(
            component_type.to_configuration_type()
        )
        configuration_filename = (
            configuration_loader.configuration_class.default_configuration_filename
        )
        configuration_filepath = directory / configuration_filename
        configuration_object = configuration_loader.load(open(configuration_filepath))
        return configuration_object

    def check_fingerprint(self, directory: Path) -> None:
        """
        Check that the fingerprint are correct against a directory path.

        :raises ValueError if:
            - the argument is not a valid package directory
            - the fingerprint do not match.
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError("Directory {} is not valid.".format(directory))

        # TODO take from release/v0.3 branch.

    def check_aea_version(self):
        """
        Check that the AEA version matches the specifier set.

        :raises ValueError if the version of the aea framework falls within a specifier.
        """
        # TODO take from release/v0.3 branch, use 'packaging' package.


class ConnectionConfig(ComponentConfiguration):
    """Handle connection configuration."""

    def __init__(
        self,
        name: str = "",
        author: str = "",
        version: str = "",
        license: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        class_name: str = "",
        protocols: Optional[Set[PublicId]] = None,
        restricted_to_protocols: Optional[Set[PublicId]] = None,
        excluded_protocols: Optional[Set[PublicId]] = None,
        dependencies: Optional[Dependencies] = None,
        description: str = "",
        **config
    ):
        """Initialize a connection configuration object."""
        super().__init__(name, author, version, license, aea_version, fingerprint)
        self.class_name = class_name
        self.protocols = protocols if protocols is not None else []
        self.restricted_to_protocols = (
            restricted_to_protocols if restricted_to_protocols is not None else set()
        )
        self.excluded_protocols = (
            excluded_protocols if excluded_protocols is not None else set()
        )
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.config = config

    @property
    def default_configuration_filename(self):
        """Get the default configuration filename."""
        return DEFAULT_CONNECTION_CONFIG_FILE

    @property
    def package_dependencies(self) -> Set[PackageId]:
        """Get the connection dependencies."""
        return set(
            PackageId(ConfigurationType.PROTOCOL, protocol_id)
            for protocol_id in self.protocols
        )

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "aea_version": self.aea_version,
            "fingerprint": self.fingerprint,
            "class_name": self.class_name,
            "protocols": sorted(map(str, self.protocols)),
            "restricted_to_protocols": sorted(map(str, self.restricted_to_protocols)),
            "excluded_protocols": sorted(map(str, self.excluded_protocols)),
            "dependencies": self.dependencies,
            "description": self.description,
            "config": self.config,
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        restricted_to_protocols = obj.get("restricted_to_protocols", set())
        restricted_to_protocols = {
            PublicId.from_str(id_) for id_ in restricted_to_protocols
        }
        excluded_protocols = obj.get("excluded_protocols", set())
        excluded_protocols = {PublicId.from_str(id_) for id_ in excluded_protocols}
        dependencies = obj.get("dependencies", {})
        protocols = {PublicId.from_str(id_) for id_ in obj.get("protocols", set())}
        return ConnectionConfig(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            fingerprint=cast(Dict, obj.get("fingerprint")),
            class_name=cast(str, obj.get("class_name")),
            protocols=cast(Set[PublicId], protocols),
            restricted_to_protocols=cast(Set[PublicId], restricted_to_protocols),
            excluded_protocols=cast(Set[PublicId], excluded_protocols),
            dependencies=cast(Dependencies, dependencies),
            description=cast(str, obj.get("description", "")),
            **cast(dict, obj.get("config"))
        )


class ProtocolConfig(ComponentConfiguration):
    """Handle protocol configuration."""

    def __init__(
        self,
        name: str = "",
        author: str = "",
        version: str = "",
        license: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        dependencies: Optional[Dependencies] = None,
        description: str = "",
    ):
        """Initialize a connection configuration object."""
        super().__init__(name, author, version, license, aea_version, fingerprint)
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description

    @property
    def default_configuration_filename(self):
        """Get the default configuration filename."""
        return DEFAULT_PROTOCOL_CONFIG_FILE

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "aea_version": self.aea_version,
            "fingerprint": self.fingerprint,
            "dependencies": self.dependencies,
            "description": self.description,
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        dependencies = cast(Dependencies, obj.get("dependencies", {}))
        return ProtocolConfig(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            fingerprint=cast(Dict, obj.get("fingerprint")),
            dependencies=dependencies,
            description=cast(str, obj.get("description", "")),
        )


class HandlerConfig(Configuration):
    """Handle a skill handler configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a handler configuration."""
        self.class_name = class_name
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {"class_name": self.class_name, "args": self.args}

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        class_name = cast(str, obj.get("class_name"))
        return HandlerConfig(class_name=class_name, **obj.get("args", {}))


class BehaviourConfig(Configuration):
    """Handle a skill behaviour configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a behaviour configuration."""
        self.class_name = class_name
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {"class_name": self.class_name, "args": self.args}

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        class_name = cast(str, obj.get("class_name"))
        return BehaviourConfig(class_name=class_name, **obj.get("args", {}))


class ModelConfig(Configuration):
    """Handle a skill model configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a model configuration."""
        self.class_name = class_name
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {"class_name": self.class_name, "args": self.args}

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        class_name = cast(str, obj.get("class_name"))
        return ModelConfig(class_name=class_name, **obj.get("args", {}))


class SkillConfig(ComponentConfiguration):
    """Class to represent a skill configuration file."""

    def __init__(
        self,
        name: str = "",
        author: str = "",
        version: str = "",
        license: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        aea_version: str = "",
        protocols: List[PublicId] = None,
        dependencies: Optional[Dependencies] = None,
        description: str = "",
    ):
        """Initialize a skill configuration."""
        super().__init__(name, author, version, license, aea_version, fingerprint)
        self.protocols = (
            protocols if protocols is not None else []
        )  # type: List[PublicId]
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.handlers = CRUDCollection[HandlerConfig]()
        self.behaviours = CRUDCollection[BehaviourConfig]()
        self.models = CRUDCollection[ModelConfig]()

    @property
    def default_configuration_filename(self):
        """Get the default configuration filename."""
        return DEFAULT_SKILL_CONFIG_FILE

    @property
    def package_dependencies(self) -> Set[PackageId]:
        """Get the connection dependencies."""
        return {
            PackageId(ConfigurationType.PROTOCOL, protocol_id)
            for protocol_id in self.protocols
        }

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "aea_version": self.aea_version,
            "fingerprint": self.fingerprint,
            "protocols": sorted(map(str, self.protocols)),
            "dependencies": self.dependencies,
            "handlers": {key: h.json for key, h in self.handlers.read_all()},
            "behaviours": {key: b.json for key, b in self.behaviours.read_all()},
            "models": {key: m.json for key, m in self.models.read_all()},
            "description": self.description,
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        name = cast(str, obj.get("name"))
        author = cast(str, obj.get("author"))
        version = cast(str, obj.get("version"))
        license = cast(str, obj.get("license"))
        aea_version = cast(str, obj.get("aea_version", ""))
        fingerprint = cast(Dict[str, str], obj.get("fingerprint", {}))
        protocols = cast(
            List[PublicId],
            [PublicId.from_str(id_) for id_ in obj.get("protocols", [])],
        )
        dependencies = cast(Dependencies, obj.get("dependencies", {}))
        description = cast(str, obj.get("description", ""))
        skill_config = SkillConfig(
            name=name,
            author=author,
            version=version,
            license=license,
            aea_version=aea_version,
            fingerprint=fingerprint,
            protocols=protocols,
            dependencies=dependencies,
            description=description,
        )

        for behaviour_id, behaviour_data in obj.get("behaviours", {}).items():  # type: ignore
            behaviour_config = BehaviourConfig.from_json(behaviour_data)
            skill_config.behaviours.create(behaviour_id, behaviour_config)

        for handler_id, handler_data in obj.get("handlers", {}).items():  # type: ignore
            handler_config = HandlerConfig.from_json(handler_data)
            skill_config.handlers.create(handler_id, handler_config)

        for model_id, model_data in obj.get("models", {}).items():  # type: ignore
            model_config = ModelConfig.from_json(model_data)
            skill_config.models.create(model_id, model_config)

        return skill_config


class AgentConfig(PackageConfiguration):
    """Class to represent the agent configuration file."""

    def __init__(
        self,
        agent_name: str = "",
        aea_version: str = "",
        author: str = "",
        version: str = "",
        license: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        registry_path: str = "",
        description: str = "",
        logging_config: Optional[Dict] = None,
    ):
        """Instantiate the agent configuration object."""
        super().__init__(agent_name, author, version, license, aea_version, fingerprint)
        self.agent_name = agent_name
        self.registry_path = registry_path
        self.description = description
        self.private_key_paths = CRUDCollection[str]()
        self.ledger_apis = CRUDCollection[Dict]()

        self.logging_config = logging_config if logging_config is not None else {}
        self._default_ledger = None  # type: Optional[str]
        self._default_connection = None  # type: Optional[PublicId]
        self.connections = set()  # type: Set[PublicId]
        self.protocols = set()  # type: Set[PublicId]
        self.skills = set()  # type: Set[PublicId]

        if self.logging_config == {}:
            self.logging_config["version"] = 1
            self.logging_config["disable_existing_loggers"] = False

    @property
    def default_configuration_filename(self):
        """Get the default configuration filename."""
        return DEFAULT_AEA_CONFIG_FILE

    @property
    def package_dependencies(self) -> Set[PackageId]:
        """Get the package dependencies."""
        protocols = set(
            PackageId(ConfigurationType.PROTOCOL, public_id)
            for public_id in self.protocols
        )
        connections = set(
            PackageId(ConfigurationType.CONNECTION, public_id)
            for public_id in self.connections
        )
        skills = set(
            PackageId(ConfigurationType.CONNECTION, public_id)
            for public_id in self.skills
        )
        return set.union(protocols, connections, skills)

    @property
    def private_key_paths_dict(self) -> Dict[str, str]:
        """Dictionary version of private key paths."""
        return {key: path for key, path in self.private_key_paths.read_all()}

    @property
    def ledger_apis_dict(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """Dictionary version of ledger apis."""
        return {
            cast(str, key): cast(Dict[str, Union[str, int]], config)
            for key, config in self.ledger_apis.read_all()
        }

    @property
    def default_connection(self) -> str:
        """Get the default connection."""
        assert self._default_connection is not None, "Default connection not set yet."
        return str(self._default_connection)

    @default_connection.setter
    def default_connection(self, connection_id: Optional[Union[str, PublicId]]):
        """
        Set the default connection.

        :param connection_id: the name of the default connection.
        :return: None
        """
        if connection_id is None:
            self._default_connection = None
        elif isinstance(connection_id, str):
            self._default_connection = PublicId.from_str(connection_id)
        else:
            self._default_connection = connection_id

    @property
    def default_ledger(self) -> str:
        """Get the default ledger."""
        assert self._default_ledger is not None, "Default ledger not set yet."
        return self._default_ledger

    @default_ledger.setter
    def default_ledger(self, ledger_id: str):
        """
        Set the default ledger.

        :param ledger_id: the id of the default ledger.
        :return: None
        """
        self._default_ledger = ledger_id

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "agent_name": self.agent_name,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "aea_version": self.aea_version,
            "fingerprint": self.fingerprint,
            "registry_path": self.registry_path,
            "description": self.description,
            "private_key_paths": self.private_key_paths_dict,
            "ledger_apis": self.ledger_apis_dict,
            "logging_config": self.logging_config,
            "default_ledger": self.default_ledger,
            "default_connection": self.default_connection,
            "connections": sorted(map(str, self.connections)),
            "protocols": sorted(map(str, self.protocols)),
            "skills": sorted(map(str, self.skills)),
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        agent_config = AgentConfig(
            agent_name=cast(str, obj.get("agent_name")),
            aea_version=cast(str, obj.get("aea_version", "")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            fingerprint=cast(Dict, obj.get("fingerprint")),
            registry_path=cast(str, obj.get("registry_path")),
            description=cast(str, obj.get("description", "")),
            logging_config=cast(Dict, obj.get("logging_config", {})),
        )

        for crypto_id, path in obj.get("private_key_paths", {}).items():  # type: ignore
            agent_config.private_key_paths.create(crypto_id, path)

        for ledger_id, ledger_data in obj.get("ledger_apis", {}).items():  # type: ignore
            agent_config.ledger_apis.create(ledger_id, ledger_data)

        # parse connection public ids
        connections = set(
            map(lambda x: PublicId.from_str(x), obj.get("connections", []))
        )
        agent_config.connections = cast(Set[PublicId], connections)

        # parse protocol public ids
        protocols = set(map(lambda x: PublicId.from_str(x), obj.get("protocols", [])))
        agent_config.protocols = cast(Set[PublicId], protocols)

        # parse skills public ids
        skills = set(map(lambda x: PublicId.from_str(x), obj.get("skills", [])))
        agent_config.skills = cast(Set[PublicId], skills)

        # set default connection
        default_connection_name = obj.get("default_connection", None)
        agent_config.default_connection = default_connection_name
        default_ledger_id = obj.get("default_ledger", None)
        agent_config.default_ledger = default_ledger_id

        return agent_config


class SpeechActContentConfig(Configuration):
    """Handle a speech_act content configuration."""

    def __init__(self, **args):
        """Initialize a speech_act content configuration."""
        self.args = args  # type: Dict[str, str]
        self._check_consistency()

    def _check_consistency(self):
        """Check consistency of the args."""
        for content_name, content_type in self.args.items():
            if type(content_name) is not str or type(content_type) is not str:
                raise ProtocolSpecificationParseError(
                    "Contents' names and types must be string."
                )
            # Check each content definition key/value (i.e. content name/type) is not empty
            if content_name == "" or content_type == "":
                raise ProtocolSpecificationParseError(
                    "Contents' names and types cannot be empty."
                )

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return self.args

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        return SpeechActContentConfig(**obj)


class ProtocolSpecification(ProtocolConfig):
    """Handle protocol specification."""

    def __init__(
        self,
        name: str = "",
        author: str = "",
        version: str = "",
        license: str = "",
        aea_version: str = "",
        fingerprint: Optional[Dict[str, str]] = None,
        description: str = "",
    ):
        """Initialize a protocol specification configuration object."""
        super().__init__(
            name,
            author,
            version,
            license,
            aea_version,
            fingerprint,
            description=description,
        )
        self.speech_acts = CRUDCollection[SpeechActContentConfig]()
        self._protobuf_snippets = None  # type: Optional[Dict]

    @property
    def protobuf_snippets(self) -> Optional[Dict]:
        """Get the protobuf snippets."""
        return self._protobuf_snippets

    @protobuf_snippets.setter
    def protobuf_snippets(self, protobuf_snippets: Optional[Dict]):
        """Set the protobuf snippets."""
        self._protobuf_snippets = protobuf_snippets

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "aea_version": self.aea_version,
            "fingerprint": self.fingerprint,
            "description": self.description,
            "speech_acts": {
                key: speech_act.json for key, speech_act in self.speech_acts.read_all()
            },
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        protocol_specification = ProtocolSpecification(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version", "")),
            fingerprint=cast(Dict, obj.get("fingerprint")),
            description=cast(str, obj.get("description", "")),
        )
        for speech_act, speech_act_content in obj.get("speech_acts", {}).items():  # type: ignore
            speech_act_content_config = SpeechActContentConfig.from_json(
                speech_act_content
            )
            protocol_specification.speech_acts.create(
                speech_act, speech_act_content_config
            )
        protocol_specification._check_consistency()
        return protocol_specification

    def _check_consistency(self):
        """Validate the correctness of the speech_acts."""
        if len(self.speech_acts.read_all()) == 0:
            raise ProtocolSpecificationParseError(
                "There should be at least one performative defined in the speech_acts."
            )
        content_dict = {}
        for performative, speech_act_content_config in self.speech_acts.read_all():
            if type(performative) is not str:
                raise ProtocolSpecificationParseError(
                    "A 'performative' is not specified as a string."
                )
            if performative == "":
                raise ProtocolSpecificationParseError(
                    "A 'performative' cannot be an empty string."
                )
            for content_name, content_type in speech_act_content_config.args.items():
                if content_name in content_dict.keys():
                    if content_type != content_dict[content_name]:  # pragma: no cover
                        raise ProtocolSpecificationParseError(
                            "The content '{}' appears more than once with different types in speech_acts.".format(
                                content_name
                            )
                        )
                content_dict[content_name] = content_type
