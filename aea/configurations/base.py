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

    def __init__(self, ledger: str = "", addr: str = "", port: int = 1000):
        """Initialize a handler configuration."""
        self.ledger = ledger
        self.addr = addr
        self.port = port

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "ledger": self.ledger,
            "addr": self.addr,
            "port": self.port
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        ledger = cast(str, obj.get("ledger"))
        addr = cast(str, obj.get("addr"))
        port = cast(int, obj.get("port"))
        return LedgerAPIConfig(
            ledger=ledger,
            addr=addr,
            port=port
        )


class ConnectionConfig(Configuration):
    """Handle connection configuration."""

    def __init__(self,
                 name: str = "",
                 author: str = "",
                 version: str = "",
                 license: str = "",
                 url: str = "",
                 class_name: str = "",
                 protocols: List[str] = None,
                 restricted_to_protocols: Optional[Set[str]] = None,
                 excluded_protocols: Optional[Set[str]] = None,
                 dependencies: Optional[Dependencies] = None,
                 description: str = "",
                 **config):
        """Initialize a connection configuration object."""
        self.name = name
        self.author = author
        self.version = version
        self.license = license
        self.fingerprint = ""
        self.url = url
        self.class_name = class_name
        self.protocols = protocols
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
            "protocols": self.protocols,
            "restricted_to_protocols": self.restricted_to_protocols,
            "excluded_protocols": self.excluded_protocols,
            "dependencies": self.dependencies,
            "description": self.description,
            "config": self.config
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        restricted_to_protocols = obj.get("restricted_to_protocols")
        restricted_to_protocols = restricted_to_protocols if restricted_to_protocols is not None else set()
        excluded_protocols = obj.get("excluded_protocols")
        excluded_protocols = excluded_protocols if excluded_protocols is not None else set()
        dependencies = cast(Dependencies, obj.get("dependencies", {}))
        protocols = cast(List[str], obj.get("protocols", []))
        return ConnectionConfig(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            url=cast(str, obj.get("url")),
            class_name=cast(str, obj.get("class_name")),
            protocols=protocols,
            restricted_to_protocols=cast(Set[str], restricted_to_protocols),
            excluded_protocols=cast(Set[str], excluded_protocols),
            dependencies=dependencies,
            description=cast(str, obj.get("description", "")),
            **cast(dict, obj.get("config"))
        )


class ProtocolConfig(Configuration):
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
        self.name = name
        self.author = author
        self.version = version
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


class SkillConfig(Configuration):
    """Class to represent a skill configuration file."""

    def __init__(self,
                 name: str = "",
                 author: str = "",
                 version: str = "",
                 license: str = "",
                 url: str = "",
                 protocols: List[str] = None,
                 dependencies: Optional[Dependencies] = None,
                 description: str = ""):
        """Initialize a skill configuration."""
        self.name = name
        self.author = author
        self.version = version
        self.license = license
        self.fingerprint = ""
        self.url = url
        self.protocols = protocols if protocols is not None else []  # type: List[str]
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
            "protocols": self.protocols,
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
        protocols = cast(List[str], obj.get("protocols", []))
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
                 ledger_apis: Dict[str, Tuple[str, int]] = None,
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

        ledger_apis = ledger_apis if ledger_apis is not None else {}
        for ledger, (addr, port) in ledger_apis.items():
            self.ledger_apis.create(ledger, LedgerAPIConfig(ledger, addr, port))

        self.logging_config = logging_config if logging_config is not None else {}
        self._default_connection = None  # type: Optional[str]
        self.connections = set()  # type: Set[str]
        self.protocols = set()  # type: Set[str]
        self.skills = set()  # type: Set[str]

        if self.logging_config == {}:
            self.logging_config["version"] = 1
            self.logging_config["disable_existing_loggers"] = False

    @property
    def default_connection(self) -> str:
        """Get the default connection."""
        assert self._default_connection is not None, "Default connection not set yet."
        return self._default_connection

    @default_connection.setter
    def default_connection(self, connection_name: str):
        """
        Set the default connection.

        :param connection_name: the name of the default connection.
        :return: None
        """
        self._default_connection = connection_name

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
            "ledger_apis": [{"ledger_api": t.json} for l, t in self.ledger_apis.read_all()],
            "logging_config": self.logging_config,
            "default_connection": self.default_connection,
            "connections": sorted(self.connections),
            "protocols": sorted(self.protocols),
            "skills": sorted(self.skills)
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        private_key_paths = {}
        for p in obj.get("private_key_paths", []):  # type: ignore
            private_key_path = PrivateKeyPathConfig.from_json(p["private_key_path"])
            private_key_paths[private_key_path.ledger] = private_key_path.path

        ledger_apis = {}
        for l in obj.get("ledger_apis", []):  # type: ignore
            ledger_api = LedgerAPIConfig.from_json(l["ledger_api"])
            ledger_apis[ledger_api.ledger] = (ledger_api.addr, ledger_api.port)

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
            ledger_apis=cast(Dict, ledger_apis)
        )

        agent_config.connections = set(cast(List[str], obj.get("connections")))
        agent_config.protocols = set(cast(List[str], obj.get("protocols")))
        agent_config.skills = set(cast(List[str], obj.get("skills")))

        # set default configuration
        default_connection_name = obj.get("default_connection", None)
        agent_config.default_connection = default_connection_name

        return agent_config
