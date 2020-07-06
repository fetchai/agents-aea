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

"""Implementation of the 'aea generate_key' subcommand."""

from pathlib import Path

import click

from aea.crypto.helpers import IDENTIFIER_TO_KEY_FILES, create_private_key
from aea.crypto.registries import crypto_registry


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice([*list(crypto_registry.supported_ids), "all"]),
    required=True,
)
def generate_key(type_):
    """Generate private keys."""
    _generate_private_key(type_)


def _generate_private_key(type_: str) -> None:
    """
    Generate private key.

    :param type_: type.

    :return: None
    """
    types = list(IDENTIFIER_TO_KEY_FILES.keys()) if type_ == "all" else [type_]
    for type_ in types:
        private_key_file = IDENTIFIER_TO_KEY_FILES[type_]
        if _can_write(private_key_file):
            create_private_key(type_)


def _can_write(path) -> bool:
    if Path(path).exists():
        value = click.confirm(
            "The file {} already exists. Do you want to overwrite it?".format(path),
            default=False,
        )
        return value
    else:
        return True
