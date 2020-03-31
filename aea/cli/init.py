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

"""Implementation of the 'aea init' subcommand."""

import click

from aea import __version__
from aea.cli.common import (
    AEA_LOGO,
    AUTHOR,
    Context,
    _get_or_create_cli_config,
    _is_validate_author_handle,
    _update_cli_config,
    pass_ctx,
)
from aea.cli.login import do_login
from aea.cli.register import do_register
from aea.cli.registry.settings import AUTH_TOKEN_KEY
from aea.cli.registry.utils import check_is_author_logged_in, is_auth_token_present
from aea.configurations.base import PublicId


def _registry_init(author):
    username = author

    if is_auth_token_present():
        check_is_author_logged_in(username)
    else:
        is_registered = click.confirm("Do you have a Registry account?")

        if is_registered:
            username = click.prompt("Username", type=str)
            password = click.prompt("Password", type=str, hide_input=True)
            do_login(username, password)
        else:
            click.echo("Create a new account on the Registry now:")
            username = click.prompt("Username", type=str)
            email = click.prompt("Email", type=str)
            password = click.prompt("Password", type=str, hide_input=True)

            password_confirmation = None
            while password_confirmation != password:
                click.echo("Please make sure that passwords are equal.")
                password_confirmation = click.prompt(
                    "Confirm password", type=str, hide_input=True
                )

            do_register(username, email, password, password_confirmation)

    return username


@click.command()
@click.option("--author", type=str, required=False)
@click.option("--registry", is_flag=True, help="For AEA init with Registry.")
@pass_ctx
def init(ctx: Context, author: str, registry: bool):
    """Initialize your AEA configurations."""
    if registry:
        author = _registry_init(author)

    config = _get_or_create_cli_config()
    config.pop(AUTH_TOKEN_KEY, None)  # for security reasons
    if config.get(AUTHOR, None) is None:
        is_not_valid_author = True
        if author is not None and _is_validate_author_handle(author):
            is_not_valid_author = False
        while is_not_valid_author:
            author = click.prompt(
                "Please enter the author handle you would like to use", type=str
            )
            if _is_validate_author_handle(author):
                is_not_valid_author = False
            else:
                click.echo(
                    "Not a valid author handle. Please try again. "
                    "Author handles must satisfy the following regex: {}".format(
                        PublicId.AUTHOR_REGEX
                    )
                )
        _update_cli_config({AUTHOR: author})
        config = _get_or_create_cli_config()
        config.pop(AUTH_TOKEN_KEY, None)  # for security reasons
        success_msg = "AEA configurations successfully initialized: {}".format(config)
    else:
        success_msg = "AEA configurations already initialized: {}".format(config)
    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    click.echo(success_msg)
