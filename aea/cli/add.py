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

"""Implementation of the 'aea add' subcommand."""

import importlib.util
import os
import shutil
from pathlib import Path
from typing import cast

import click
from click import pass_context
from jsonschema import ValidationError

from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.skills.base import DEFAULT_SKILL_CONFIG_FILE, DEFAULT_CONNECTION_CONFIG_FILE


@click.group()
@pass_ctx
def add(ctx: Context):
    """Add a resource to the agent."""
    _try_to_load_agent_config(ctx)


@add.command()
@click.argument('dirpath', type=str, required=True)
@pass_ctx
def connection(ctx: Context, dirpath):
    """Add a connection to the configuration file."""

    # check that the provided path points to a proper connection directory -> look for connection.yaml file.
    connection_configuration_filepath = Path(os.path.join(dirpath, DEFAULT_CONNECTION_CONFIG_FILE))
    if not connection_configuration_filepath.exists():
        logger.error("Path '{}' does not exist.".format(connection_configuration_filepath))
        exit(-1)
        return

    # try to load the connection configuration file
    try:
        connection_configuration = ctx.connection_loader.load(open(str(connection_configuration_filepath)))
    except ValidationError as e:
        logger.error("Connection configuration file not valid: {}".format(str(e)))
        exit(-1)
        return

    # check if we already have a connection with the same name
    logger.debug("Connection already supported by the agent: {}".format(ctx.agent_config.connections))
    connection_name = connection_configuration.name
    if connection_name in ctx.agent_config.connections:
        logger.error("A connection with name '{}' already exists. Aborting...".format(connection_name))
        exit(-1)
        return

    agent_name = ctx.agent_config.agent_name
    logger.debug("Adding connection {connection_name} to the agent {agent_name}..."
                 .format(agent_name=agent_name, connection_name=connection_name))

    # copy the connection package into the agent's supported connections.
    dirpath = str(Path(dirpath).absolute())
    src = dirpath
    dest = os.path.join(ctx.cwd, "connections", connection_name)
    logger.info("Copying connection modules. src={} dst={}".format(src, dest))
    try:
        shutil.copytree(src, dest)
    except Exception as e:
        logger.error(e)
        exit(-1)

    # make the 'connections' folder a Python package.
    connections_init_module = os.path.join(ctx.cwd, "connections", "__init__.py")
    logger.debug("Creating {}".format(connections_init_module))
    Path(connections_init_module).touch(exist_ok=True)

    # add the connections to the configurations.
    logger.debug("Registering the connection into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.connections.add(connection_name)
    ctx.agent_loader.dump(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))


@add.command()
@click.argument('protocol_name', type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_name):
    """Add a protocol to the agent."""
    agent_name = cast(str, ctx.agent_config.agent_name)
    logger.debug("Adding protocol {protocol_name} to the agent {agent_name}..."
                 .format(agent_name=agent_name, protocol_name=protocol_name))

    # find the supported protocols and check if the candidate protocol is supported.
    protocols_module_spec = importlib.util.find_spec("aea.protocols")
    assert protocols_module_spec is not None, "Protocols module spec is None."
    _protocols_submodules = protocols_module_spec.loader.contents()  # type: ignore
    _protocols_submodules = filter(lambda x: not x.startswith("__") and x != "base", _protocols_submodules)
    aea_supported_protocol = set(_protocols_submodules)
    logger.debug("Supported protocols: {}".format(aea_supported_protocol))
    if protocol_name not in aea_supported_protocol:
        logger.error("Protocol '{}' not supported. Aborting...".format(protocol_name))
        return

    # check if we already have a protocol with the same name
    logger.debug("Protocols already supported by the agent: {}".format(ctx.agent_config.protocols))
    if protocol_name in ctx.agent_config.protocols:
        logger.error("A protocol with name '{}' already exists. Aborting...".format(protocol_name))
        return

    # copy the protocol package into the agent's supported protocols.
    assert protocols_module_spec.submodule_search_locations is not None, "Submodule search locations is None."
    protocols_dir = protocols_module_spec.submodule_search_locations[0]
    src = os.path.join(protocols_dir, protocol_name)
    dest = os.path.join("protocols", protocol_name)
    logger.info("Copying protocol modules. src={} dst={}".format(src, dest))
    shutil.copytree(src, dest)

    # make the 'protocols' folder a Python package.
    logger.debug("Creating {}".format(os.path.join(agent_name, "protocols", "__init__.py")))
    Path(os.path.join("protocols", "__init__.py")).touch(exist_ok=True)

    # add the protocol to the configurations.
    logger.debug("Registering the protocol into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.protocols.add(protocol_name)
    ctx.agent_loader.dump(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))


@add.command()
@click.argument('skill_name', type=str, required=True)
@click.argument('dirpath', type=str, required=True)
@pass_context
def skill(click_context, skill_name, dirpath):
    """Add a skill to the agent."""
    ctx = cast(Context, click_context.obj)
    agent_name = ctx.agent_config.agent_name
    logger.debug("Adding skill {skill_name} to the agent {agent_name}..."
                 .format(agent_name=agent_name, skill_name=skill_name))

    # check if we already have a skill with the same name
    logger.debug("Skills already supported by the agent: {}".format(ctx.agent_config.skills))
    if skill_name in ctx.agent_config.skills:
        logger.error("A skill with name '{}' already exists. Aborting...".format(skill_name))
        exit(-1)
        return

    # check that the provided path points to a proper skill directory -> look for skill.yaml file.
    skill_configuration_filepath = Path(os.path.join(dirpath, DEFAULT_SKILL_CONFIG_FILE))
    if not skill_configuration_filepath.exists():
        logger.error("Path '{}' does not exist.".format(skill_configuration_filepath))
        exit(-1)
        return

    # try to load the skill configuration file
    try:
        skill_configuration = ctx.skill_loader.load(open(str(skill_configuration_filepath)))
    except ValidationError as e:
        logger.error("Skill configuration file not valid: {}".format(str(e)))
        exit(-1)
        return

    # copy the skill package into the agent's supported skills.
    dirpath = str(Path(dirpath).absolute())
    src = dirpath
    dest = os.path.join("skills", skill_name)
    logger.info("Copying skill modules. src={} dst={}".format(src, dest))
    try:
        shutil.copytree(src, dest)
    except Exception as e:
        logger.error(e)
        exit(-1)

    # make the 'skills' folder a Python package.
    skills_init_module = os.path.join("skills", "__init__.py")
    logger.debug("Creating {}".format(skills_init_module))
    Path(skills_init_module).touch(exist_ok=True)

    # check for not supported protocol, and add it.
    if skill_configuration.protocol not in ctx.agent_config.protocols:
        logger.info("Adding protocol '{}' to the agent...".format(skill_configuration.protocol))
        click_context.invoke(protocol, protocol_name=skill_configuration.protocol)

    # add the skill to the configurations.
    logger.debug("Registering the skill into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.skills.add(skill_name)
    ctx.agent_loader.dump(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))
