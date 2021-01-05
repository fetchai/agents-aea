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

"""Implementation of plug-in mechanism for cryptos."""
from typing import Dict

from pkg_resources import EntryPoint, iter_entry_points

from aea.crypto import register_crypto
from aea.crypto.registries.base import EntryPoint as EntryPointString


def get_plugins() -> Dict[str, EntryPoint]:
    """Return a dict of all installed crypto plugins, by name."""

    plugins = iter_entry_points(group="aea.cryptos")

    return {plugin.name: plugin for plugin in plugins}


def load_all_cryptos() -> None:
    """Load all crypto plugins."""
    for ledger_id, entry_point in get_plugins().items():
        # TODO handle unpacking errors
        # TODO check class is an instance of Crypto interface
        entry_point_string = EntryPointString(
            f"{entry_point.module_name}:{entry_point.attrs[0]}"
        )
        register_crypto(ledger_id, entry_point_string)
