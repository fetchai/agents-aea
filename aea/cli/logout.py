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

"""Implementation of the 'aea logout' subcommand."""

import click

from aea.cli.registry.logout import registry_logout
from aea.cli.registry.settings import AUTH_TOKEN_KEY
from aea.cli.utils.config import update_cli_config


@click.command(name="logout", help="Logout from the registry account.")
def logout() -> None:
    """Logout from the registry account."""
    click.echo("Logging out...")
    do_logout()
    click.echo("Successfully logged out.")


def do_logout() -> None:
    """Logout from Registry account."""
    registry_logout()
    update_cli_config({AUTH_TOKEN_KEY: None})
