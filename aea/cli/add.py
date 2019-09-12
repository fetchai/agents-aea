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

from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.skills.base.config import DEFAULT_AEA_CONFIG_FILE


@click.group()
@pass_ctx
def add(ctx: Context):
    """Add a resource to the agent."""
    _try_to_load_agent_config(ctx)


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
    ctx.loader.dump_agent_configuration(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))


@add.command()
@click.argument('skill_name', type=str, required=True)
@click.argument('dirpath', type=str, default=None, required=False)
@pass_ctx
def skill(ctx: Context, skill_name, dirpath):
    """Add a skill to the agent."""
    agent_name = ctx.agent_config.agent_name
    logger.debug("Adding skill {skill_name} to the agent {agent_name}..."
                 .format(agent_name=agent_name, skill_name=skill_name))

    # check if we already have a skill with the same name
    logger.debug("Skills already supported by the agent: {}".format(ctx.agent_config.skills))
    if skill_name in ctx.agent_config.skills:
        logger.error("A skill with name '{}' already exists. Aborting...".format(skill_name))
        return

    # copy the skill package into the agent's supported skills.
    if dirpath is None:
        logger.info("Path not specified. Using '{}'...".format(os.path.join(".", skill_name)))
        src = skill_name
    else:
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

    # add the skill to the configurations.
    logger.debug("Registering the skill into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.skills.add(skill_name)
    ctx.loader.dump_agent_configuration(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))
