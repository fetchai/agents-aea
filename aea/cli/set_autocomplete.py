# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""Implementation of the 'aea set-autocomple' subcommand."""
import os
from os import environ

import click


SHELL_SUPPORTED = "bash"
AUTOCOMPLETE_FILE_PATH = "~/.aea-autocomplete.sh"
COMPLETETION_LOAD_CMD = f"source {AUTOCOMPLETE_FILE_PATH}"
BASHRC = "~/.bashrc"


@click.command()
def set_autocomplete() -> None:
    """Set autocompletition support for bash shell."""
    shell = environ["SHELL"].split("/")[-1]

    if shell != SHELL_SUPPORTED:
        raise click.ClickException(
            f"Your shell `{shell}` is not supported! Supported shell is: {SHELL_SUPPORTED}"
        )

    click.echo("Generating autocompletition script...")
    os.system(f"_AEA_COMPLETE=source_bash aea > {AUTOCOMPLETE_FILE_PATH}")  # nosec
    click.echo("Autocompletition script generated.")

    try:
        with open(os.path.expanduser(BASHRC), "r") as f:
            data = f.read()
    except FileNotFoundError:
        data = ""

    if COMPLETETION_LOAD_CMD not in data:
        # add command
        with open(os.path.expanduser(BASHRC), "a+") as f:
            f.write("\n")
            f.write(COMPLETETION_LOAD_CMD)
            f.write("\n")
            click.echo(f"{BASHRC} updated!")
    else:
        click.echo(f"{BASHRC} was already updated! skip.")

    click.echo("Autocompletition installed! Don't forget to reload shell!")
