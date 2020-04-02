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

"""This module contains the resources class."""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple, TypeVar, Union, cast

from aea.configurations.base import ComponentType, ContractId, PublicId, SkillId
from aea.configurations.components import Component
from aea.contracts.base import Contract
from aea.protocols.base import Protocol
from aea.registries.base import (
    ComponentRegistry,
    ContractRegistry,
    HandlerRegistry,
    ProtocolId,
    ProtocolRegistry,
    Registry,
)
from aea.skills.base import Behaviour, Handler, Model, Skill
from aea.skills.tasks import Task


logger = logging.getLogger(__name__)

PACKAGE_NAME_REGEX = re.compile(
    "^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
)
INTERNAL_PROTOCOL_ID = PublicId.from_str("fetchai/internal:0.1.0")
DECISION_MAKER = "decision_maker"

Item = TypeVar("Item")
ItemId = TypeVar("ItemId")
ComponentId = Tuple[SkillId, str]
SkillComponentType = TypeVar("SkillComponentType", Handler, Behaviour, Task, Model)


class Resources:
    """This class implements the object that holds the resources of an AEA."""

    # TODO the 'directory' argument to be removed
    def __init__(self, directory: Optional[Union[str, os.PathLike]] = None):
        """
        Instantiate the resources.

        :param directory: the path to the directory which contains the resources
             (skills, connections and protocols)
        """
        self._contract_registry = ContractRegistry()
        self._protocol_registry = ProtocolRegistry()
        self._handler_registry = HandlerRegistry()
        self._behaviour_registry = ComponentRegistry[Behaviour]()
        self._model_registry = ComponentRegistry[Model]()
        self._skills = dict()  # type: Dict[SkillId, Skill]

        self._registries = [
            self._contract_registry,
            self._protocol_registry,
            self._handler_registry,
            self._behaviour_registry,
            self._model_registry,
        ]  # type: List[Registry]

    def add_component(self, component: Component):
        """Add a component to resources."""
        if component.component_type == ComponentType.PROTOCOL:
            self.add_protocol(cast(Protocol, component))
        elif component.component_type == ComponentType.SKILL:
            self.add_skill(cast(Skill, component))
        elif component.component_type == ComponentType.CONTRACT:
            self.add_contract(cast(Contract, component))
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
        :return: None
        """
        self._protocol_registry.register(protocol.public_id, protocol)

    def get_protocol(self, protocol_id: ProtocolId) -> Optional[Protocol]:
        """
        Get protocol for given protocol id.

        :param protocol_id: the protocol id
        :return: a matching protocol, if present, else None
        """
        protocol = self._protocol_registry.fetch(protocol_id)
        return protocol

    def get_all_protocols(self) -> List[Protocol]:
        """
        Get the list of all the protocols.

        :return: the list of protocols.
        """
        protocols = self._protocol_registry.fetch_all()
        return protocols

    def remove_protocol(self, protocol_id: ProtocolId) -> None:
        """
        Remove a protocol from the set of resources.

        :param protocol_id: the protocol id for the protocol to be removed.
        :return: None
        """
        self._protocol_registry.unregister(protocol_id)

    def add_contract(self, contract: Contract) -> None:
        """
        Add a contract to the set of resources.

        :param contract: a contract
        :return: None
        """
        self._contract_registry.register(contract.id, contract)

    def get_contract(self, contract_id: ContractId) -> Optional[Contract]:
        """
        Get contract for given contract id.

        :param contract_id: the contract id
        :return: a matching contract, if present, else None
        """
        contract = self._contract_registry.fetch(contract_id)
        return contract

    def get_all_contracts(self) -> List[Contract]:
        """
        Get the list of all the contracts.

        :return: the list of contracts.
        """
        contracts = self._contract_registry.fetch_all()
        return contracts

    def remove_contract(self, contract_id: ContractId) -> None:
        """
        Remove a contract from the set of resources.

        :param contract_id: the contract id for the contract to be removed.
        :return: None
        """
        self._contract_registry.unregister(contract_id)

    def add_skill(self, skill: Skill) -> None:
        """
        Add a skill to the set of resources.

        :param skill: a skill
        :return: None
        """
        skill_id = skill.config.public_id
        self._skills[skill_id] = skill
        if skill.handlers is not None:
            for handler in skill.handlers.values():
                self._handler_registry.register((skill_id, handler.name), handler)
        if skill.behaviours is not None:
            for behaviour in skill.behaviours.values():
                self._behaviour_registry.register((skill_id, behaviour.name), behaviour)
        if skill.models is not None:
            for model in skill.models.values():
                self._model_registry.register((skill_id, model.name), model)
        self.inject_contracts(skill)

    def inject_contracts(self, skill: Skill) -> None:
        if skill.config.contracts is not None:
            # check all contracts are present
            contracts = {}  # type: Dict[str, Contract]
            for contract_id in skill.config.contracts:
                contract = self._contract_registry.fetch(contract_id)
                if contract is None:
                    raise ValueError(
                        "Missing contract for contract id {}".format(contract_id)
                    )
                contracts[contract_id.name] = contract
            skill.inject_contracts(contracts)

    def get_skill(self, skill_id: SkillId) -> Optional[Skill]:
        """
        Get the skill for a given skill id.

        :param skill_id: the skill id
        :return: a matching skill, if present, else None
        """
        return self._skills.get(skill_id, None)

    def get_all_skills(self) -> List[Skill]:
        """
        Get the list of all the skills.

        :return: the list of skills.
        """
        return list(self._skills.values())

    def remove_skill(self, skill_id: SkillId) -> None:
        """
        Remove a skill from the set of resources.

        :param skill_id: the skill id for the skill to be removed.
        :return: None
        """
        self._skills.pop(skill_id, None)
        try:
            self._handler_registry.unregister_by_skill(skill_id)
        except ValueError:
            pass

        try:
            self._behaviour_registry.unregister_by_skill(skill_id)
        except ValueError:
            pass

    def get_handler(
        self, protocol_id: ProtocolId, skill_id: SkillId
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

    def get_handlers(self, protocol_id: ProtocolId) -> List[Handler]:
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
        self, skill_id: SkillId, behaviour_name: str
    ) -> Optional[Behaviour]:
        """
        Get a specific behaviours for a given skill.

        :param skill_id: the skill id
        :param behaviour_name: the behaviour name
        :return: the behaviour, if it is present, else None
        """
        behaviour = self._behaviour_registry.fetch((skill_id, behaviour_name))
        return behaviour

    def get_behaviours(self, skill_id: SkillId) -> List[Behaviour]:
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

        :return: None
        """
        for r in self._registries:
            r.setup()

    def teardown(self) -> None:
        """
        Teardown the resources.

        Calls teardown on all resources.

        :return: None
        """
        for r in self._registries:
            r.teardown()
