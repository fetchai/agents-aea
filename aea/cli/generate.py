# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
from typing import Set

import click
import yaml

from aea.cli.fingerprint import fingerprint_item
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.loggers import logger
from aea.configurations.base import (
    ProtocolSpecification,
    ProtocolSpecificationParseError,
    PublicId,
)
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    PROTOCOL,
    PROTOCOL_LANGUAGE_PYTHON,
    SUPPORTED_PROTOCOL_LANGUAGES,
)
from aea.helpers.io import open_file
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
    type=click.Choice(SUPPORTED_PROTOCOL_LANGUAGES),
    required=False,
    default=PROTOCOL_LANGUAGE_PYTHON,
    help="Specify the language in which to generate the protocol package.",
)
@pass_ctx
def protocol(ctx: Context, protocol_specification_path: str, language: str) -> None:
    """Generate a protocol based on a specification and add it to the configuration file and agent."""
    ctx.set_config("language", language)
    _generate_protocol(ctx, protocol_specification_path)


@clean_after
def _generate_protocol(ctx: Context, protocol_specification_path: str) -> None:
    """Generate a protocol based on a specification and add it to the configuration file and agent."""
    protocol_plural = PROTOCOL + "s"

    # Create protocol generator (load, validate,
    # extract fields from protocol specification yaml file)
    try:
        output_path = os.path.join(ctx.cwd, protocol_plural)
        protocol_generator = ProtocolGenerator(protocol_specification_path, output_path)
    except FileNotFoundError as e:
        raise click.ClickException(  # pragma: no cover
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + str(e)
        )
    except yaml.YAMLError as e:
        raise click.ClickException(  # pragma: no cover
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + "Yaml error in the protocol specification file:"
            + str(e)
        )
    except ProtocolSpecificationParseError as e:
        raise click.ClickException(  # pragma: no cover
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + "Error while parsing the protocol specification: "
            + str(e)
        )
    except Exception as e:  # pragma: no cover
        raise click.ClickException(  # pragma: no cover
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + str(e)
        )

    # helpers
    language = ctx.config.get("language")
    existing_protocol_ids_list = getattr(ctx.agent_config, "{}s".format(PROTOCOL))
    existing_protocol_name_list = [
        public_id.name for public_id in existing_protocol_ids_list
    ]
    protocol_spec = protocol_generator.protocol_specification
    protocol_directory_path = os.path.join(ctx.cwd, protocol_plural, protocol_spec.name)

    # Check if a protocol with the same name exists in the agent config
    if protocol_spec.name in existing_protocol_name_list:
        raise click.ClickException(
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + f"A {PROTOCOL} with name '{protocol_spec.name}' already exists. Aborting..."
        )

    # Check if a directory with the same name as the protocol's exists
    # in the protocols directory of the agent's directory
    if os.path.exists(protocol_directory_path):
        raise click.ClickException(
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + f"A directory with name '{protocol_spec.name}' already exists. Aborting..."
        )

    ctx.clean_paths.append(protocol_directory_path)
    agent_name = ctx.agent_config.agent_name
    click.echo(
        "Generating {} '{}' and adding it to the agent '{}'...".format(
            PROTOCOL, protocol_spec.name, agent_name
        )
    )

    if language == PROTOCOL_LANGUAGE_PYTHON:
        _generate_full_mode(
            ctx, protocol_generator, protocol_spec, existing_protocol_ids_list, language
        )
    else:
        _generate_protobuf_mode(ctx, protocol_generator, language)


@clean_after
def _generate_full_mode(
    ctx: Context,
    protocol_generator: ProtocolGenerator,
    protocol_spec: ProtocolSpecification,
    existing_id_list: Set[PublicId],
    language: str,
) -> None:
    """Generate a protocol in 'full' mode, and add it to the configuration file and agent."""
    try:
        warning_message = protocol_generator.generate(
            protobuf_only=False, language=language
        )
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
            ctx.agent_config,
            open_file(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"),
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
    ctx: Context,  # pylint: disable=unused-argument
    protocol_generator: ProtocolGenerator,
    language: str,
) -> None:
    """Generate a protocol in 'protobuf' mode, and add it to the configuration file and agent."""
    try:
        warning_message = protocol_generator.generate(
            protobuf_only=True, language=language
        )
        if warning_message is not None:
            click.echo(warning_message)
    except FileExistsError:  # pragma: no cover
        raise click.ClickException(  # pragma: no cover
            f"A {PROTOCOL} with this name already exists. Please choose a different name and try again."
        )
    except Exception as e:  # pragma: no cover
        raise click.ClickException(  # pragma: no cover
            "Protocol is NOT generated. The following error happened while generating the protocol:\n"
            + str(e)
        )
