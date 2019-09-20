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

DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
T = TypeVar('T')

Address = str
ProtocolId = str


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


class ConnectionConfig(Configuration):
    """Handle connection configuration."""

    def __init__(self,
                 name: str = "",
                 authors: str = "",
                 version: str = "",
                 license: str = "",
                 url: str = "",
                 class_name: str = "",
                 supported_protocols: Optional[List[ProtocolId]] = None,
                 **config):
        """Initialize a connection configuration object."""
        self.name = name
        self.authors = authors
        self.version = version
        self.license = license
        self.url = url
        self.class_name = class_name
        self.supported_protocols = supported_protocols if supported_protocols is not None else []
        self.config = config

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "authors": self.authors,
            "version": self.version,
            "license": self.license,
            "url": self.url,
            "class_name": self.class_name,
            "supported_protocol": self.supported_protocols,
            "config": self.config
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        supported_protocols = cast(List[str], obj.get("supported_protocols"))
        return ConnectionConfig(
            name=cast(str, obj.get("name")),
            authors=cast(str, obj.get("authors")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            url=cast(str, obj.get("url")),
            class_name=cast(str, obj.get("class_name")),
            supported_protocols=supported_protocols,
            config=obj.get("config")
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
            args=obj.get("args")
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
            args=obj.get("args")
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
            args=obj.get("args")
        )


class SkillConfig(Configuration):
    """Class to represent a skill configuration file."""

    def __init__(self,
                 name: str = "",
                 authors: str = "",
                 version: str = "",
                 license: str = "",
                 url: str = "",
                 protocol: str = ""):
        """Initialize a skill configuration."""
        self.name = name
        self.authors = authors
        self.version = version
        self.license = license
        self.url = url
        self.protocol = protocol
        self.handler = HandlerConfig()
        self.behaviours = CRUDCollection[BehaviourConfig]()
        self.tasks = CRUDCollection[TaskConfig]()

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "name": self.name,
            "authors": self.authors,
            "version": self.version,
            "license": self.license,
            "url": self.url,
            "protocol": self.protocol,
            "handler": self.handler.json,
            "behaviours": [{"behaviour": b.json} for _, b in self.behaviours.read_all()],
            "tasks": [{"task": t.json} for _, t in self.tasks.read_all()],
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        name = cast(str, obj.get("name"))
        authors = cast(str, obj.get("authors"))
        version = cast(str, obj.get("version"))
        license = cast(str, obj.get("license"))
        url = cast(str, obj.get("url"))
        protocol = cast(str, obj.get("protocol"))
        skill_config = SkillConfig(
            name=name,
            authors=authors,
            version=version,
            license=license,
            url=url,
            protocol=protocol
        )

        for b in obj.get("behaviours"):  # type: ignore
            behaviour_config = BehaviourConfig.from_json(b["behaviour"])
            skill_config.behaviours.create(behaviour_config.class_name, behaviour_config)

        for t in obj.get("tasks"):  # type: ignore
            task_config = BehaviourConfig.from_json(t["task"])
            skill_config.tasks.create(task_config.class_name, task_config)

        handler = HandlerConfig.from_json(obj.get("handler"))  # type: ignore
        skill_config.handler = handler

        return skill_config


class AgentConfig(Configuration):
    """Class to represent the agent configuration file."""

    def __init__(self,
                 agent_name: str = "",
                 aea_version: str = "",
                 authors: str = "",
                 version: str = "",
                 license: str = "",
                 url: str = "",
                 private_key_pem_path: str = ""):
        """Instantiate the agent configuration object."""
        self.agent_name = agent_name
        self.aea_version = aea_version
        self.authors = authors
        self.version = version
        self.license = license
        self.url = url
        self.private_key_pem_path = private_key_pem_path
        self._default_connection = None  # type: Optional[str]
        self.connections = set()  # type: Set[str]
        self.protocols = set()  # type: Set[str]
        self.skills = set()  # type: Set[str]

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
            "authors": self.authors,
            "version": self.version,
            "license": self.license,
            "url": self.url,
            "private_key_pem_path": self.private_key_pem_path,
            "default_connection": self.default_connection,
            "connections": sorted(self.connections),
            "protocols": sorted(self.protocols),
            "skills": sorted(self.skills)
        }

    @classmethod
    def from_json(cls, obj: Dict):
        """Initialize from a JSON object."""
        agent_config = AgentConfig(
            agent_name=cast(str, obj.get("agent_name")),
            aea_version=cast(str, obj.get("aea_version")),
            authors=cast(str, obj.get("authors")),
            version=cast(str, obj.get("version")),
            license=cast(str, obj.get("license")),
            url=cast(str, obj.get("url")),
            private_key_pem_path=cast(str, obj.get("private_key_pem_path")),
        )

        agent_config.connections = set(cast(List[str], obj.get("connections")))
        agent_config.protocols = set(cast(List[str], obj.get("protocols")))
        agent_config.skills = set(cast(List[str], obj.get("skills")))

        # set default configuration
        default_connection_name = obj.get("default_connection", None)
        agent_config.default_connection = default_connection_name

        return agent_config
