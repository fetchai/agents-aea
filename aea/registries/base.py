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

"""This module contains registries."""

import copy
from abc import ABC, abstractmethod
from operator import itemgetter
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, TypeVar, cast

from aea.components.base import Component
from aea.configurations.base import ComponentId, ComponentType, PublicId
from aea.exceptions import AEASetupError, AEATeardownError, parse_exception
from aea.helpers.logging import WithLogger, get_logger
from aea.skills.base import Behaviour, Handler, Model


Item = TypeVar("Item")
ItemId = TypeVar("ItemId")
SkillComponentType = TypeVar("SkillComponentType", Handler, Behaviour, Model)


class Registry(Generic[ItemId, Item], WithLogger, ABC):
    """This class implements an abstract registry."""

    def __init__(self, agent_name: str = "standalone") -> None:
        """
        Initialize the registry.

        :param agent_name: the name of the agent
        """
        logger = get_logger(__name__, agent_name)
        super().__init__(logger)

    @abstractmethod
    def register(
        self, item_id: ItemId, item: Item, is_dynamically_added: bool = False
    ) -> None:
        """
        Register an item.

        :param item_id: the public id of the item.
        :param item: the item.
        :param is_dynamically_added: whether or not the item is dynamically added.
        :return: None
        :raises: ValueError if an item is already registered with that item id.
        """

    @abstractmethod
    def unregister(self, item_id: ItemId) -> Optional[Item]:
        """
        Unregister an item.

        :param item_id: the public id of the item.
        :return: the item
        :raises: ValueError if no item registered with that item id.
        """

    @abstractmethod
    def fetch(self, item_id: ItemId) -> Optional[Item]:
        """
        Fetch an item.

        :param item_id: the public id of the item.
        :return: the Item
        """

    @abstractmethod
    def fetch_all(self) -> List[Item]:
        """
        Fetch all the items.

        :return: the list of items.
        """

    @abstractmethod
    def ids(self) -> Set[ItemId]:
        """
        Return the set of all the used item ids.

        :return: the set of item ids.
        """

    @abstractmethod
    def setup(self) -> None:
        """
        Set up registry.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """


class PublicIdRegistry(Generic[Item], Registry[PublicId, Item]):
    """
    This class implement a registry whose keys are public ids.

    In particular, it is able to handle the case when the public id
    points to the 'latest' version of a package.
    """

    __slots__ = ("_public_id_to_item",)

    def __init__(self) -> None:
        """Initialize the registry."""
        super().__init__()
        self._public_id_to_item: Dict[PublicId, Item] = {}

    def register(  # pylint: disable=arguments-differ,unused-argument
        self, public_id: PublicId, item: Item, is_dynamically_added: bool = False
    ) -> None:
        """Register an item."""
        if public_id.package_version.is_latest:
            raise ValueError(
                f"Cannot register item with public id 'latest': {public_id}"
            )
        if public_id in self._public_id_to_item:
            raise ValueError(f"Item already registered with item id '{public_id}'")
        self._public_id_to_item[public_id] = item

    def unregister(  # pylint: disable=arguments-differ
        self, public_id: PublicId
    ) -> Item:
        """Unregister an item."""
        if public_id not in self._public_id_to_item:
            raise ValueError(f"No item registered with item id '{public_id}'")
        item = self._public_id_to_item.pop(public_id)
        return item

    def fetch(  # pylint: disable=arguments-differ
        self, public_id: PublicId
    ) -> Optional[Item]:
        """
        Fetch an item associated with a public id.

        :param public_id: the public id.
        :return: an item, or None if the key is not present.
        """
        if public_id.package_version.is_latest:
            filtered_records: List[Tuple[PublicId, Item]] = list(
                filter(
                    lambda x: public_id.same_prefix(x[0]),
                    self._public_id_to_item.items(),
                )
            )
            if len(filtered_records) == 0:
                return None
            return max(filtered_records, key=itemgetter(0))[1]
        return self._public_id_to_item.get(public_id, None)

    def fetch_all(self) -> List[Item]:
        """Fetch all the items."""
        return list(self._public_id_to_item.values())

    def ids(self) -> Set[PublicId]:
        """Get all the item ids."""
        return set(self._public_id_to_item.keys())

    def setup(self) -> None:
        """Set up the items."""

    def teardown(self) -> None:
        """Tear down the items."""


class AgentComponentRegistry(Registry[ComponentId, Component]):
    """This class implements a simple dictionary-based registry for agent components."""

    __slots__ = ("_components_by_type", "_registered_keys")

    def __init__(self, **kwargs: Any) -> None:
        """
        Instantiate the registry.

        :param kwargs: kwargs
        """
        super().__init__(**kwargs)
        self._components_by_type: Dict[ComponentType, Dict[PublicId, Component]] = {}
        self._registered_keys: Set[ComponentId] = set()

    def register(  # pylint: disable=arguments-differ,unused-argument
        self,
        component_id: ComponentId,
        component: Component,
        is_dynamically_added: bool = False,
    ) -> None:
        """
        Register a component.

        :param component_id: the id of the component.
        :param component: the component object.
        :param is_dynamically_added: whether or not the item is dynamically added.
        """
        if component_id in self._registered_keys:
            raise ValueError(
                "Component already registered with item id '{}'".format(component_id)
            )
        if component.component_id != component_id:
            raise ValueError(
                "Component id '{}' is different to the id '{}' specified.".format(
                    component.component_id, component_id
                )
            )
        self._register(component_id, component)

    def _register(self, component_id: ComponentId, component: Component) -> None:
        """
        Do the actual registration.

        :param component_id: the component id
        :param component: the component to register
        """
        self._components_by_type.setdefault(component_id.component_type, {})[
            component_id.public_id
        ] = component
        self._registered_keys.add(component_id)

    def _unregister(self, component_id: ComponentId) -> Optional[Component]:
        """
        Do the actual unregistration.

        :param component_id: the component id
        :return: the item
        """
        item = self._components_by_type.get(component_id.component_type, {}).pop(
            component_id.public_id, None
        )
        self._registered_keys.discard(component_id)
        if item is not None:
            self.logger.debug(
                "Component '{}' has been removed.".format(item.component_id)
            )
        return item

    def unregister(  # pylint: disable=arguments-differ
        self, component_id: ComponentId
    ) -> Optional[Component]:
        """
        Unregister a component.

        :param component_id: the ComponentId
        :return: the item
        """
        if component_id not in self._registered_keys:
            raise ValueError(
                "No item registered with item id '{}'".format(component_id)
            )
        return self._unregister(component_id)

    def fetch(  # pylint: disable=arguments-differ
        self, component_id: ComponentId
    ) -> Optional[Component]:
        """
        Fetch the component by id.

        :param component_id: the contract id
        :return: the component or None if the component is not registered
        """
        return self._components_by_type.get(component_id.component_type, {}).get(
            component_id.public_id, None
        )

    def fetch_all(self) -> List[Component]:
        """
        Fetch all the components.

        :return: the list of registered components.
        """
        return [
            component
            for components_by_public_id in self._components_by_type.values()
            for component in components_by_public_id.values()
        ]

    def fetch_by_type(self, component_type: ComponentType) -> List[Component]:
        """
        Fetch all the components by a given type..

        :param component_type: a component type
        :return: the list of registered components of a given type.
        """
        return list(self._components_by_type.get(component_type, {}).values())

    def ids(self) -> Set[ComponentId]:
        """Get the item ids."""
        return self._registered_keys

    def setup(self) -> None:
        """Set up the registry."""

    def teardown(self) -> None:
        """Teardown the registry."""


class ComponentRegistry(
    Registry[Tuple[PublicId, str], SkillComponentType], Generic[SkillComponentType]
):
    """This class implements a generic registry for skill components."""

    __slots__ = ("_items", "_dynamically_added")

    def __init__(self, **kwargs: Any) -> None:
        """
        Instantiate the registry.

        :param kwargs: kwargs
        """
        super().__init__(**kwargs)
        self._items: PublicIdRegistry[
            Dict[str, SkillComponentType]
        ] = PublicIdRegistry()
        self._dynamically_added: Dict[PublicId, Set[str]] = {}

    def register(
        self,
        item_id: Tuple[PublicId, str],
        item: SkillComponentType,
        is_dynamically_added: bool = False,
    ) -> None:
        """
        Register a item.

        :param item_id: a pair (skill id, item name).
        :param item: the item to register.
        :param is_dynamically_added: whether or not the item is dynamically added.
        :raises: ValueError if an item is already registered with that item id.
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        skill_items = self._items.fetch(skill_id)
        if skill_items is not None and item_name in skill_items.keys():
            raise ValueError(
                f"Item already registered with skill id '{skill_id}' and name '{item_name}'"
            )

        if skill_items is not None:
            self._items.unregister(skill_id)
        else:
            skill_items = {}
        skill_items[item_name] = item
        self._items.register(skill_id, skill_items)

        if is_dynamically_added:
            self._dynamically_added.setdefault(skill_id, set()).add(item_name)

    def unregister(self, item_id: Tuple[PublicId, str]) -> Optional[SkillComponentType]:
        """
        Unregister a item.

        :param item_id: a pair (skill id, item name).
        :return: skill component
        :raises: ValueError if no item registered with that item id.
        """
        return self._unregister_from_main_index(item_id)

    def _unregister_from_main_index(
        self, item_id: Tuple[PublicId, str]
    ) -> SkillComponentType:
        """
        Unregister a item.

        :param item_id: a pair (skill id, item name).
        :return: None
        :raises: ValueError if no item registered with that item id.
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        name_to_item = self._items.fetch(skill_id)
        if name_to_item is None or item_name not in name_to_item:
            raise ValueError(
                "No item registered with component id '{}'".format(item_id)
            )
        self.logger.debug("Unregistering item with id {}".format(item_id))
        item = name_to_item.pop(item_name)
        if len(name_to_item) == 0:
            self._items.unregister(skill_id)
        else:
            self._items.unregister(skill_id)
            self._items.register(skill_id, name_to_item)

        items = self._dynamically_added.get(skill_id, None)
        if items is not None:
            items.remove(item_name)
            if len(items) == 0:
                self._dynamically_added.pop(skill_id, None)
        return item

    def fetch(self, item_id: Tuple[PublicId, str]) -> Optional[SkillComponentType]:
        """
        Fetch an item.

        :param item_id: the public id of the item.
        :return: the Item
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        name_to_item = self._items.fetch(skill_id)
        if name_to_item is None:
            return None
        return name_to_item.get(item_name, None)

    def fetch_by_skill(self, skill_id: PublicId) -> List[SkillComponentType]:
        """Fetch all the items of a given skill."""
        temp: Optional[Dict[str, SkillComponentType]] = self._items.fetch(skill_id)
        name_to_item: Dict[str, SkillComponentType] = {} if temp is None else temp
        return list(name_to_item.values())

    def fetch_all(self) -> List[SkillComponentType]:
        """Fetch all the items."""
        return [item for items in self._items.fetch_all() for item in items.values()]

    def unregister_by_skill(self, skill_id: PublicId) -> None:
        """Unregister all the components by skill."""
        if skill_id not in self._items.ids():
            raise ValueError(
                "No component of skill {} present in the registry.".format(skill_id)
            )
        self._items.unregister(skill_id)
        self._dynamically_added.pop(skill_id, None)

    def ids(self) -> Set[Tuple[PublicId, str]]:
        """Get the item ids."""
        result: Set[Tuple[PublicId, str]] = set()
        for skill_id in self._items.ids():
            name_to_item = cast(
                Dict[str, SkillComponentType], self._items.fetch(skill_id)
            )
            for name, _ in name_to_item.items():
                result.add((skill_id, name))
        return result

    def setup(self) -> None:
        """Set up the items in the registry."""
        for item in self.fetch_all():
            if item.context.is_active:
                self.logger.debug(
                    "Calling setup() of component {} of skill {}".format(
                        item.name, item.skill_id
                    )
                )
                try:
                    item.setup()
                except Exception as e:  # pragma: nocover # pylint: disable=broad-except
                    e_str = parse_exception(e)
                    e_str = f"An error occurred while setting up item {item.skill_id}/{type(item).__name__}:\n{e_str}"
                    raise AEASetupError(e_str)
            else:
                self.logger.debug(
                    "Ignoring setup() of component {} of skill {}, because the skill is not active.".format(
                        item.name, item.skill_id
                    )
                )

    def teardown(self) -> None:
        """Teardown the registry."""
        for name_to_items in self._items.fetch_all():
            for _, item in name_to_items.items():
                self.logger.debug(
                    "Calling teardown() of component {} of skill {}".format(
                        item.name, item.skill_id
                    )
                )
                try:
                    item.teardown()
                except Exception as e:  # pragma: nocover # pylint: disable=broad-except
                    e_str = parse_exception(e)
                    e_str = f"An error occurred while tearing down item {item.skill_id}/{type(item).__name__}:\n{str(e_str)}"
                    e = AEATeardownError(e_str)
                    self.logger.error(str(e))
        _dynamically_added = copy.deepcopy(self._dynamically_added)
        for skill_id, items_names in _dynamically_added.items():
            for item_name in items_names:
                self.unregister((skill_id, item_name))


class HandlerRegistry(ComponentRegistry[Handler]):
    """This class implements the handlers registry."""

    __slots__ = ("_items_by_protocol_and_skill",)

    def __init__(self, **kwargs: Any) -> None:
        """
        Instantiate the registry.

        :param kwargs: kwargs
        """
        super().__init__(**kwargs)
        # nested public id registries; one for protocol ids, one for skill ids
        self._items_by_protocol_and_skill = PublicIdRegistry[
            PublicIdRegistry[Handler]
        ]()

    def register(
        self,
        item_id: Tuple[PublicId, str],
        item: Handler,
        is_dynamically_added: bool = False,
    ) -> None:
        """
        Register a handler.

        :param item_id: the item id.
        :param item: the handler.
        :param is_dynamically_added: whether or not the item is dynamically added.
        :raises ValueError: if the protocol is None, or an item with pair (skill_id, protocol_id_ already exists.
        """
        skill_id = item_id[0]

        protocol_id = item.SUPPORTED_PROTOCOL
        if protocol_id is None:
            raise ValueError(
                "Please specify a supported protocol for handler class '{}'".format(
                    item.__class__.__name__
                )
            )

        protocol_handlers_by_skill = self._items_by_protocol_and_skill.fetch(
            protocol_id
        )
        if (
            protocol_handlers_by_skill is not None
            and skill_id in protocol_handlers_by_skill.ids()
        ):
            raise ValueError(
                "A handler already registered with pair of protocol id {} and skill id {}".format(
                    protocol_id, skill_id
                )
            )
        if protocol_handlers_by_skill is None:
            # registry from skill ids to handlers.
            new_registry: PublicIdRegistry = PublicIdRegistry()
            self._items_by_protocol_and_skill.register(protocol_id, new_registry)
        registry = cast(Registry, self._items_by_protocol_and_skill.fetch(protocol_id))
        registry.register(skill_id, item)
        super().register(item_id, item, is_dynamically_added=is_dynamically_added)

    def unregister(self, item_id: Tuple[PublicId, str]) -> Handler:
        """
        Unregister a item.

        :param item_id: a pair (skill id, item name).
        :return: the unregistered handler
        :raises: ValueError if no item is registered with that item id.
        """
        skill_id = item_id[0]
        handler = super()._unregister_from_main_index(item_id)

        # remove from index by protocol and skill
        protocol_id = cast(PublicId, handler.SUPPORTED_PROTOCOL)
        protocol_handlers_by_skill = cast(
            PublicIdRegistry, self._items_by_protocol_and_skill.fetch(protocol_id)
        )
        protocol_handlers_by_skill.unregister(skill_id)
        if len(protocol_handlers_by_skill.ids()) == 0:
            self._items_by_protocol_and_skill.unregister(protocol_id)
        return handler

    def unregister_by_skill(self, skill_id: PublicId) -> None:
        """Unregister all the components by skill."""
        # unregister from the main index.
        if skill_id not in self._items.ids():
            raise ValueError(
                "No component of skill {} present in the registry.".format(skill_id)
            )

        self._dynamically_added.pop(skill_id, None)

        handlers = cast(Dict[str, Handler], self._items.fetch(skill_id)).values()
        self._items.unregister(skill_id)

        # unregister from the protocol-skill index
        for handler in handlers:
            protocol_id = cast(PublicId, handler.SUPPORTED_PROTOCOL)
            if protocol_id in self._items_by_protocol_and_skill.ids():
                skill_id_to_handler = cast(
                    PublicIdRegistry,
                    self._items_by_protocol_and_skill.fetch(protocol_id),
                )
                skill_id_to_handler.unregister(skill_id)

    def fetch_by_protocol(self, protocol_id: PublicId) -> List[Handler]:
        """
        Fetch the handler by the pair protocol id and skill id.

        :param protocol_id: the protocol id
        :return: the handlers registered for the protocol_id and skill_id
        """
        if protocol_id not in self._items_by_protocol_and_skill.ids():
            return []

        protocol_handlers_by_skill = cast(
            PublicIdRegistry, self._items_by_protocol_and_skill.fetch(protocol_id)
        )
        handlers = [
            cast(Handler, protocol_handlers_by_skill.fetch(skill_id))
            for skill_id in protocol_handlers_by_skill.ids()
        ]
        return handlers

    def fetch_by_protocol_and_skill(
        self, protocol_id: PublicId, skill_id: PublicId
    ) -> Optional[Handler]:
        """
        Fetch the handler by the pair protocol id and skill id.

        :param protocol_id: the protocol id
        :param skill_id: the skill id.
        :return: the handlers registered for the protocol_id and skill_id
        """
        if protocol_id not in self._items_by_protocol_and_skill.ids():
            return None
        protocols_by_skill_id = cast(
            PublicIdRegistry, self._items_by_protocol_and_skill.fetch(protocol_id)
        )
        if skill_id not in protocols_by_skill_id.ids():
            return None
        return protocols_by_skill_id.fetch(skill_id)
