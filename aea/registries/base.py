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
import logging
from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, Set, Tuple, TypeVar, cast

from aea.components.base import Component
from aea.configurations.base import (
    ComponentId,
    ComponentType,
    ProtocolId,
    PublicId,
    SkillId,
)
from aea.helpers.logging import WithLogger
from aea.skills.base import Behaviour, Handler, Model

logger = logging.getLogger(__name__)

Item = TypeVar("Item")
ItemId = TypeVar("ItemId")
SkillComponentType = TypeVar("SkillComponentType", Handler, Behaviour, Model)


class Registry(Generic[ItemId, Item], WithLogger, ABC):
    """This class implements an abstract registry."""

    def __init__(self):
        """Initialize the registry."""
        super().__init__(logger)

    @abstractmethod
    def register(self, item_id: ItemId, item: Item) -> None:
        """
        Register an item.

        :param item_id: the public id of the item.
        :param item: the item.
        :return: None
        :raises: ValueError if an item is already registered with that item id.
        """

    @abstractmethod
    def unregister(self, item_id: ItemId) -> None:
        """
        Unregister an item.

        :param item_id: the public id of the item.
        :return: None
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


class AgentComponentRegistry(Registry[ComponentId, Component]):
    """This class implements a simple dictionary-based registry for agent components."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        super().__init__()
        self._components_by_type: Dict[ComponentType, Dict[PublicId, Component]] = {}
        self._registered_keys: Set[ComponentId] = set()

    def register(
        self, component_id: ComponentId, component: Component
    ) -> None:  # pylint: disable=arguments-differ
        """
        Register a component.

        :param component_id: the id of the component.
        :param component: the component object.
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
        :return: None
        """
        self._components_by_type.setdefault(component_id.component_type, {})[
            component_id.public_id
        ] = component
        self._registered_keys.add(component_id)

    def _unregister(self, component_id: ComponentId) -> None:
        """
        Do the actual unregistration.

        :param component_id: the component id
        :return: None
        """
        item = self._components_by_type.get(component_id.component_type, {}).pop(
            component_id.public_id, None
        )
        self._registered_keys.discard(component_id)
        if item is not None:
            self.logger.debug(
                "Component '{}' has been removed.".format(item.component_id)
            )

    def unregister(
        self, component_id: ComponentId
    ) -> None:  # pylint: disable=arguments-differ
        """
        Unregister a component.

        :param component_id: the ComponentId
        """
        if component_id not in self._registered_keys:
            raise ValueError(
                "No item registered with item id '{}'".format(component_id)
            )
        self._unregister(component_id)

    def fetch(
        self, component_id: ComponentId
    ) -> Optional[Component]:  # pylint: disable=arguments-differ
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

        :return the list of registered components.
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
        :return the list of registered components of a given type.
        """
        return list(self._components_by_type.get(component_type, {}).values())

    def setup(self) -> None:
        """
        Set up the registry.

        :return: None
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        self._components_by_type = {}
        self._registered_keys = set()


class ComponentRegistry(
    Registry[Tuple[SkillId, str], SkillComponentType], Generic[SkillComponentType]
):
    """This class implements a generic registry for skill components."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        super().__init__()
        self._items = {}  # type: Dict[SkillId, Dict[str, SkillComponentType]]

    def register(self, item_id: Tuple[SkillId, str], item: SkillComponentType) -> None:
        """
        Register a item.

        :param item_id: a pair (skill id, item name).
        :param item: the item to register.
        :return: None
        :raises: ValueError if an item is already registered with that item id.
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        if item_name in self._items.get(skill_id, {}).keys():
            raise ValueError(
                "Item already registered with skill id '{}' and name '{}'".format(
                    skill_id, item_name
                )
            )
        self._items.setdefault(skill_id, {})[item_name] = item

    def unregister(self, item_id: Tuple[SkillId, str]) -> None:
        """
        Unregister a item.

        :param item_id: a pair (skill id, item name).
        :return: None
        :raises: ValueError if no item registered with that item id.
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        name_to_item = self._items.get(skill_id, {})
        if item_name not in name_to_item:
            raise ValueError(
                "No item registered with component id '{}'".format(item_id)
            )
        self.logger.debug("Unregistering item with id {}".format(item_id))
        name_to_item.pop(item_name)

        if len(name_to_item) == 0:
            self._items.pop(skill_id, None)

    def fetch(self, item_id: Tuple[SkillId, str]) -> Optional[SkillComponentType]:
        """
        Fetch an item.

        :param item_id: the public id of the item.
        :return: the Item
        """
        skill_id = item_id[0]
        item_name = item_id[1]
        return self._items.get(skill_id, {}).get(item_name, None)

    def fetch_by_skill(self, skill_id: SkillId) -> List[Item]:
        """Fetch all the items of a given skill."""
        return [*self._items.get(skill_id, {}).values()]

    def fetch_all(self) -> List[SkillComponentType]:
        """Fetch all the items."""
        return [
            item for skill_id, items in self._items.items() for item in items.values()
        ]

    def unregister_by_skill(self, skill_id: SkillId) -> None:
        """Unregister all the components by skill."""
        if skill_id not in self._items:
            raise ValueError(
                "No component of skill {} present in the registry.".format(skill_id)
            )
        self._items.pop(skill_id, None)

    def setup(self) -> None:
        """
        Set up the items in the registry.

        :return: None
        """
        for item in self.fetch_all():
            if item.context.is_active:
                self.logger.debug(
                    "Calling setup() of component {} of skill {}".format(
                        item.name, item.skill_id
                    )
                )
                item.setup()
            else:
                self.logger.debug(
                    "Ignoring setup() of component {} of skill {}, because the skill is not active.".format(
                        item.name, item.skill_id
                    )
                )

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for skill_id, items in self._items.items():
            for _, item in items.items():
                try:
                    item.teardown()
                except Exception as e:  # pragma: nocover # pylint: disable=broad-except
                    self.logger.warning(
                        "An error occurred while tearing down item {}/{}: {}".format(
                            skill_id, type(item).__name__, str(e)
                        )
                    )


class HandlerRegistry(ComponentRegistry[Handler]):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        super().__init__()
        self._items_by_protocol_and_skill = (
            {}
        )  # type: Dict[ProtocolId, Dict[SkillId, Handler]]

    def register(self, item_id: Tuple[SkillId, str], item: Handler) -> None:
        """
        Register a handler.

        :param item_id: the item id.
        :param item: the handler.
        :return: None
        :raises ValueError: if the protocol is None, or an item with pair (skill_id, protocol_id_ already exists.
        """
        super().register(item_id, item)

        skill_id = item_id[0]

        protocol_id = item.SUPPORTED_PROTOCOL
        if protocol_id is None:
            super().unregister(item_id)
            raise ValueError(
                "Please specify a supported protocol for handler class '{}'".format(
                    item.__class__.__name__
                )
            )

        protocol_handlers_by_skill = self._items_by_protocol_and_skill.get(
            protocol_id, {}
        )
        if skill_id in protocol_handlers_by_skill:
            # clean up previous modifications done by super().register
            super().unregister(item_id)
            raise ValueError(
                "A handler already registered with pair of protocol id {} and skill id {}".format(
                    protocol_id, skill_id
                )
            )

        self._items_by_protocol_and_skill.setdefault(protocol_id, {})[skill_id] = item

    def unregister(self, item_id: Tuple[SkillId, str]) -> None:
        """
        Unregister a item.

        :param item_id: a pair (skill id, item name).
        :return: None
        :raises: ValueError if no item is registered with that item id.
        """
        # remove from main index
        skill_id = item_id[0]
        item_name = item_id[1]
        name_to_item = self._items.get(skill_id, {})
        if item_name not in name_to_item:
            raise ValueError(
                "No item registered with component id '{}'".format(item_id)
            )
        self.logger.debug(  # pylint: disable=no-member
            "Unregistering item with id {}".format(item_id)
        )
        handler = name_to_item.pop(item_name)

        if len(name_to_item) == 0:
            self._items.pop(skill_id, None)

        # remove from index by protocol and skill
        protocol_id = cast(ProtocolId, handler.SUPPORTED_PROTOCOL)
        protocol_handlers_by_skill = self._items_by_protocol_and_skill.get(
            protocol_id, {}
        )
        protocol_handlers_by_skill.pop(skill_id, None)
        if len(protocol_handlers_by_skill) == 0:
            self._items_by_protocol_and_skill.pop(protocol_id, None)

    def unregister_by_skill(self, skill_id: SkillId) -> None:
        """Unregister all the components by skill."""
        # unregister from the main index.
        if skill_id not in self._items:
            raise ValueError(
                "No component of skill {} present in the registry.".format(skill_id)
            )
        handlers = self._items.pop(skill_id).values()

        # unregister from the protocol-skill index
        for handler in handlers:
            protocol_id = cast(ProtocolId, handler.SUPPORTED_PROTOCOL)
            self._items_by_protocol_and_skill.get(protocol_id, {}).pop(skill_id, None)

    def fetch_by_protocol(self, protocol_id: ProtocolId) -> List[Handler]:
        """
        Fetch the handler by the pair protocol id and skill id.

        :param protocol_id: the protocol id
        :return: the handlers registered for the protocol_id and skill_id
        """
        protocol_handlers_by_skill = self._items_by_protocol_and_skill.get(
            protocol_id, {}
        )
        handlers = [
            protocol_handlers_by_skill[skill_id]
            for skill_id in protocol_handlers_by_skill
        ]
        return handlers

    def fetch_by_protocol_and_skill(
        self, protocol_id: ProtocolId, skill_id: SkillId
    ) -> Optional[Handler]:
        """
        Fetch the handler by the pair protocol id and skill id.

        :param protocol_id: the protocol id
        :param skill_id: the skill id.
        :return: the handlers registered for the protocol_id and skill_id
        """
        return self._items_by_protocol_and_skill.get(protocol_id, {}).get(
            skill_id, None
        )
