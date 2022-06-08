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
"""Implementation of the 'aea config' subcommand."""
import contextlib
import json
from typing import Optional, cast

import click
from click.exceptions import ClickException

from aea.cli.utils.constants import CONFIG_SUPPORTED_KEY_TYPES
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.configurations.manager import AgentConfigManager, VariableDoesNotExist
from aea.configurations.validation import ExtraPropertiesError
from aea.exceptions import AEAException
from aea.helpers.env_vars import convert_value_str_to_type


@click.group()
@click.pass_context
@check_aea_project
def config(click_context: click.Context) -> None:  # pylint: disable=unused-argument
    """Read or modify a configuration of the agent."""


@config.command()
@click.argument("JSON_PATH", required=True)
@click.option(
    "--aev",
    "apply_environment_variables",
    required=False,
    is_flag=True,
    default=False,
    help="Populate Agent configs from Environment variables.",
)
@pass_ctx
def get(ctx: Context, apply_environment_variables: bool, json_path: str) -> None:
    """Get a field."""
    try:
        agent_config_manager = AgentConfigManager.load(
            ctx.cwd, apply_environment_variables
        )
        value = agent_config_manager.get_variable(json_path)
    except (ValueError, AEAException) as e:
        raise ClickException(*e.args)

    if isinstance(value, dict):
        # turn it to json compatible string, not dict str representation
        value = json.dumps(value, sort_keys=True)
    click.echo(value)


@config.command(name="set")
@click.option(
    "--type",
    "type_",
    default=None,
    type=click.Choice(CONFIG_SUPPORTED_KEY_TYPES + [None]),  # type: ignore
    help="Specify the type of the value.",
)
@click.argument("JSON_PATH", required=True)
@click.argument("VALUE", required=True, type=str)
@click.option(
    "--aev",
    "apply_environment_variables",
    required=False,
    is_flag=True,
    default=False,
    help="Populate Agent configs from Environment variables.",
)
@pass_ctx
def set_command(
    ctx: Context,
    json_path: str,
    value: str,
    apply_environment_variables: bool,
    type_: Optional[str],
) -> None:
    """Set a field."""
    try:
        agent_config_manager = AgentConfigManager.load(
            ctx.cwd, apply_environment_variables
        )

        current_value = None
        with contextlib.suppress(VariableDoesNotExist):
            current_value = agent_config_manager.get_variable(json_path)

        # type was not specified, tried to auto determine
        if type_ is None:
            # apply str as default type
            converted_value = convert_value_str_to_type(value, "str")
            if current_value is not None:
                # try to convert to original value's type
                with contextlib.suppress(Exception):
                    converted_value = convert_value_str_to_type(
                        value, type(current_value).__name__
                    )
        else:
            # convert to type specified by user
            converted_value = convert_value_str_to_type(value, cast(str, type_))

        agent_config_manager.set_variable(json_path, converted_value)
        agent_config_manager.dump_config()
    except ExtraPropertiesError as e:  # pragma: nocover
        raise ClickException(f"Attribute `{e.args[0][0]}` is not allowed to change!")
    except (ValueError, AEAException) as e:
        raise ClickException(*e.args)
