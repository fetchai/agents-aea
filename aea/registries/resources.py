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
import pprint
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, TypeVar, Union

from aea.configurations.base import (
    AgentConfig,
    ConfigurationType,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    PublicId,
    SkillId,
)
from aea.configurations.loader import ConfigLoader
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
from aea.skills.base import AgentContext, Behaviour, Handler, Model, Skill
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

    def __init__(self, directory: Optional[Union[str, os.PathLike]] = None):
        """
        Instantiate the resources.

        :param directory: the path to the directory which contains the resources
             (skills, connections and protocols)
        """
        self._directory = (
            str(Path(directory).absolute())
            if directory is not None
            else str(Path(".").absolute())
        )
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

    @property
    def directory(self) -> str:
        """Get the directory."""
        return self._directory

    def _load_agent_config(self) -> AgentConfig:
        """Load the agent configuration."""
        config_loader = ConfigLoader.from_configuration_type(ConfigurationType.AGENT)
        agent_config = config_loader.load(
            open(os.path.join(self.directory, DEFAULT_AEA_CONFIG_FILE))
        )
        return agent_config

    def load(self, agent_context: AgentContext) -> None:
        """
        Load all the resources.

        Performs the following:

        - loads the agent configuration
        - populates the resources with all protocols in the directory
          and referenced in the configuration
        - populates the resources with all skills in the directory
          and referenced in the configuration

        :param agent_context: the agent context
        """
        agent_configuration = self._load_agent_config()
        self._contract_registry.populate(
            self.directory, allowed_contracts=agent_configuration.contracts
        )
        self._protocol_registry.populate(
            self.directory, allowed_protocols=agent_configuration.protocols
        )
        self._populate_skills(
            self.directory, agent_context, allowed_skills=agent_configuration.skills
        )

    def _populate_skills(
        self,
        directory: str,
        agent_context: AgentContext,
        allowed_skills: Optional[Set[PublicId]] = None,
    ) -> None:
        """
        Populate skills.

        Processes all allowed_skills in the directory and calls add_skill() with them.

        :param directory: the agent's resources directory.
        :param agent_context: the agent's context object
        :param allowed_skills: an optional set of allowed skills (public ids).
                               If None, every skill is allowed.
        :return: None
        """
        skill_directory_paths = set()  # type: ignore

        # find all skill directories from vendor/*/skills
        skill_directory_paths.update(Path(directory, "vendor").glob("./*/skills/*/"))
        # find all skill directories from skills/
        skill_directory_paths.update(Path(directory, "skills").glob("./*/"))

        skills_packages_paths = list(
            filter(
                lambda x: PACKAGE_NAME_REGEX.match(str(x.name)) and x.is_dir(),
                skill_directory_paths,
            )
        )  # type: ignore
        logger.debug(
            "Found the following skill packages: {}".format(
                pprint.pformat(map(str, skills_packages_paths))
            )
        )
        for skill_directory in skills_packages_paths:
            logger.debug(
                "Processing the following skill directory: '{}".format(skill_directory)
            )
            try:
                skill_loader = ConfigLoader.from_configuration_type(
                    ConfigurationType.SKILL
                )
                skill_config = skill_loader.load(
                    open(skill_directory / DEFAULT_SKILL_CONFIG_FILE)
                )
                if (
                    allowed_skills is not None
                    and skill_config.public_id not in allowed_skills
                ):
                    logger.debug(
                        "Ignoring skill {}, not declared in the configuration file.".format(
                            skill_config.public_id
                        )
                    )
                    continue
                else:
                    skill = Skill.from_dir(str(skill_directory), agent_context)
                    assert skill is not None
                    self.add_skill(skill)
                    self.inject_contracts(skill)
            except Exception as e:
                logger.warning(
                    "A problem occurred while parsing the skill directory {}. Exception: {}".format(
                        skill_directory, str(e)
                    )
                )

    def add_protocol(self, protocol: Protocol) -> None:
        """
        Add a protocol to the set of resources.

        :param protocol: a protocol
        :return: None
        """
        self._protocol_registry.register(protocol.id, protocol)

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
