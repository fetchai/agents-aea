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
from pathlib import Path

import click
from jsonschema import ValidationError
import yaml

# from aea import AEA_DIR
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.configurations.base import PublicId, DEFAULT_AEA_CONFIG_FILE
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

    # loader = getattr(ctx, "{}_loader".format(item_type))
    # default_config_filename = globals()["DEFAULT_{}_CONFIG_FILE".format(item_type.upper())]

    item_type_plural = item_type + "s"

    protocol_template = ProtocolTemplate(specification_path)

    try:
        protocol_template.load()
    except (yaml.YAMLError, ProtocolSpecificationParseError) as e:
        print(str(e))
        print("Load error, exiting now!")
        exit(1)

    # check if we already have an item with the same name
    logger.debug("{} already supported by the agent: {}".format(item_type_plural, existing_item_list))
    protocol_name = protocol_template.name
    if protocol_name in existing_item_list:
        logger.error("A {} with name '{}' already exists. Aborting...".format(item_type, protocol_name))
        sys.exit(1)

    # import pdb; pdb.set_trace()

    try:
        agent_name = ctx.agent_config.agent_name
        logger.info("Generating {} '{}' and adding it to the agent '{}'...".format(item_type, protocol_name, agent_name))

        # output_path = Path(os.path.join(ctx.cwd, item_type_plural))
        output_path = os.path.join(ctx.cwd, item_type_plural)
        protocol_generator = ProtocolGenerator(protocol_template, output_path)
        protocol_generator.generate()

        Path(item_type_plural).mkdir(exist_ok=True)
        #
        # # create the connection folder
        # dest = Path(os.path.join(item_type_plural, item_name))
        #
        # # copy the skill package into the agent's supported skills.
        # src = Path(os.path.join(AEA_DIR, item_type_plural, "scaffold"))
        # logger.debug("Copying {} modules. src={} dst={}".format(item_type, src, dest))
        #
        # shutil.copytree(src, dest)

        # add the connection to the configurations.
        logger.debug("Registering the {} into {}".format(item_type, DEFAULT_AEA_CONFIG_FILE))
        existing_id_list.add(PublicId("fetchai", protocol_name, "0.1.0"))
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))

        # ensure the name in the yaml and the name of the folder are the same
        # config_filepath = os.path.join(ctx.cwd, item_type_plural, item_name, default_config_filename)
        # config = loader.load(open(str(config_filepath)))
        # config.name = item_name
        # loader.dump(config, open(config_filepath, "w"))

    except FileExistsError:
        logger.error("A {} with this name already exists. Please choose a different name and try again.".format(item_type))
        sys.exit(1)
    except ValidationError:
        logger.error("Error when validating the skill configuration file.")
        shutil.rmtree(os.path.join(item_type_plural, item_name), ignore_errors=True)
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
