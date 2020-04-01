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

from typing import Optional

import click

from aea import __version__
from aea.cli.common import (
    AEA_LOGO,
    AUTHOR,
    Context,
    NOT_PERMITTED_AUTHORS,
    _get_or_create_cli_config,
    _is_permitted_author_handle,
    _is_valid_author_handle,
    _update_cli_config,
    pass_ctx,
)
from aea.cli.login import do_login
from aea.cli.register import do_register
from aea.cli.registry.settings import AUTH_TOKEN_KEY
from aea.cli.registry.utils import check_is_author_logged_in, is_auth_token_present
from aea.configurations.base import PublicId


def _local_init(author: Optional[str] = None) -> str:
    """
    Create an author name for local usage only.

    :param author: the author name (optional)
    """
    is_acceptable_author = False
    if (
        author is not None
        and _is_valid_author_handle(author)
        and _is_permitted_author_handle(author)
    ):
        is_acceptable_author = True
        valid_author = author
    while not is_acceptable_author:
        author_prompt = click.prompt(
            "Please enter the author handle you would like to use", type=str
        )
        valid_author = author_prompt
        if _is_valid_author_handle(author_prompt) and _is_permitted_author_handle(
            author_prompt
        ):
            is_acceptable_author = True
        elif not _is_valid_author_handle(author_prompt):
            is_acceptable_author = False
            click.echo(
                "Not a valid author handle. Please try again. "
                "Author handles must satisfy the following regex: {}".format(
                    PublicId.AUTHOR_REGEX
                )
            )
        elif not _is_permitted_author_handle(author_prompt):
            is_acceptable_author = False
            click.echo(
                "Not a permitted author handle. The following author handles are not allowed: {}".format(
                    NOT_PERMITTED_AUTHORS
                )
            )

    return valid_author


def _registry_init(author: Optional[str] = None) -> str:
    """
    Create an author name on the registry.

    :param author: the author name
    """
    if author is not None and is_auth_token_present():
        check_is_author_logged_in(author)
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

            password_confirmation = ""  # nosec
            while password_confirmation != password:
                click.echo("Please make sure that passwords are equal.")
                password_confirmation = click.prompt(
                    "Confirm password", type=str, hide_input=True
                )

            do_register(username, email, password, password_confirmation)

    return username


def do_init(author: str, reset: bool, registry: bool) -> None:
    """
    Initialize your AEA configurations.

    :param author: str author username.
    :param reset: True, if resetting the author name
    :param registry: True, if registry is used

    :return: None.
    """
    config = _get_or_create_cli_config()
    if reset or config.get(AUTHOR, None) is None:
        if registry:
            author = _registry_init(author)
        else:
            author = _local_init(author)
        _update_cli_config({AUTHOR: author})
        config.pop(AUTH_TOKEN_KEY, None)  # for security reasons
        success_msg = "AEA configurations successfully initialized: {}".format(config)
    else:
        config.pop(AUTH_TOKEN_KEY, None)  # for security reasons
        success_msg = "AEA configurations already initialized: {}. To reset use '--reset'.".format(
            config
        )
    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    click.echo(success_msg)


@click.command()
@click.option("--author", type=str, required=False)
@click.option("--reset", is_flag=True, help="To reset the initialization.")
@click.option("--local", is_flag=True, help="For init AEA locally.")
@pass_ctx
def init(ctx: Context, author: str, reset: bool, local: bool):
    """Initialize your AEA configurations."""
    do_init(author, reset, not local)
