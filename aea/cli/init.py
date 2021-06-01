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
from aea.cli.login import do_login
from aea.cli.register import do_register
from aea.cli.registry.settings import AUTH_TOKEN_KEY
from aea.cli.registry.utils import check_is_author_logged_in, is_auth_token_present
from aea.cli.utils.config import get_or_create_cli_config, update_cli_config
from aea.cli.utils.constants import AEA_LOGO, AUTHOR_KEY
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.cli.utils.package_utils import validate_author_name


@click.command()
@click.option("--author", type=str, required=False)
@click.option("--reset", is_flag=True, help="To reset the initialization.")
@click.option("--local", is_flag=True, help="For init AEA locally.")
@click.option("--no-subscribe", is_flag=True, help="For developers subscription.")
@pass_ctx
def init(  # pylint: disable=unused-argument
    ctx: Context, author: str, reset: bool, local: bool, no_subscribe: bool
) -> None:
    """Initialize your AEA configurations."""
    do_init(author, reset, not local, no_subscribe)


def do_init(author: str, reset: bool, registry: bool, no_subscribe: bool) -> None:
    """
    Initialize your AEA configurations.

    :param author: str author username.
    :param reset: True, if resetting the author name
    :param registry: True, if registry is used
    :param no_subscribe: bool flag for developers subscription skip on register.
    """
    config = get_or_create_cli_config()
    if reset or config.get(AUTHOR_KEY, None) is None:
        author = validate_author_name(author)
        if registry:
            _registry_init(username=author, no_subscribe=no_subscribe)

        update_cli_config({AUTHOR_KEY: author})
        config = get_or_create_cli_config()
        config.pop(AUTH_TOKEN_KEY, None)  # for security reasons
        success_msg = "AEA configurations successfully initialized: {}".format(config)
    else:
        config.pop(AUTH_TOKEN_KEY, None)  # for security reasons
        success_msg = "AEA configurations already initialized: {}. To reset use '--reset'.".format(
            config
        )
    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    click.echo(success_msg)


def _registry_init(username: str, no_subscribe: bool) -> None:
    """
    Create an author name on the registry.

    :param username: the user name
    :param no_subscribe: bool flag for developers subscription skip on register.
    """
    if username is not None and is_auth_token_present():
        check_is_author_logged_in(username)
    else:
        is_registered = click.confirm("Do you have a Registry account?")
        if is_registered:
            password = click.prompt("Password", type=str, hide_input=True)
            do_login(username, password)
        else:
            click.echo("Create a new account on the Registry now:")
            email = click.prompt("Email", type=str)
            password = click.prompt("Password", type=str, hide_input=True)

            password_confirmation = ""  # nosec
            while password_confirmation != password:
                click.echo("Please make sure that passwords are equal.")
                password_confirmation = click.prompt(
                    "Confirm password", type=str, hide_input=True
                )

            do_register(username, email, password, password_confirmation, no_subscribe)
