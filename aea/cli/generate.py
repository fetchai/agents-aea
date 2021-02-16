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
import yaml

import click

from aea.cli.fingerprint import fingerprint_item
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.loggers import logger
from aea.configurations.base import ProtocolSpecificationParseError, PublicId, ProtocolSpecification
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE, PROTOCOL
from aea.protocols.generator.base import ProtocolGenerator


@click.group()
@click.pass_context
@check_aea_project
def generate(
    click_context: click.core.Context,  # pylint: disable=unused-argument
) -> None:
    """Generate a package for the agent."""


@generate.command()
@click.argument("protocol_specification_path", type=str, required=True)
@click.option(
    "--l",
    "language",
    type=str,
    required=False,
    default="python",
    help="Specify the language in which to generate the protocol package.",
)
@pass_ctx
def protocol(ctx: Context, protocol_specification_path: str, language: str) -> None:
    """Generate a protocol based on a specification and add it to the configuration file and agent."""
    # Get existing items
    existing_id_list = getattr(ctx.agent_config, "{}s".format(PROTOCOL))
    existing_item_list = [public_id.name for public_id in existing_id_list]
    item_type_plural = PROTOCOL + "s"

    # Create protocol generator (load, validate,
    # extract fields from protocol specification yaml file)
    try:
        output_path = os.path.join(ctx.cwd, item_type_plural)
        protocol_generator = ProtocolGenerator(protocol_specification_path, output_path)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))  # pragma: no cover
    except yaml.YAMLError as e:
        raise click.ClickException(  # pragma: no cover
            "Error in protocol specification yaml file:" + str(e)
        )
    except ProtocolSpecificationParseError as e:
        raise click.ClickException(  # pragma: no cover
            "The following error happened while parsing the protocol specification: "
            + str(e)
        )
    except Exception as e:
        raise click.ClickException(str(e))

    # helpers
    protocol_spec = protocol_generator.protocol_specification
    protocol_directory_path = os.path.join(
        ctx.cwd, item_type_plural, protocol_spec.name
    )
    logger.debug(
        "{} already supported by the agent: {}".format(
            item_type_plural, existing_item_list
        )
    )

    # Check if we already have an item with the same name in the agent config
    if protocol_spec.name in existing_item_list:
        raise click.ClickException(
            "A {} with name '{}' already exists. Aborting...".format(
                PROTOCOL, protocol_spec.name
            )
        )

    # Check if we already have a directory with the same name in the resource
    # directory (e.g. protocols) of the agent's directory
    if os.path.exists(protocol_directory_path):
        raise click.ClickException(
            "A directory with name '{}' already exists. Aborting...".format(
                protocol_spec.name
            )
        )

    ctx.clean_paths.append(protocol_directory_path)
    agent_name = ctx.agent_config.agent_name
    click.echo(
        "Generating {} '{}' and adding it to the agent '{}'...".format(
            PROTOCOL, protocol_spec.name, agent_name
        )
    )

    if language == "python":
        _generate_full_mode(ctx, protocol_generator, protocol_spec, existing_id_list)
    else:
        _generate_protobuf_mode(ctx, protocol_generator, protocol_spec, existing_id_list, language)


@clean_after
def _generate_full_mode(
        ctx: Context,
        protocol_generator: ProtocolGenerator,
        protocol_spec: ProtocolSpecification,
        existing_id_list
) -> None:
    """Generate a protocol in 'full' mode, and add it to the configuration file and agent."""
    try:
        warning_message = protocol_generator.generate()
        if warning_message is not None:
            click.echo(warning_message)

        # Add the item to the configurations
        logger.debug(
            "Registering the {} into {}".format(PROTOCOL, DEFAULT_AEA_CONFIG_FILE)
        )
        existing_id_list.add(
            PublicId(protocol_spec.author, protocol_spec.name, protocol_spec.version)
        )
        ctx.agent_loader.dump(
            ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
        )
    except FileExistsError:
        raise click.ClickException(  # pragma: no cover
            "A {} with this name already exists. Please choose a different name and try again.".format(
                PROTOCOL
            )
        )
    except Exception as e:
        raise click.ClickException(
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + str(e)
        )
    fingerprint_item(ctx, PROTOCOL, protocol_spec.public_id)


@clean_after
def _generate_protobuf_mode(
        ctx: Context,
        protocol_generator: ProtocolGenerator,
        protocol_spec: ProtocolSpecification,
        existing_id_list,
        language: str
) -> None:
    """Generate a protocol in 'protobuf' mode, and add it to the configuration file and agent."""
    try:
        warning_message = protocol_generator.generate(protobuf_only=True)
        if warning_message is not None:
            click.echo(warning_message)

        # Add the item to the configurations
        logger.debug(
            "Registering the {} into {}".format(PROTOCOL, DEFAULT_AEA_CONFIG_FILE)
        )
        existing_id_list.add(
            PublicId(protocol_spec.author, protocol_spec.name, protocol_spec.version)
        )
        ctx.agent_loader.dump(
            ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
        )
    except FileExistsError:
        raise click.ClickException(  # pragma: no cover
            "A {} with this name already exists. Please choose a different name and try again.".format(
                PROTOCOL
            )
        )
    except Exception as e:
        raise click.ClickException(
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + str(e)
        )
