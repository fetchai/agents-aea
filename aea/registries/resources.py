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
from aea.protocols.base import Protocol
from aea.registries.base import ComponentRegistry, HandlerRegistry, ProtocolRegistry
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
    """This class implements the resources of an AEA."""

    def __init__(self, directory: Optional[Union[str, os.PathLike]] = None):
        """Instantiate the resources."""
        self._directory = (
            str(Path(directory).absolute())
            if directory is not None
            else str(Path(".").absolute())
        )
        self.protocol_registry = ProtocolRegistry()
        self.handler_registry = HandlerRegistry()
        self.behaviour_registry = ComponentRegistry[Behaviour]()
        self.model_registry = ComponentRegistry[Model]()
        self._skills = dict()  # type: Dict[SkillId, Skill]

        self._registries = [
            self.protocol_registry,
            self.handler_registry,
            self.behaviour_registry,
            self.model_registry,
        ]

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
        """Load all the resources."""
        agent_configuration = self._load_agent_config()
        self.protocol_registry.populate(
            self.directory, allowed_protocols=agent_configuration.protocols
        )
        self.populate_skills(
            self.directory, agent_context, allowed_skills=agent_configuration.skills
        )

    def populate_skills(
        self,
        directory: str,
        agent_context: AgentContext,
        allowed_skills: Optional[Set[PublicId]] = None,
    ) -> None:
        """
        Populate skills.

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
            except Exception as e:
                logger.warning(
                    "A problem occurred while parsing the skill directory {}. Exception: {}".format(
                        skill_directory, str(e)
                    )
                )

    def add_skill(self, skill: Skill):
        """Add a skill to the set of resources."""
        skill_id = skill.config.public_id
        self._skills[skill_id] = skill
        if skill.handlers is not None:
            for handler in skill.handlers.values():
                self.handler_registry.register((skill_id, handler.name), handler)
        if skill.behaviours is not None:
            for behaviour in skill.behaviours.values():
                self.behaviour_registry.register((skill_id, behaviour.name), behaviour)
        if skill.models is not None:
            for model in skill.models.values():
                self.model_registry.register((skill_id, model.name), model)

    def add_protocol(self, protocol: Protocol):
        """Add a protocol to the set of resources."""
        self.protocol_registry.register(protocol.id, protocol)

    def get_skill(self, skill_id: SkillId) -> Optional[Skill]:
        """Get the skill."""
        return self._skills.get(skill_id, None)

    def get_all_skills(self) -> List[Skill]:
        """
        Get the list of all the skills.

        :return: the list of skills.
        """
        return list(self._skills.values())

    def remove_skill(self, skill_id: SkillId):
        """Remove a skill from the set of resources."""
        self._skills.pop(skill_id, None)
        try:
            self.handler_registry.unregister_by_skill(skill_id)
        except ValueError:
            pass

        try:
            self.behaviour_registry.unregister_by_skill(skill_id)
        except ValueError:
            pass

    def setup(self):
        """
        Set up the resources.

        :return: None
        """
        for r in self._registries:
            r.setup()

    def teardown(self):
        """
        Teardown the resources.

        :return: None
        """
        for r in self._registries:
            r.teardown()
