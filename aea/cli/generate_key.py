# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""Implementation of the 'aea generate_key' subcommand."""
from pathlib import Path
from typing import Dict, Optional, Union

import click

from aea.cli.add_key import _add_private_key
from aea.cli.utils.click_utils import password_option
from aea.cli.utils.decorators import _check_aea_project
from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.crypto.helpers import create_private_key
from aea.crypto.registries import crypto_registry


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice([*list(crypto_registry.supported_ids), "all"]),
    required=True,
)
@click.argument(
    "file",
    metavar="FILE",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, readable=True),
    required=False,
)
@password_option(confirmation_prompt=True)
@click.option(
    "--add-key",
    is_flag=True,
    help="Add key generated.",
)
@click.option(
    "--connection", is_flag=True, help="For adding a private key for connections."
)
@click.option(
    "--extra-entropy",
    type=str,
    required=False,
    default="",
)
@click.pass_context
def generate_key(
    click_context: click.core.Context,
    type_: str,
    file: str,
    password: Optional[str],
    add_key: bool = False,
    connection: bool = False,
    extra_entropy: Union[str, bytes, int] = "",
) -> None:
    """Generate a private key and place it in a file."""
    keys_generated = _generate_private_key(type_, file, password, extra_entropy)
    if add_key:
        _check_aea_project((click_context,))
        for key_type, key_filename in keys_generated.items():
            _add_private_key(
                click_context, key_type, key_filename, password, connection
            )


def _generate_private_key(
    type_: str,
    file: Optional[str] = None,
    password: Optional[str] = None,
    extra_entropy: Union[str, bytes, int] = "",
) -> Dict[str, str]:
    """
    Generate private key.

    :param type_: type.
    :param file: path to file.
    :param password: the password to encrypt/decrypt the private key.
    :param extra_entropy: add extra randomness to whatever randomness your OS can provide

    :return: dict of types and filenames of keys generated
    """
    keys = {}
    if type_ == "all" and file is not None:
        raise click.ClickException("Type all cannot be used in combination with file.")
    types = list(crypto_registry.supported_ids) if type_ == "all" else [type_]
    for type__ in types:
        private_key_file = (
            PRIVATE_KEY_PATH_SCHEMA.format(type__) if file is None else file
        )
        if _can_write(private_key_file):
            create_private_key(type__, private_key_file, password, extra_entropy)
        keys[type__] = private_key_file
    return keys


def _can_write(path: str) -> bool:
    if Path(path).exists():
        value = click.confirm(
            "The file {} already exists. Do you want to overwrite it?".format(path),
            default=False,
        )
        return value
    return True
