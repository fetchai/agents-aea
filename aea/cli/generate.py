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
from jsonschema import ValidationError
import yaml

from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.configurations.base import PublicId, DEFAULT_AEA_CONFIG_FILE, DEFAULT_VERSION
from aea.protocols.generator import ProtocolTemplate, ProtocolGenerator, ProtocolSpecificationParseError

# these variables are being used dynamically
from aea.configurations.base import DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_PROTOCOL_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE  # noqa: F401


@click.group()
@pass_ctx
def generate(ctx: Context):
    """Generate a resource for the agent."""
    _try_to_load_agent_config(ctx)


def _generate_item(ctx: Context, item_type, item_name, specification_path):
    """Generate an item based on a specification and add it to the configuration file and agent."""
    existing_id_list = getattr(ctx.agent_config, "{}s".format(item_type))
    existing_item_list = [public_id.name for public_id in existing_id_list]

    item_type_plural = item_type + "s"

    try:
        protocol_template = ProtocolTemplate(specification_path)
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

    try:
        protocol_template.load()
    except (yaml.YAMLError, ProtocolSpecificationParseError) as e:
        logger.error(str(e))
        logger.error("Load error. Aborting...")
        exit(1)

    # check if we already have an item with the same name
    logger.debug("{} already supported by the agent: {}".format(item_type_plural, existing_item_list))
    protocol_name = protocol_template.name
    if protocol_name in existing_item_list:
        logger.error("A {} with name '{}' already exists. Aborting...".format(item_type, protocol_name))
        sys.exit(1)

    try:
        agent_name = ctx.agent_config.agent_name
        logger.info("Generating {} '{}' and adding it to the agent '{}'...".format(item_type, protocol_name, agent_name))

        output_path = os.path.join(ctx.cwd, item_type_plural)
        protocol_generator = ProtocolGenerator(protocol_template, output_path)
        protocol_generator.generate()

        # add the item to the configurations.
        logger.debug("Registering the {} into {}".format(item_type, DEFAULT_AEA_CONFIG_FILE))
        existing_id_list.add(PublicId("fetchai", protocol_name, DEFAULT_VERSION))
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))

    except FileExistsError:
        logger.error("A {} with this name already exists. Please choose a different name and try again.".format(item_type))
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(os.path.join(item_type_plural, item_name), ignore_errors=True)
        sys.exit(1)


@generate.command()
@click.argument('protocol_specification_path', type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_specification_path: str):
    """Generate a protocol based on a specification and add it to the configuration file and agent."""
    _generate_item(ctx, "protocol", None, protocol_specification_path)
