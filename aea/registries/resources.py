# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""This module contains the resources class."""
from contextlib import suppress
from typing import Dict, List, Optional, cast

from aea.components.base import Component
from aea.configurations.base import ComponentId, ComponentType, PublicId
from aea.connections.base import Connection
from aea.contracts.base import Contract
from aea.protocols.base import Protocol
from aea.registries.base import (
    AgentComponentRegistry,
    ComponentRegistry,
    HandlerRegistry,
    Registry,
)
from aea.skills.base import Behaviour, Handler, Model, Skill


class Resources:
    """This class implements the object that holds the resources of an AEA."""

    __slots__ = (
        "_agent_name",
        "_component_registry",
        "_specification_to_protocol_id",
        "_handler_registry",
        "_behaviour_registry",
        "_model_registry",
        "_registries",
    )

    def __init__(self, agent_name: str = "standalone") -> None:
        """
        Instantiate the resources.

        :param agent_name: the name of the agent
        """
        self._agent_name = agent_name
        self._component_registry = AgentComponentRegistry(agent_name=agent_name)
        self._specification_to_protocol_id: Dict[PublicId, PublicId] = {}
        self._handler_registry = HandlerRegistry(agent_name=agent_name)
        self._behaviour_registry = ComponentRegistry[Behaviour](agent_name=agent_name)
        self._model_registry = ComponentRegistry[Model](agent_name=agent_name)

        self._registries = [
            self._component_registry,
            self._handler_registry,
            self._behaviour_registry,
            self._model_registry,
        ]  # type: List[Registry]

    @property
    def agent_name(self) -> str:
        """Get the agent name."""
        return self._agent_name

    @property
    def component_registry(self) -> AgentComponentRegistry:
        """Get the agent component registry."""
        return self._component_registry

    @property
    def behaviour_registry(self) -> ComponentRegistry[Behaviour]:
        """Get the behaviour registry."""
        return self._behaviour_registry

    @property
    def handler_registry(self) -> HandlerRegistry:
        """Get the handler registry."""
        return self._handler_registry

    @property
    def model_registry(self) -> ComponentRegistry[Model]:
        """Get the model registry."""
        return self._model_registry

    def add_component(self, component: Component) -> None:
        """Add a component to resources."""
        if component.component_type == ComponentType.PROTOCOL:
            self.add_protocol(cast(Protocol, component))
        elif component.component_type == ComponentType.SKILL:
            self.add_skill(cast(Skill, component))
        elif component.component_type == ComponentType.CONTRACT:
            self.add_contract(cast(Contract, component))
        elif component.component_type == ComponentType.CONNECTION:
            self.add_connection(cast(Connection, component))
        else:
            raise ValueError(
                "Component type {} not supported.".format(
                    component.component_type.value
                )
            )

    def add_protocol(self, protocol: Protocol) -> None:
        """
        Add a protocol to the set of resources.

        :param protocol: a protocol
        """
        self._component_registry.register(protocol.component_id, protocol)
        self._specification_to_protocol_id[
            protocol.protocol_specification_id
        ] = protocol.public_id

    def get_protocol(self, protocol_id: PublicId) -> Optional[Protocol]:
        """
        Get protocol for given protocol id.

        :param protocol_id: the protocol id
        :return: a matching protocol, if present, else None
        """
        protocol = self._component_registry.fetch(
            ComponentId(ComponentType.PROTOCOL, protocol_id)
        )
        return cast(Protocol, protocol)

    def get_protocol_by_specification_id(
        self, protocol_specification_id: PublicId
    ) -> Optional[Protocol]:
        """
        Get protocol for given protocol_specification_id.

        :param protocol_specification_id: the protocol id
        :return: a matching protocol, if present, else None
        """
        protocol_id = self._specification_to_protocol_id.get(
            protocol_specification_id, None
        )

        if protocol_id is None:
            return None

        return self.get_protocol(protocol_id)

    def get_all_protocols(self) -> List[Protocol]:
        """
        Get the list of all the protocols.

        :return: the list of protocols.
        """
        protocols = self._component_registry.fetch_by_type(ComponentType.PROTOCOL)
        return cast(List[Protocol], protocols)

    def remove_protocol(self, protocol_id: PublicId) -> None:
        """
        Remove a protocol from the set of resources.

        :param protocol_id: the protocol id for the protocol to be removed.
        """
        protocol = cast(
            Optional[Protocol],
            self._component_registry.unregister(
                ComponentId(ComponentType.PROTOCOL, protocol_id)
            ),
        )
        if protocol is not None:
            self._specification_to_protocol_id.pop(protocol.protocol_specification_id)

    def add_contract(self, contract: Contract) -> None:
        """
        Add a contract to the set of resources.

        :param contract: a contract
        """
        self._component_registry.register(contract.component_id, contract)

    def get_contract(self, contract_id: PublicId) -> Optional[Contract]:
        """
        Get contract for given contract id.

        :param contract_id: the contract id
        :return: a matching contract, if present, else None
        """
        contract = self._component_registry.fetch(
            ComponentId(ComponentType.CONTRACT, contract_id)
        )
        return cast(Contract, contract)

    def get_all_contracts(self) -> List[Contract]:
        """
        Get the list of all the contracts.

        :return: the list of contracts.
        """
        contracts = self._component_registry.fetch_by_type(ComponentType.CONTRACT)
        return cast(List[Contract], contracts)

    def remove_contract(self, contract_id: PublicId) -> None:
        """
        Remove a contract from the set of resources.

        :param contract_id: the contract id for the contract to be removed.
        """
        self._component_registry.unregister(
            ComponentId(ComponentType.CONTRACT, contract_id)
        )

    def add_connection(self, connection: Connection) -> None:
        """
        Add a connection to the set of resources.

        :param connection: a connection
        """
        self._component_registry.register(connection.component_id, connection)

    def get_connection(self, connection_id: PublicId) -> Optional[Connection]:
        """
        Get connection for given connection id.

        :param connection_id: the connection id
        :return: a matching connection, if present, else None
        """
        connection = self._component_registry.fetch(
            ComponentId(ComponentType.CONNECTION, connection_id)
        )
        return cast(Connection, connection)

    def get_all_connections(self) -> List[Connection]:
        """
        Get the list of all the connections.

        :return: the list of connections.
        """
        connections = self._component_registry.fetch_by_type(ComponentType.CONNECTION)
        return cast(List[Connection], connections)

    def remove_connection(self, connection_id: PublicId) -> None:
        """
        Remove a connection from the set of resources.

        :param connection_id: the connection id for the connection to be removed.
        """
        self._component_registry.unregister(
            ComponentId(ComponentType.CONNECTION, connection_id)
        )

    def add_skill(self, skill: Skill) -> None:
        """
        Add a skill to the set of resources.

        :param skill: a skill
        """
        self._component_registry.register(skill.component_id, skill)
        if skill.handlers is not None:
            for handler in skill.handlers.values():
                self._handler_registry.register(
                    (skill.public_id, handler.name), handler
                )
        if skill.behaviours is not None:
            for behaviour in skill.behaviours.values():
                self._behaviour_registry.register(
                    (skill.public_id, behaviour.name), behaviour
                )
        if skill.models is not None:
            for model in skill.models.values():
                self._model_registry.register((skill.public_id, model.name), model)

    def get_skill(self, skill_id: PublicId) -> Optional[Skill]:
        """
        Get the skill for a given skill id.

        :param skill_id: the skill id
        :return: a matching skill, if present, else None
        """
        skill = self._component_registry.fetch(
            ComponentId(ComponentType.SKILL, skill_id)
        )
        return cast(Skill, skill)

    def get_all_skills(self) -> List[Skill]:
        """
        Get the list of all the skills.

        :return: the list of skills.
        """
        skills = self._component_registry.fetch_by_type(ComponentType.SKILL)
        return cast(List[Skill], skills)

    def remove_skill(self, skill_id: PublicId) -> None:
        """
        Remove a skill from the set of resources.

        :param skill_id: the skill id for the skill to be removed.
        """
        self._component_registry.unregister(ComponentId(ComponentType.SKILL, skill_id))
        with suppress(ValueError):
            self._handler_registry.unregister_by_skill(skill_id)
        with suppress(ValueError):
            self._behaviour_registry.unregister_by_skill(skill_id)
        with suppress(ValueError):
            self._model_registry.unregister_by_skill(skill_id)

    def get_handler(
        self, protocol_id: PublicId, skill_id: PublicId
    ) -> Optional[Handler]:
        """
        Get a specific handler.

        :param protocol_id: the protocol id the handler is handling
        :param skill_id: the skill id of the handler's skill
        :return: the handler
        """
        handler = self._handler_registry.fetch_by_protocol_and_skill(
            protocol_id, skill_id
        )
        return handler

    def get_handlers(self, protocol_id: PublicId) -> List[Handler]:
        """
        Get all handlers for a given protocol.

        :param protocol_id: the protocol id the handler is handling
        :return: the list of handlers matching the protocol
        """
        handlers = self._handler_registry.fetch_by_protocol(protocol_id)
        return handlers

    def get_all_handlers(self) -> List[Handler]:
        """
        Get all handlers from all skills.

        :return: the list of handlers
        """
        handlers = self._handler_registry.fetch_all()
        return handlers

    def get_behaviour(
        self, skill_id: PublicId, behaviour_name: str
    ) -> Optional[Behaviour]:
        """
        Get a specific behaviours for a given skill.

        :param skill_id: the skill id
        :param behaviour_name: the behaviour name
        :return: the behaviour, if it is present, else None
        """
        behaviour = self._behaviour_registry.fetch((skill_id, behaviour_name))
        return behaviour

    def get_behaviours(self, skill_id: PublicId) -> List[Behaviour]:
        """
        Get all behaviours for a given skill.

        :param skill_id: the skill id
        :return: the list of behaviours of the skill
        """
        behaviours = self._behaviour_registry.fetch_by_skill(
            skill_id
        )  # type: List[Behaviour]
        return behaviours

    def get_all_behaviours(self) -> List[Behaviour]:
        """
        Get all behaviours from all skills.

        :return: the list of all behaviours
        """
        behaviours = self._behaviour_registry.fetch_all()
        return behaviours

    def setup(self) -> None:
        """
        Set up the resources.

        Calls setup on all resources.
        """
        for r in self._registries:
            r.setup()

    def teardown(self) -> None:
        """
        Teardown the resources.

        Calls teardown on all resources.
        """
        for r in self._registries:
            r.teardown()
