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
from aea.configurations.base import PublicId


@click.command()
@click.option("--author", type=str, required=False)
@pass_ctx
def init(ctx: Context, author: str):
    """Initialize your AEA configurations."""
    config = _get_or_create_cli_config()
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
                    "Not a valid author handle. Please try again. Author handles must satisfy the following regex: {}".format(
                        PublicId.AUTHOR_REGEX
                    )
                )
        _update_cli_config({AUTHOR: author})
        config = _get_or_create_cli_config()
        success_msg = "AEA configurations successfully initialized: {}".format(config)
    else:
        success_msg = "AEA configurations already initialized: {}".format(config)
    click.echo(AEA_LOGO + "v" + __version__ + "\n")
    click.echo(success_msg)
