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

"""Implementation of the 'aea generate' subcommand."""

import os
import shutil
import sys

import click

from aea.configurations.loader import ConfigLoader
from aea.configurations.base import ProtocolSpecification
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.configurations.base import PublicId, DEFAULT_AEA_CONFIG_FILE, DEFAULT_VERSION
from aea.protocols.generator import ProtocolGenerator

# these variables are being used dynamically
from aea.configurations.base import DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_PROTOCOL_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE  # noqa: F401


@click.group()
@pass_ctx
def generate(ctx: Context):
    """Generate a resource for the agent."""
    _try_to_load_agent_config(ctx)


def _generate_item(ctx: Context, item_type, specification_path):
    """Generate an item based on a specification and add it to the configuration file and agent."""
    # Get existing items
    existing_id_list = getattr(ctx.agent_config, "{}s".format(item_type))
    existing_item_list = [public_id.name for public_id in existing_id_list]

    item_type_plural = item_type + "s"

    # Load item specification yaml file
    try:
        config_loader = ConfigLoader("protocol-specification_schema.json", ProtocolSpecification)
        protocol_spec = config_loader.load(open(specification_path))
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

    protocol_directory_path = os.path.join(ctx.cwd, item_type_plural, protocol_spec.name)

    # Check if we already have an item with the same name in the agent config
    logger.debug("{} already supported by the agent: {}".format(item_type_plural, existing_item_list))
    if protocol_spec.name in existing_item_list:
        logger.error("A {} with name '{}' already exists. Aborting...".format(item_type, protocol_spec.name))
        sys.exit(1)
    # Check if we already have a directory with the same name in the resource directory (e.g. protocols) of the agent's directory
    if os.path.exists(protocol_directory_path):
        logger.error("A directory with name '{}' already exists. Aborting...".format(protocol_spec.name))
        sys.exit(1)

    try:
        agent_name = ctx.agent_config.agent_name
        logger.info("Generating {} '{}' and adding it to the agent '{}'...".format(item_type, protocol_spec.name, agent_name))

        output_path = os.path.join(ctx.cwd, item_type_plural)
        protocol_generator = ProtocolGenerator(protocol_spec, output_path)
        protocol_generator.generate()

        # Add the item to the configurations
        logger.debug("Registering the {} into {}".format(item_type, DEFAULT_AEA_CONFIG_FILE))
        existing_id_list.add(PublicId("fetchai", protocol_spec.name, DEFAULT_VERSION))
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))
    except FileExistsError:
        logger.error("A {} with this name already exists. Please choose a different name and try again.".format(item_type))
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(os.path.join(item_type_plural, protocol_spec.name), ignore_errors=True)
        sys.exit(1)


@generate.command()
@click.argument('protocol_specification_path', type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_specification_path: str):
    """Generate a protocol based on a specification and add it to the configuration file and agent."""
    _generate_item(ctx, "protocol", protocol_specification_path)
