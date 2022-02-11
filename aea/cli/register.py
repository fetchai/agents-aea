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

"""Implementation of the 'aea login' subcommand."""

import click

from aea.cli.registry.registration import register as register_new_account
from aea.cli.registry.settings import AUTH_TOKEN_KEY
from aea.cli.utils.config import update_cli_config
from aea.cli.utils.package_utils import validate_author_name


@click.command(name="register", help="Create a new registry account.")
@click.option("--username", type=str, required=True, prompt=True)
@click.option("--email", type=str, required=True, prompt=True)
@click.option("--password", type=str, required=True, prompt=True, hide_input=True)
@click.option(
    "--confirm_password", type=str, required=True, prompt=True, hide_input=True
)
@click.option("--no-subscribe", is_flag=True, help="For developers subscription.")
def register(
    username: str, email: str, password: str, confirm_password: str, no_subscribe: bool
) -> None:
    """Create a new registry account."""
    do_register(username, email, password, confirm_password, no_subscribe)


def do_register(
    username: str,
    email: str,
    password: str,
    password_confirmation: str,
    no_subscribe: bool,
) -> None:
    """
    Register a new Registry account and save auth token.

    :param username: str username.
    :param email: str email.
    :param password: str password.
    :param password_confirmation: str password confirmation.
    :param no_subscribe: bool flag for developers subscription skip on register.
    """
    username = validate_author_name(username)
    token = register_new_account(username, email, password, password_confirmation)
    update_cli_config({AUTH_TOKEN_KEY: token})
    if not no_subscribe and click.confirm(
        "Do you want to subscribe for developer news?"
    ):
        click.echo(
            "Please visit `https://aea-registry.fetch.ai/mailing-list` "
            "to subscribe for developer news"
        )
    click.echo("Successfully registered and logged in: {}".format(username))
