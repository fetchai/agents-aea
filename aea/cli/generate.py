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
import subprocess  # nosec
import sys
from typing import cast

import click

from aea.cli.fingerprint import _fingerprint_item
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after
from aea.cli.utils.loggers import logger
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_VERSION,
    ProtocolSpecification,
    ProtocolSpecificationParseError,
    PublicId,
)
from aea.configurations.loader import ConfigLoader
from aea.protocols.generator import ProtocolGenerator


@click.group()
@click.pass_context
@check_aea_project
def generate(click_context):
    """Generate a resource for the agent."""


@clean_after
def _generate_item(click_context, item_type, specification_path):
    """Generate an item based on a specification and add it to the configuration file and agent."""
    # check protocol buffer compiler is installed
    ctx = cast(Context, click_context.obj)
    res = shutil.which("protoc")
    if res is None:
        raise click.ClickException(
            "Please install protocol buffer first! See the following link: https://developers.google.com/protocol-buffers/"
        )

    # check black code formatter is installed
    res = shutil.which("black")
    if res is None:
        raise click.ClickException(
            "Please install black code formater first! See the following link: https://black.readthedocs.io/en/stable/installation_and_usage.html"
        )

    # Get existing items
    existing_id_list = getattr(ctx.agent_config, "{}s".format(item_type))
    existing_item_list = [public_id.name for public_id in existing_id_list]

    item_type_plural = item_type + "s"

    # Load item specification yaml file
    try:
        config_loader = ConfigLoader(
            "protocol-specification_schema.json", ProtocolSpecification
        )
        protocol_spec = config_loader.load_protocol_specification(
            open(specification_path)
        )
    except Exception as e:
        raise click.ClickException(str(e))

    protocol_directory_path = os.path.join(
        ctx.cwd, item_type_plural, protocol_spec.name
    )

    # Check if we already have an item with the same name in the agent config
    logger.debug(
        "{} already supported by the agent: {}".format(
            item_type_plural, existing_item_list
        )
    )
    if protocol_spec.name in existing_item_list:
        raise click.ClickException(
            "A {} with name '{}' already exists. Aborting...".format(
                item_type, protocol_spec.name
            )
        )
    # Check if we already have a directory with the same name in the resource directory (e.g. protocols) of the agent's directory
    if os.path.exists(protocol_directory_path):
        raise click.ClickException(
            "A directory with name '{}' already exists. Aborting...".format(
                protocol_spec.name
            )
        )

    ctx.clean_paths.append(protocol_directory_path)
    try:
        agent_name = ctx.agent_config.agent_name
        click.echo(
            "Generating {} '{}' and adding it to the agent '{}'...".format(
                item_type, protocol_spec.name, agent_name
            )
        )

        output_path = os.path.join(ctx.cwd, item_type_plural)
        protocol_generator = ProtocolGenerator(protocol_spec, output_path)
        protocol_generator.generate()

        # Add the item to the configurations
        logger.debug(
            "Registering the {} into {}".format(item_type, DEFAULT_AEA_CONFIG_FILE)
        )
        existing_id_list.add(PublicId("fetchai", protocol_spec.name, DEFAULT_VERSION))
        ctx.agent_loader.dump(
            ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
        )
    except FileExistsError:
        raise click.ClickException(
            "A {} with this name already exists. Please choose a different name and try again.".format(
                item_type
            )
        )
    except ProtocolSpecificationParseError as e:
        raise click.ClickException(
            "The following error happened while parsing the protocol specification: "
            + str(e)
        )
    except Exception as e:
        raise click.ClickException(
            "There was an error while generating the protocol. The protocol is NOT generated. Exception: "
            + str(e)
        )

    # Run black code formatting
    try:
        subp = subprocess.Popen(  # nosec
            [
                sys.executable,
                "-m",
                "black",
                os.path.join(item_type_plural, protocol_spec.name),
                "--quiet",
            ]
        )
        subp.wait(10.0)
    finally:
        poll = subp.poll()
        if poll is None:  # pragma: no cover
            subp.terminate()
            subp.wait(5)

    _fingerprint_item(click_context, "protocol", protocol_spec.public_id)


@generate.command()
@click.argument("protocol_specification_path", type=str, required=True)
@click.pass_context
def protocol(click_context, protocol_specification_path: str):
    """Generate a protocol based on a specification and add it to the configuration file and agent."""
    _generate_item(click_context, "protocol", protocol_specification_path)
