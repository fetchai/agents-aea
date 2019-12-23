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

import os
import shutil
import sys
from pathlib import Path
from typing import cast

import click
from click import pass_context
from jsonschema import ValidationError

from aea import AEA_DIR
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config, PublicIdParameter
from aea.cli.registry.utils import fetch_package, split_public_id
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE, \
    DEFAULT_PROTOCOL_CONFIG_FILE


@click.group()
@click.option('--registry', is_flag=True, help="For adding from Registry.")
@pass_ctx
def add(ctx: Context, registry):
    """Add a resource to the agent."""
    if registry:
        ctx.set_config("is_registry", True)
    _try_to_load_agent_config(ctx)


def _find_connection_locally(ctx, connection_name, click_context):
    # check that the provided path points to a proper connection directory -> look for connection.yaml file.
    # first check in aea dir
    registry_path = ctx.agent_config.registry_path
    connection_configuration_filepath = Path(os.path.join(registry_path, "connections", connection_name, DEFAULT_CONNECTION_CONFIG_FILE))
    if not connection_configuration_filepath.exists():
        # then check in registry
        registry_path = AEA_DIR
        connection_configuration_filepath = Path(os.path.join(registry_path, "connections", connection_name, DEFAULT_CONNECTION_CONFIG_FILE))
        if not connection_configuration_filepath.exists():
            logger.error("Cannot find connection: '{}'.".format(connection_name))
            sys.exit(1)

    # try to load the connection configuration file
    try:
        connection_configuration = ctx.connection_loader.load(open(str(connection_configuration_filepath)))
        if connection_configuration.restricted_to_protocols != []:
            logger.info("Connection '{}' is restricted to the following protocols: {}".format(connection_name, connection_configuration.restricted_to_protocols))
    except ValidationError as e:
        logger.error("Connection configuration file not valid: {}".format(str(e)))
        sys.exit(1)

    # copy the connection package into the agent's supported connections.
    src = str(Path(os.path.join(registry_path, "connections", connection_name)).absolute())
    dest = os.path.join(ctx.cwd, "connections", connection_name)
    logger.debug("Copying connection modules. src={} dst={}".format(src, dest))
    try:
        shutil.copytree(src, dest)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

    # check for protocol dependencies not yet added, and add it.
    for protocol_name in connection_configuration.protocols:
        if protocol_name not in ctx.agent_config.protocols:
            logger.debug("Adding protocol '{}' to the agent...".format(protocol_name))
            click_context.invoke(protocol, protocol_name=protocol_name)


@add.command()
@click.argument(
    'connection_name', type=PublicIdParameter(), required=True
)
@pass_context
def connection(click_context, connection_name):
    """Add a connection to the configuration file."""
    ctx = cast(Context, click_context.obj)
    agent_name = ctx.agent_config.agent_name

    is_registry = ctx.config.get("is_registry")
    if is_registry:
        public_id = str(connection_name)
        connection_name = split_public_id(connection_name)[1]

    logger.info("Adding connection '{}' to the agent '{}'...".format(connection_name, agent_name))

    # check if we already have a connection with the same name
    logger.debug("Connections already supported by the agent: {}".format(ctx.agent_config.connections))
    if connection_name in ctx.agent_config.connections:
        logger.error("A connection with name '{}' already exists. Aborting...".format(connection_name))
        sys.exit(1)

    # find and add connection
    if is_registry:
        # fetch from Registry
        fetch_package('connection', public_id=public_id, cwd=ctx.cwd)
    else:
        _find_connection_locally(ctx, connection_name, click_context)

    # make the 'connections' folder a Python package.
    connections_init_module = os.path.join(ctx.cwd, "connections", "__init__.py")
    logger.debug("Creating {}".format(connections_init_module))
    Path(connections_init_module).touch(exist_ok=True)

    # add the connections to the configurations.
    logger.debug("Registering the connection into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.connections.add(connection_name)
    ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))


def _find_protocol_locally(ctx, protocol_name):
    # check that the provided path points to a proper protocol directory -> look for protocol.yaml file.
    # first check in aea dir
    registry_path = ctx.agent_config.registry_path
    protocol_configuration_filepath = Path(os.path.join(registry_path, "protocols", protocol_name, DEFAULT_PROTOCOL_CONFIG_FILE))
    if not protocol_configuration_filepath.exists():
        # then check in registry
        registry_path = AEA_DIR
        protocol_configuration_filepath = Path(os.path.join(registry_path, "protocols", protocol_name, DEFAULT_PROTOCOL_CONFIG_FILE))
        if not protocol_configuration_filepath.exists():
            logger.error("Cannot find protocol: '{}'.".format(protocol_name))
            sys.exit(1)

    # try to load the protocol configuration file
    try:
        protocol_configuration = ctx.protocol_loader.load(open(str(protocol_configuration_filepath)))
        logger.debug("Protocol available: {}".format(protocol_configuration.name))
    except ValidationError as e:
        logger.error("Protocol configuration file not valid: {}".format(str(e)))
        sys.exit(1)

    # copy the protocol package into the agent's supported connections.
    src = str(Path(os.path.join(registry_path, "protocols", protocol_name)).absolute())
    dest = os.path.join(ctx.cwd, "protocols", protocol_name)
    logger.debug("Copying protocol modules. src={} dst={}".format(src, dest))
    try:
        shutil.copytree(src, dest)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


@add.command()
@click.argument(
    'protocol_name', type=PublicIdParameter(), required=True
)
@pass_context
def protocol(click_context, protocol_name):
    """Add a protocol to the agent."""
    ctx = cast(Context, click_context.obj)
    agent_name = cast(str, ctx.agent_config.agent_name)

    is_registry = ctx.config.get("is_registry")
    if is_registry:
        public_id = str(protocol_name)
        protocol_name = split_public_id(protocol_name)[1]

    logger.info("Adding protocol '{}' to the agent '{}'...".format(protocol_name, agent_name))

    # check if we already have a protocol with the same name
    logger.debug("Protocols already supported by the agent: {}".format(ctx.agent_config.protocols))
    if protocol_name in ctx.agent_config.protocols:
        logger.error("A protocol with name '{}' already exists. Aborting...".format(protocol_name))
        sys.exit(1)

    # find and add protocol
    if is_registry:
        # fetch from Registry
        fetch_package('protocol', public_id=public_id, cwd=ctx.cwd)
    else:
        _find_protocol_locally(ctx, protocol_name)

    # make the 'protocols' folder a Python package.
    logger.debug("Creating {}".format(os.path.join(agent_name, "protocols", "__init__.py")))
    Path(os.path.join(ctx.cwd, "protocols", "__init__.py")).touch(exist_ok=True)

    # add the protocol to the configurations.
    logger.debug("Registering the protocol into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.protocols.add(protocol_name)
    ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))


def _find_skill_locally(ctx, skill_name, click_context):
    # check that the provided path points to a proper skill directory -> look for skill.yaml file.
    # first check in aea dir
    registry_path = ctx.agent_config.registry_path
    skill_configuration_filepath = Path(os.path.join(registry_path, "skills", skill_name, DEFAULT_SKILL_CONFIG_FILE))
    if not skill_configuration_filepath.exists():
        # then check in registry
        registry_path = AEA_DIR
        skill_configuration_filepath = Path(os.path.join(registry_path, "skills", skill_name, DEFAULT_SKILL_CONFIG_FILE))
        if not skill_configuration_filepath.exists():
            logger.error("Cannot find skill: '{}'.".format(skill_name))
            sys.exit(1)

    # try to load the skill configuration file
    try:
        skill_configuration = ctx.skill_loader.load(open(str(skill_configuration_filepath)))
    except ValidationError as e:
        logger.error("Skill configuration file not valid: {}".format(str(e)))
        sys.exit(1)

    # copy the skill package into the agent's supported skills.
    src = str(Path(os.path.join(registry_path, "skills", skill_name)).absolute())
    dest = os.path.join(ctx.cwd, "skills", skill_name)
    logger.debug("Copying skill modules. src={} dst={}".format(src, dest))
    try:
        shutil.copytree(src, dest)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

    # check for protocol dependencies not yet added, and add it.
    for protocol_name in skill_configuration.protocols:
        if protocol_name not in ctx.agent_config.protocols:
            logger.debug("Adding protocol '{}' to the agent...".format(protocol_name))
            click_context.invoke(protocol, protocol_name=protocol_name)


@add.command()
@click.argument('skill_name', type=PublicIdParameter(), required=True)
@pass_context
def skill(click_context, skill_name):
    """Add a skill to the agent."""
    ctx = cast(Context, click_context.obj)
    agent_name = ctx.agent_config.agent_name

    is_registry = ctx.config.get("is_registry")
    if is_registry:
        public_id = str(skill_name)
        skill_name = split_public_id(skill_name)[1]

    logger.info("Adding skill '{}' to the agent '{}'...".format(skill_name, agent_name))

    # check if we already have a skill with the same name
    logger.debug("Skills already supported by the agent: {}".format(ctx.agent_config.skills))
    if skill_name in ctx.agent_config.skills:
        logger.error("A skill with name '{}' already exists. Aborting...".format(skill_name))
        sys.exit(1)

    # find and add protocol
    if is_registry:
        # fetch from Registry
        fetch_package('skill', public_id=public_id, cwd=ctx.cwd)
    else:
        _find_skill_locally(ctx, skill_name, click_context)

    # make the 'skills' folder a Python package.
    skills_init_module = os.path.join(ctx.cwd, "skills", "__init__.py")
    logger.debug("Creating {}".format(skills_init_module))
    Path(skills_init_module).touch(exist_ok=True)

    # add the skill to the configurations.
    logger.debug("Registering the skill into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.skills.add(skill_name)
    ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))
