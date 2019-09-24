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
from pathlib import Path

import click
from jsonschema import ValidationError

from aea import AEA_DIR
from aea.channels.base import DEFAULT_CONNECTION_FILE, DEFAULT_CONNECTION_CONFIG_FILE
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, DEFAULT_PROTOCOL_FILES, ConnectionConfig


@click.group()
@pass_ctx
def scaffold(ctx: Context):
    """Scaffold a resource for the agent."""
    _try_to_load_agent_config(ctx)


@scaffold.command()
@click.argument('connection_name', type=str, required=True)
@pass_ctx
def connection(ctx: Context, connection_name: str) -> None:
    """
    Add a connection scaffolding to the configuration file and agent.

    :param ctx: the context
    :param connection_name: the name of the connection
    :return: None
    """
    # check if we already have a connection with the same name
    logger.debug("Connections already supported by the agent: {}".format(ctx.agent_config.connections))
    if connection_name in ctx.agent_config.connections:
        logger.error("A connection with name '{}' already exists. Aborting...".format(connection_name))
        exit(-1)
        return

    try:
        # create the connection folder
        path = Path(os.path.join("connections", connection_name))
        path.mkdir(exist_ok=True)

        # create a config file inside the connection folder
        config_file = open(os.path.join("connections", connection_name, DEFAULT_CONNECTION_CONFIG_FILE), "w")
        connection_config = ConnectionConfig(name=connection_name,
                                             authors="",
                                             version="v1",
                                             license="",
                                             url="",
                                             class_name="",
                                             supported_protocols=[""])
        ctx.connection_loader.dump(connection_config, config_file)
        logger.info("Created connection config file {}".format(DEFAULT_CONNECTION_CONFIG_FILE))

        # create a python file inside the connection folder
        connection_file_module = os.path.join("connections", connection_name, DEFAULT_CONNECTION_FILE)
        logger.info("Creating {}".format(connection_file_module))
        Path(connection_file_module).touch(exist_ok=True)

        # make the connection folder a Python package.
        connection_init_module = os.path.join("connections", connection_name, "__init__.py")
        logger.info("Creating {}".format(connection_init_module))
        Path(connection_init_module).touch(exist_ok=True)

        # add the connection to the configurations.
        logger.info("Registering the connection into {}".format(DEFAULT_AEA_CONFIG_FILE))
        ctx.agent_config.connections.add(connection_name)
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))

    except OSError:
        logger.error("Directory already exist. Aborting...")
        exit(-1)
    except ValidationError as e:
        logger.error(str(e))
        shutil.rmtree(connection_name, ignore_errors=True)
        exit(-1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(connection_name, ignore_errors=True)
        exit(-1)


@scaffold.command()
@click.argument('protocol_name', type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_name: str):
    """
    Add a protocol scaffolding to the configuration file and agent.

    :param ctx: the context
    :param protocol_name: the name of the protocol
    :return: None
    """
    # check if we already have a protocol with the same name
    logger.debug("Protocols already supported by the agent: {}".format(ctx.agent_config.protocols))
    if protocol_name in ctx.agent_config.protocols:
        logger.error("A protocol with name '{}' already exists. Aborting...".format(protocol_name))
        exit(-1)
        return

    try:
        # create the protocol folder
        path = Path(os.path.join("protocols", protocol_name))
        path.mkdir(exist_ok=True)

        # create the needed python files inside the protocol folder
        for file in DEFAULT_PROTOCOL_FILES:
            protocol_file_module = os.path.join("protocols", protocol_name, file)
            logger.info("Creating {}".format(protocol_file_module))
            Path(protocol_file_module).touch(exist_ok=True)

        # make the protocol folder a Python package.
        protocol_init_module = os.path.join("protocols", protocol_name, "__init__.py")
        logger.info("Creating {}".format(protocol_init_module))
        Path(protocol_init_module).touch(exist_ok=True)

        # add the protocol to the configurations.
        logger.info("Registering the protocol into {}".format(DEFAULT_AEA_CONFIG_FILE))
        ctx.agent_config.protocols.add(protocol_name)
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))

    except OSError:
        logger.error("Directory already exist. Aborting...")
        exit(-1)
    except ValidationError as e:
        logger.error(str(e))
        shutil.rmtree(protocol_name, ignore_errors=True)
        exit(-1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(protocol_name, ignore_errors=True)
        exit(-1)


@scaffold.command()
@click.argument('skill_name', type=str, required=True)
@pass_ctx
def skill(ctx: Context, skill_name: str):
    """
    Add a skill scaffolding to the configuration file and agent.

    :param ctx: the context
    :param skill_name: the name of the skill
    :return: None
    """
    # check if we already have a skill with the same name
    logger.debug("Skills already supported by the agent: {}".format(ctx.agent_config.skills))
    if skill_name in ctx.agent_config.skills:
        logger.error("A skill with name '{}' already exists. Aborting...".format(skill_name))
        exit(-1)
        return

    try:
        # create the skill folder
        dest = Path(os.path.join("skills", skill_name))

        # copy the skill package into the agent's supported skills.
        src = Path(os.path.join(AEA_DIR, "skills", "scaffold"))
        logger.info("Copying skill modules. src={} dst={}".format(src, dest))
        try:
            shutil.copytree(src, dest)
        except Exception as e:
            logger.error(e)
            exit(-1)

        # add the skill to the configurations.
        logger.info("Registering the protocol into {}".format(DEFAULT_AEA_CONFIG_FILE))
        ctx.agent_config.skills.add(skill_name)
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))

    except OSError:
        logger.error("Directory already exist. Aborting...")
        exit(-1)
    except ValidationError as e:
        logger.error(str(e))
        shutil.rmtree(skill_name, ignore_errors=True)
        exit(-1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(skill_name, ignore_errors=True)
        exit(-1)
