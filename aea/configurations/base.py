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
from typing import TypeVar, Generic, Optional, List, Tuple, Dict, Set, cast
# from aea.helpers.base import generate_fingerprint

DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
DEFAULT_SKILL_CONFIG_FILE = "skill.yaml"
DEFAULT_CONNECTION_CONFIG_FILE = 'connection.yaml'
DEFAULT_PROTOCOL_CONFIG_FILE = 'protocol.yaml'
DEFAULT_PRIVATE_KEY_PATHS = {"default": "", "fetchai": "", "ethereum": ""}
T = TypeVar('T')

ProtocolId = str
SkillId = str
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


class PublicId(object):
    """This class implement a public identifier.

    A public identifier is composed of three elements:
    - username
    - package name
    - version

    The concatenation of those three elements gives the public identifier:

        username/package_name:version

    >>> public_id = PublicId("username", "my_package", "0.1.0")
    >>> assert public_id.username == "username"
    >>> assert public_id.package_name == "my_package"
    >>> assert public_id.version == "0.1.0"
    >>> another_public_id = PublicId("username", "my_package", "0.1.0")
    >>> assert hash(public_id) == hash(another_public_id)
    >>> assert public_id == another_public_id
    """

    AUTHOR_REGEX = r"[a-zA-Z0-9_]*"
    PACKAGE_NAME_REGEX = r"[a-zA-Z_][a-zA-Z0-9_]*"
    VERSION_REGEX = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
    PUBLIC_ID_REGEX = r"^({})/({}):({})$".format(AUTHOR_REGEX, PACKAGE_NAME_REGEX, VERSION_REGEX)

    def __init__(self, username: str, package_name: str, version: str):
        """Initialize the public identifier"""
        self._username = username
        self._package_name = package_name
        self._version = version

    @property
    def username(self):
        """Get the username."""
        return self._username

    @property
    def package_name(self):
        """Get the package_name."""
        return self._package_name

    @property
    def version(self):
        """Get the version."""
        return self._version

    @classmethod
    def from_string(cls, public_id_string: str) -> 'PublicId':
        """
        Initialize the public id from the string.

        >>> str(PublicId.from_string("username/package_name:0.1.0"))
        'username/package_name:0.1.0'

        A bad formatted input raises value error:
        >>> PublicId.from_string("bad/formatted:input")
        Traceback (most recent call last):
        ...
        ValueError: Input 'bad/formatted:input' is not well formatted.

        :param public_id_string: the public id in string format.
        :return: the public id object.
        :raises ValueError: if the string in input is not well formatted.
        """
        if not re.match(cls.PUBLIC_ID_REGEX, public_id_string):
            raise ValueError("Input '{}' is not well formatted.".format(public_id_string))
        else:
            username, package_name, version = re.findall(cls.PUBLIC_ID_REGEX, public_id_string)[0][:3]
            return PublicId(username, package_name, version)

    def __hash__(self):
        """Get the hash."""
        return hash((self.username, self.package_name, self.version))

    def __str__(self):
        """Get the string representation."""
        return "{username}/{package_name}:{version}"\
            .format(username=self.username, package_name=self.package_name, version=self.version)

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, PublicId) and self.username == other.username and self.package_name == other.package_name \
            and self.version == other.version


class PackageConfiguration(Configuration, ABC):
    """This class represent a package configuration."""

    def __init__(self,
                 name: str,
                 author: str,
                 version: str):
        """Initialize a package configuration."""
        self.name = name
        self.author = author
        self.version = version

    @property
    def public_id(self) -> PublicId:
        """Get the public id."""
        return PublicId(self.author, self.name, self.version)


class PrivateKeyPathConfig(Configuration):
    """Handle a private key path configuration."""

    def __init__(self, ledger: str = "", path: str = ""):
        """Initialize a handler configuration."""
        self.ledger = ledger
        self.path = path

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "ledger": self.ledger,
            "path": self.path
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        ledger = cast(str, obj.get("ledger"))
        path = cast(str, obj.get("path"))
        return PrivateKeyPathConfig(
            ledger=ledger,
            path=path
        )


class LedgerAPIConfig(Configuration):
    """Handle a ledger api configuration."""

    def __init__(self, **args):
        """Initialize a ledger class configuration."""
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "args": self.args
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        return LedgerAPIConfig(
            **obj.get("args", {})
        )


class ConnectionConfig(PackageConfiguration):
    """Handle connection configuration."""

    def __init__(self,
                 name: str = "",
                 author: str = "",
                 version: str = "",
                 license: str = "",
                 url: str = "",
                 class_name: str = "",
                 protocols: Optional[Set[PublicId]] = None,
                 restricted_to_protocols: Optional[Set[PublicId]] = None,
                 excluded_protocols: Optional[Set[PublicId]] = None,
                 dependencies: Optional[Dependencies] = None,
                 description: str = "",
                 **config):
        """Initialize a connection configuration object."""
        super().__init__(name, author, version)
        self.license = license
        self.fingerprint = ""
        self.url = url
        self.class_name = class_name
        self.protocols = protocols if protocols is not None else []
        self.restricted_to_protocols = restricted_to_protocols if restricted_to_protocols is not None else set()
        self.excluded_protocols = excluded_protocols if excluded_protocols is not None else set()
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.config = config

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "fingerprint": self.fingerprint,
            "url": self.url,
            "class_name": self.class_name,
            "protocols": list(map(str, self.protocols)),
            "restricted_to_protocols": list(map(str, self.restricted_to_protocols)),
            "excluded_protocols": list(map(str, self.excluded_protocols)),
            "dependencies": self.dependencies,
            "description": self.description,
            "config": self.config
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        restricted_to_protocols = obj.get("restricted_to_protocols", set())
        restricted_to_protocols = {PublicId.from_string(id_) for id_ in restricted_to_protocols}
        excluded_protocols = obj.get("excluded_protocols", set())
        excluded_protocols = {PublicId.from_string(id_) for id_ in excluded_protocols}
        dependencies = obj.get("dependencies", {})
        protocols = {PublicId.from_string(id_) for id_ in obj.get("protocols", set())}
        return ConnectionConfig(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            url=cast(str, obj.get("url")),
            class_name=cast(str, obj.get("class_name")),
            protocols=cast(Set[PublicId], protocols),
            restricted_to_protocols=cast(Set[PublicId], restricted_to_protocols),
            excluded_protocols=cast(Set[PublicId], excluded_protocols),
            dependencies=cast(Dependencies, dependencies),
            description=cast(str, obj.get("description", "")),
            **cast(dict, obj.get("config"))
        )


class ProtocolConfig(PackageConfiguration):
    """Handle protocol configuration."""

    def __init__(self,
                 name: str = "",
                 author: str = "",
                 version: str = "",
                 license: str = "",
                 url: str = "",
                 dependencies: Optional[Dependencies] = None,
                 description: str = ""):
        """Initialize a connection configuration object."""
        super().__init__(name, author, version)
        self.license = license
        self.fingerprint = ""
        self.url = url
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "fingerprint": self.fingerprint,
            "url": self.url,
            "dependencies": self.dependencies,
            "description": self.description
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
            url=cast(str, obj.get("url")),
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
        return {
            "class_name": self.class_name,
            "args": self.args
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        class_name = cast(str, obj.get("class_name"))
        return HandlerConfig(
            class_name=class_name,
            **obj.get("args", {})
        )


class BehaviourConfig(Configuration):
    """Handle a skill behaviour configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a behaviour configuration."""
        self.class_name = class_name
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "class_name": self.class_name,
            "args": self.args
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        class_name = cast(str, obj.get("class_name"))
        return BehaviourConfig(
            class_name=class_name,
            **obj.get("args", {})
        )


class TaskConfig(Configuration):
    """Handle a skill task configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a task configuration."""
        self.class_name = class_name
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "class_name": self.class_name,
            "args": self.args
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        class_name = cast(str, obj.get("class_name"))
        return TaskConfig(
            class_name=class_name,
            **obj.get("args", {})
        )


class SharedClassConfig(Configuration):
    """Handle a skill shared class configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a shared class configuration."""
        self.class_name = class_name
        self.args = args

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "class_name": self.class_name,
            "args": self.args
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        class_name = cast(str, obj.get("class_name"))
        return SharedClassConfig(
            class_name=class_name,
            **obj.get("args", {})
        )


class SkillConfig(PackageConfiguration):
    """Class to represent a skill configuration file."""

    def __init__(self,
                 name: str = "",
                 author: str = "",
                 version: str = "",
                 license: str = "",
                 url: str = "",
                 protocols: List[PublicId] = None,
                 dependencies: Optional[Dependencies] = None,
                 description: str = ""):
        """Initialize a skill configuration."""
        super().__init__(name, author, version)
        self.license = license
        self.fingerprint = ""
        self.url = url
        self.protocols = protocols if protocols is not None else []  # type: List[PublicId]
        self.dependencies = dependencies if dependencies is not None else {}
        self.description = description
        self.handlers = CRUDCollection[HandlerConfig]()
        self.behaviours = CRUDCollection[BehaviourConfig]()
        self.tasks = CRUDCollection[TaskConfig]()
        self.shared_classes = CRUDCollection[SharedClassConfig]()

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "fingerprint": self.fingerprint,
            "url": self.url,
            "protocols": list(map(str, self.protocols)),
            "dependencies": self.dependencies,
            "handlers": {key: h.json for key, h in self.handlers.read_all()},
            "behaviours": {key: b.json for key, b in self.behaviours.read_all()},
            "tasks": {key: t.json for key, t in self.tasks.read_all()},
            "shared_classes": {key: s.json for key, s in self.shared_classes.read_all()},
            "description": self.description
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        name = cast(str, obj.get("name"))
        author = cast(str, obj.get("author"))
        version = cast(str, obj.get("version"))
        license = cast(str, obj.get("license"))
        url = cast(str, obj.get("url"))
        protocols = cast(List[PublicId], [PublicId.from_string(id_) for id_ in obj.get("protocols", [])])
        dependencies = cast(Dependencies, obj.get("dependencies", {}))
        description = cast(str, obj.get("description", ""))
        skill_config = SkillConfig(
            name=name,
            author=author,
            version=version,
            license=license,
            url=url,
            protocols=protocols,
            dependencies=dependencies,
            description=description
        )

        for behaviour_id, behaviour_data in obj.get("behaviours", {}).items():  # type: ignore
            behaviour_config = BehaviourConfig.from_json(behaviour_data)
            skill_config.behaviours.create(behaviour_id, behaviour_config)

        for task_id, task_data in obj.get("tasks", {}).items():  # type: ignore
            task_config = TaskConfig.from_json(task_data)
            skill_config.tasks.create(task_id, task_config)

        for handler_id, handler_data in obj.get("handlers", {}).items():  # type: ignore
            handler_config = HandlerConfig.from_json(handler_data)
            skill_config.handlers.create(handler_id, handler_config)

        for shared_class_id, shared_class_data in obj.get("shared_classes", {}).items():  # type: ignore
            shared_class_config = SharedClassConfig.from_json(shared_class_data)
            skill_config.shared_classes.create(shared_class_id, shared_class_config)

        return skill_config


class AgentConfig(Configuration):
    """Class to represent the agent configuration file."""

    def __init__(self,
                 agent_name: str = "",
                 aea_version: str = "",
                 author: str = "",
                 version: str = "",
                 license: str = "",
                 fingerprint: str = "",
                 url: str = "",
                 registry_path: str = "",
                 description: str = "",
                 private_key_paths: Dict[str, str] = None,
                 logging_config: Optional[Dict] = None):
        """Instantiate the agent configuration object."""
        self.agent_name = agent_name
        self.aea_version = aea_version
        self.author = author
        self.version = version
        self.license = license
        self.fingerprint = fingerprint
        self.url = url
        self.registry_path = registry_path
        self.description = description
        self.private_key_paths = CRUDCollection[PrivateKeyPathConfig]()
        self.ledger_apis = CRUDCollection[LedgerAPIConfig]()

        private_key_paths = private_key_paths if private_key_paths is not None else {}
        for ledger, path in private_key_paths.items():
            self.private_key_paths.create(ledger, PrivateKeyPathConfig(ledger, path))

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
    def default_connection(self) -> str:
        """Get the default connection."""
        assert self._default_connection is not None, "Default connection not set yet."
        return str(self._default_connection)

    @default_connection.setter
    def default_connection(self, connection_name: Optional[str]):
        """
        Set the default connection.

        :param connection_name: the name of the default connection.
        :return: None
        """
        if connection_name is not None:
            self._default_connection = PublicId.from_string(connection_name)
        else:
            self._default_connection = None

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
            "aea_version": self.aea_version,
            "author": self.author,
            "version": self.version,
            "license": self.license,
            "fingerprint": self.fingerprint,
            "url": self.url,
            "registry_path": self.registry_path,
            "description": self.description,
            "private_key_paths": [{"private_key_path": p.json} for l, p in self.private_key_paths.read_all()],
            "ledger_apis": {key: l.json for key, l in self.ledger_apis.read_all()},
            "logging_config": self.logging_config,
            "default_ledger": self.default_ledger,
            "default_connection": self.default_connection,
            "connections": sorted(map(str, self.connections)),
            "protocols": sorted(map(str, self.protocols)),
            "skills": sorted(map(str, self.skills))
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        private_key_paths = {}
        for p in obj.get("private_key_paths", []):  # type: ignore
            private_key_path = PrivateKeyPathConfig.from_json(p["private_key_path"])
            private_key_paths[private_key_path.ledger] = private_key_path.path

        agent_config = AgentConfig(
            agent_name=cast(str, obj.get("agent_name")),
            aea_version=cast(str, obj.get("aea_version")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            url=cast(str, obj.get("url")),
            registry_path=cast(str, obj.get("registry_path")),
            description=cast(str, obj.get("description", "")),
            logging_config=cast(Dict, obj.get("logging_config", {})),
            private_key_paths=cast(Dict, private_key_paths),
        )

        for ledger_id, ledger_data in obj.get("ledger_apis", {}).items():  # type: ignore
            ledger_config = LedgerAPIConfig.from_json(ledger_data)
            agent_config.ledger_apis.create(ledger_id, ledger_config)

        # parse connection public ids
        connections = set(map(lambda x: PublicId.from_string(x), obj.get("connections", [])))
        agent_config.connections = cast(Set[PublicId], connections)

        # parse protocol public ids
        protocols = set(map(lambda x: PublicId.from_string(x), obj.get("protocols", [])))
        agent_config.protocols = cast(Set[PublicId], protocols)

        # parse skills public ids
        skills = set(map(lambda x: PublicId.from_string(x), obj.get("skills", [])))
        agent_config.skills = cast(Set[PublicId], skills)

        # set default connection
        default_connection_name = obj.get("default_connection", None)
        agent_config.default_connection = default_connection_name
        default_ledger_id = obj.get("default_ledger", None)
        agent_config.default_ledger = default_ledger_id

        return agent_config
