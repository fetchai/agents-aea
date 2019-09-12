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

from typing import TypeVar, Generic, Any, Optional, List, Tuple, Dict, Set

DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
T = TypeVar('T')


class CRUDCollection(Generic[T]):
    """Interface of a CRUD collection."""

    def __init__(self):
        """Instantiate a CRUD collection."""
        self._items_by_id = {}  # type: Dict[str, Any]

    def create(self, item_id: str, item: Any) -> None:
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

    def read(self, item_id: str) -> Optional[Any]:
        """
        Get an item by its name.

        :param item_id: the item id.
        :return: the associated item, or None if the item id is not present.
        """
        return self._items_by_id.get(item_id, None)

    def update(self, item_id: str, item: Any) -> None:
        """
        Update an existing item.

        :param item_id: the item id.
        :param item: the item to be added.
        :return: None
        """
        self._items_by_id[item_id] = item

    def delete(self, item_id: str) -> None:
        """Delete an item."""
        self._items_by_id.pop(item_id, None)

    def read_all(self) -> List[Tuple[str, Any]]:
        """Read all the items."""
        return [(k, v) for k, v in self._items_by_id.items()]


class ConnectionConfig:
    """Handle connection configuration."""

    def __init__(self, name: str = "", type: str = "", **config):
        """Initialize a connection configuration object."""
        self.name = name
        self.type = type
        self.config = config


class HandlerConfig:
    """Handle a skill handler configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a handler configuration."""
        self.class_name = class_name
        self.args = args


class BehaviourConfig:
    """Handle a skill behaviour configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a behaviour configuration."""
        self.class_name = class_name
        self.args = args


class TaskConfig:
    """Handle a skill task configuration."""

    def __init__(self, class_name: str = "", **args):
        """Initialize a task configuration."""
        self.class_name = class_name
        self.args = args


class SkillConfig(object):
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


class AgentConfig(object):
    """Class to represent the agent configuration file."""

    def __init__(self, agent_name: str = "", aea_version: str = ""):
        """Instantiate the agent configuration object."""
        self.agent_name = agent_name  # type: str
        self.aea_version = aea_version  # type: str
        self._default_connection = None  # type: Optional[ConnectionConfig]
        self.connections = CRUDCollection[ConnectionConfig]()  # type: CRUDCollection
        self.protocols = set()  # type: Set[str]
        self.skills = set()  # type: Set[str]

    @property
    def default_connection(self) -> ConnectionConfig:
        """Get the default connection."""
        assert self._default_connection is not None, "Default connection not set yet."
        return self._default_connection

    def set_default_connection(self, connection: ConnectionConfig):
        """
        Set the default connection.

        :param connection: the default connection.
        :return: None
        """
        self._default_connection = connection
        self.connections.update(connection.name, connection)
