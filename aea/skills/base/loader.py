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

"""Implementation of the parser for configuration file."""
import inspect
import json
import os
from typing import TextIO

import yaml
from jsonschema import validate  # type: ignore

from aea.skills.base.config import ConnectionConfig, AgentConfig, SkillConfig, HandlerConfig, BehaviourConfig, \
    TaskConfig

_CUR_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))
_SCHEMAS_DIR = os.path.join(_CUR_DIR, "schemas")


class ConfigLoader:
    """This class implement parsing, serialization and validation functionalities for the 'aea' configuration files."""

    def __init__(self):
        """Initialize the parser for configuration files."""
        self._aea_config_schema = json.load(open(os.path.join(_SCHEMAS_DIR, "aea-config_schema.json")))
        self._skill_config_schema = json.load(open(os.path.join(_SCHEMAS_DIR, "skill-config_schema.json")))

    def load_agent_configuration(self, fp: TextIO) -> AgentConfig:
        """
        Load an agent configuration file.

        :param fp: the file pointer to the configuration file
        :return: the Agent Configuration object.
        """
        agent_configuration_file = yaml.safe_load(fp)
        validate(instance=agent_configuration_file, schema=self._aea_config_schema)

        agent_config = AgentConfig()
        agent_config.agent_name = agent_configuration_file.get("agent_name")
        agent_config.aea_version = agent_configuration_file.get("aea_version")

        # process connections
        for c in agent_configuration_file.get("connections"):
            connection_obj = c["connection"]
            connection_config = ConnectionConfig(name=connection_obj["name"], type=connection_obj["type"],
                                                 **connection_obj["config"])
            agent_config.connections.create(connection_config.name, connection_config)

        # process protocols
        for p in agent_configuration_file.get("protocols"):
            agent_config.protocols.add(p)

        # process skills
        for s in agent_configuration_file.get("skills"):
            agent_config.skills.add(s)

        # set default configuration
        default_connection_name = agent_configuration_file.get("default_connection", None)
        if default_connection_name is not None:
            default_connection_config = agent_config.connections.read(default_connection_name)
            if default_connection_config is not None:
                agent_config.set_default_connection(default_connection_config)

        return agent_config

    def dump_agent_configuration(self, agent_config: AgentConfig, fp: TextIO) -> None:
        """Dump an agent configuration.

        :param agent_config: the agent configuration to be dumped.
        :param fp: the file pointer to the configuration file
        :return: None
        """
        result = dict()
        result["agent_name"] = agent_config.agent_name
        result["aea_version"] = agent_config.aea_version
        result["default_connection"] = agent_config.default_connection.name

        result["connections"] = []  # type: ignore
        for _, c in agent_config.connections.read_all():
            connection_obj = dict(
                name=c.name,
                type=c.type,
                config=c.config
            )
            result["connections"].append({"connection": connection_obj})  # type: ignore

        result["protocols"] = list(agent_config.protocols)  # type: ignore
        result["skills"] = list(agent_config.skills)  # type: ignore

        validate(instance=result, schema=self._aea_config_schema)
        yaml.safe_dump(result, fp)

    def load_skill_configuration(self, fp: TextIO) -> SkillConfig:
        """Load the skill configuration."""
        configuration_file = yaml.safe_load(fp)
        validate(instance=configuration_file, schema=self._skill_config_schema)

        skill_config = SkillConfig()
        skill_config.name = configuration_file["name"]
        skill_config.authors = configuration_file["authors"]
        skill_config.version = configuration_file["version"]
        skill_config.license = configuration_file["license"]
        skill_config.url = configuration_file["url"]
        skill_config.protocol = configuration_file["protocol"]

        # process handler
        skill_config.handler = HandlerConfig(
            class_name=configuration_file["handler"]["class_name"],
            args=configuration_file["handler"]["args"]
        )

        for b in configuration_file["behaviours"]:
            behaviour_obj = b["behaviour"]
            behaviour_config = BehaviourConfig(class_name=behaviour_obj["class_name"],
                                               args=behaviour_obj["args"])
            skill_config.behaviours.create(behaviour_config.class_name, behaviour_config)

        for t in configuration_file["tasks"]:
            task_obj = t["task"]
            task_config = TaskConfig(class_name=task_obj["class_name"],
                                     args=task_obj["args"])
            skill_config.tasks.create(task_config.class_name, task_config)

        return skill_config

    def dump_skill_configuration(self, skill_config: SkillConfig, fp: TextIO) -> None:
        """Dump a skill configuration."""
        result = {}
        result["name"] = skill_config.name
        result["authors"] = skill_config.authors
        result["version"] = skill_config.version
        result["license"] = skill_config.license
        result["url"] = skill_config.url
        result["protocol"] = skill_config.protocol

        result["handler"] = {  # type: ignore
            "class_name": skill_config.handler.class_name,
            "args": skill_config.handler.args
        }

        result["behaviours"] = []  # type: ignore
        for _, b in skill_config.behaviours.read_all():
            behaviour_obj = dict(
                class_name=b.class_name,
                args=b.args
            )
            result["behaviours"].append({"behaviour": behaviour_obj})  # type: ignore

        result["tasks"] = []  # type: ignore
        for _, t in skill_config.tasks.read_all():
            task_obj = dict(
                class_name=t.class_name,
                args=t.args
            )
            result["tasks"].append({"task": task_obj})  # type: ignore

        validate(instance=result, schema=self._skill_config_schema)
        yaml.safe_dump(result, fp)
