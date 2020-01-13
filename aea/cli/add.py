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
from typing import cast, Collection

import click
from click import pass_context
from jsonschema import ValidationError

from aea import AEA_DIR
from aea.cli.common import Context, pass_ctx, logger, try_to_load_agent_config, PublicIdParameter
from aea.cli.registry.utils import fetch_package
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, PublicId, \
    PackageConfiguration, ConnectionConfig, SkillConfig, ConfigurationType, \
    _get_default_configuration_file_name_from_type
from aea.configurations.loader import ConfigLoader


@click.group()
@click.option('--registry', is_flag=True, help="For adding from Registry.")
@pass_ctx
def add(ctx: Context, registry):
    """Add a resource to the agent."""
    if registry:
        ctx.set_config("is_registry", True)
    try_to_load_agent_config(ctx)


def _copy_package_directory(ctx, package_path, item_type, item_name):
    # copy the item package into the agent's supported packages.
    item_type_plural = item_type + "s"
    src = str(package_path.absolute())
    dest = os.path.join(ctx.cwd, item_type_plural, item_name)
    logger.debug("Copying {} modules. src={} dst={}".format(item_type, src, dest))
    try:
        shutil.copytree(src, dest)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


def _add_protocols(click_context, protocols: Collection[PublicId]):
    ctx = cast(Context, click_context.obj)
    # check for protocol dependencies not yet added, and add it.
    for protocol_public_id in protocols:
        if protocol_public_id not in ctx.agent_config.protocols:
            logger.debug("Adding protocol '{}' to the agent...".format(protocol_public_id))
            click_context.invoke(protocol, protocol_public_id=protocol_public_id)


def _find_item_locally(ctx, item_type, item_public_id) -> PackageConfiguration:
    """
    Find an item in the registry or in the AEA directory and copy it to the agent resources.

    :param ctx: the CLI context.
    :param item_type: the type of the item to load. One of: protocols, connections, skills
    :param item_public_id: the public id of the item to find.
    :return: the configuration object of the found item
    :raises SystemExit: if the search fails.
    """
    item_type_plural = item_type + 's'
    item_name = item_public_id.name
    registry_path = ctx.agent_config.registry_path
    package_path = Path(registry_path, item_public_id.author, item_type_plural, item_name)
    config_file_name = _get_default_configuration_file_name_from_type(item_type)
    item_configuration_filepath = package_path / config_file_name
    if not item_configuration_filepath.exists():
        # then check in aea dir
        registry_path = AEA_DIR
        package_path = Path(registry_path, item_type_plural, item_name)
        item_configuration_filepath = package_path / config_file_name
        if not item_configuration_filepath.exists():
            logger.error("Cannot find {}: '{}'.".format(item_type, item_public_id))
            sys.exit(1)

    # try to load the item configuration file
    try:
        item_configuration_loader = ConfigLoader.from_configuration_type(ConfigurationType(item_type))
        item_configuration = item_configuration_loader.load(open(str(item_configuration_filepath)))
    except ValidationError as e:
        logger.error("{} configuration file not valid: {}".format(item_type.capitalize(), str(e)))
        sys.exit(1)

    # check that the configuration file of the found package matches the expected author and version.
    version = item_configuration.version
    author = item_configuration.author
    if item_public_id.author != author or item_public_id.version != version:
        logger.error("Cannot find {} with author and version specified.".format(item_type))
        sys.exit(1)

    _copy_package_directory(ctx, package_path, item_type, item_name)
    return item_configuration


@add.command()
@click.argument('connection_public_id', type=PublicIdParameter(), required=True)
@pass_context
def connection(click_context, connection_public_id: PublicId):
    """Add a connection to the configuration file."""
    ctx = cast(Context, click_context.obj)
    agent_name = ctx.agent_config.agent_name

    is_registry = ctx.config.get("is_registry")

    logger.info("Adding connection '{}' to the agent '{}'...".format(connection_public_id, agent_name))

    # check if we already have a connection with the same name
    logger.debug("Connections already supported by the agent: {}".format(ctx.agent_config.connections))
    if _is_item_present('connection', connection_public_id, ctx):
        logger.error("A connection with id '{}' already exists. Aborting...".format(connection_public_id))
        sys.exit(1)

    # find and add connection
    if is_registry:
        # fetch from Registry
        fetch_package('connection', public_id=connection_public_id, cwd=ctx.cwd)
    else:
        connection_configuration = _find_item_locally(ctx, "connection", connection_public_id)
        connection_configuration = cast(ConnectionConfig, connection_configuration)
        _add_protocols(click_context, connection_configuration.protocols)

    # add the connections to the configurations.
    logger.debug("Registering the connection into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.connections.add(connection_public_id)
    ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))


@add.command()
@click.argument('protocol_public_id', type=PublicIdParameter(), required=True)
@pass_context
def protocol(click_context, protocol_public_id):
    """Add a protocol to the agent."""
    ctx = cast(Context, click_context.obj)
    agent_name = cast(str, ctx.agent_config.agent_name)

    is_registry = ctx.config.get("is_registry")

    logger.info("Adding protocol '{}' to the agent '{}'...".format(protocol_public_id, agent_name))

    # check if we already have a protocol with the same name
    logger.debug("Protocols already supported by the agent: {}".format(ctx.agent_config.protocols))
    if _is_item_present('protocol', protocol_public_id, ctx):
        logger.error("A protocol with id '{}' already exists. Aborting...".format(protocol_public_id))
        sys.exit(1)

    # find and add protocol
    if is_registry:
        # fetch from Registry
        fetch_package('protocol', public_id=protocol_public_id, cwd=ctx.cwd)
    else:
        _find_item_locally(ctx, "protocol", protocol_public_id)

    # add the protocol to the configurations.
    logger.debug("Registering the protocol into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.protocols.add(protocol_public_id)
    ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))


@add.command()
@click.argument('skill_public_id', type=PublicIdParameter(), required=True)
@pass_context
def skill(click_context, skill_public_id: PublicId):
    """Add a skill to the agent."""
    ctx = cast(Context, click_context.obj)
    agent_name = ctx.agent_config.agent_name

    is_registry = ctx.config.get("is_registry")

    logger.info("Adding skill '{}' to the agent '{}'...".format(skill_public_id, agent_name))

    # check if we already have a skill with the same name
    logger.debug("Skills already supported by the agent: {}".format(ctx.agent_config.skills))
    if _is_item_present('skill', skill_public_id, ctx):
        logger.error("A skill with id '{}' already exists. Aborting...".format(skill_public_id))
        sys.exit(1)

    # find and add protocol
    if is_registry:
        # fetch from Registry
        fetch_package('skill', public_id=skill_public_id, cwd=ctx.cwd)
    else:
        skill_configuration = _find_item_locally(ctx, "skill", skill_public_id)
        skill_configuration = cast(SkillConfig, skill_configuration)
        _add_protocols(click_context, skill_configuration.protocols)

    # add the skill to the configurations.
    logger.debug("Registering the skill into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.skills.add(skill_public_id)
    ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))


def _is_item_present(item_type, item_public_id, ctx):
    item_type_plural = item_type + 's'
    dest_path = os.path.join(ctx.cwd, item_type_plural, item_public_id.name)
    items_in_config = getattr(ctx.agent_config, item_type_plural)
    return item_public_id in items_in_config and os.path.exists(dest_path)
