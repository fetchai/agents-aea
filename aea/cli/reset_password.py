# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Implementation of the 'aea reset_password' subcommand."""

import click

from aea.cli.registry.login import registry_reset_password


@click.command(
    name="reset_password", help="Reset the password of the registry account."
)
@click.argument("email", type=str, required=True)
def reset_password(email: str) -> None:
    """Command to request Registry to reset password."""
    _do_password_reset(email)


def _do_password_reset(email: str) -> None:
    """
    Request Registry to reset password.

    :param email: str email.
    """
    registry_reset_password(email)
    click.echo("An email with a password reset link was sent to {}".format(email))
