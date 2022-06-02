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

"""Implementation of plug-in mechanism for cryptos."""
import itertools
import pprint
from typing import Iterator, List, Set

from pkg_resources import EntryPoint, WorkingSet

from aea.configurations.constants import (
    ALLOWED_GROUPS,
    CRYPTO_PLUGIN_GROUP,
    DOTTED_PATH_MODULE_ELEMENT_SEPARATOR,
    FAUCET_APIS_PLUGIN_GROUP,
    LEDGER_APIS_PLUGIN_GROUP,
)
from aea.crypto import register_crypto, register_faucet_api, register_ledger_api
from aea.crypto.registries.base import EntryPoint as EntryPointString
from aea.crypto.registries.base import ItemId
from aea.exceptions import AEAException, AEAPluginError, enforce


_from_group_to_register_callable = {
    CRYPTO_PLUGIN_GROUP: register_crypto,
    LEDGER_APIS_PLUGIN_GROUP: register_ledger_api,
    FAUCET_APIS_PLUGIN_GROUP: register_faucet_api,
}


class Plugin:
    """Class that implements an AEA plugin."""

    __slots__ = ("_group", "_entry_point")

    def __init__(self, group: str, entry_point: EntryPoint):
        """
        Initialize the plugin.

        :param group: the group the plugin belongs to.
        :param entry_point: the entrypoint.
        """
        self._group = group
        self._entry_point = entry_point
        self._check_consistency()

    def _check_consistency(self) -> None:
        """
        Check consistency of input.

        :raises AEAPluginError: if some input is not correct.  # noqa: DAR402
        """
        _error_message_prefix = f"Error with plugin '{self._entry_point.name}':"
        enforce(
            self.group in ALLOWED_GROUPS,
            f"{_error_message_prefix} '{self.group}' is not in the allowed groups: {pprint.pformat(ALLOWED_GROUPS)}",
            AEAPluginError,
        )
        enforce(
            ItemId.REGEX.match(self._entry_point.name) is not None,
            f"{_error_message_prefix} '{self._entry_point.name}' is not a valid identifier for a plugin.",
            AEAPluginError,
        )
        enforce(
            len(self._entry_point.attrs) == 1,
            f"{_error_message_prefix} Nested attributes currently not supported.",
            AEAPluginError,
        )
        enforce(
            len(self._entry_point.extras) == 0,
            f"{_error_message_prefix} Extras currently not supported.",
            AEAPluginError,
        )
        enforce(
            EntryPointString.REGEX.match(self.entry_point_path) is not None,
            f"{_error_message_prefix} Entry point path '{self.entry_point_path}' is not valid.",
        )

    @property
    def name(self) -> str:
        """Get the plugin identifier."""
        return self._entry_point.name

    @property
    def group(self) -> str:
        """Get the group."""
        return self._group

    @property
    def attr(self) -> str:
        """Get the class name."""
        return self._entry_point.attrs[0]

    @property
    def entry_point_path(self) -> str:
        """Get the entry point path."""
        class_name = self.attr
        return f"{self._entry_point.module_name}{DOTTED_PATH_MODULE_ELEMENT_SEPARATOR}{class_name}"


def _check_no_duplicates(plugins: List[EntryPoint]) -> None:
    """Check there are no two plugins with the same id."""
    seen: Set[str] = set()
    duplicate_plugins = [p for p in plugins if p.name in seen or seen.add(p.name)]  # type: ignore
    error_msg = f"Found plugins with the same id: {pprint.pformat(duplicate_plugins)}"
    enforce(len(duplicate_plugins) == 0, error_msg, AEAPluginError)


def _get_plugins(group: str) -> List[Plugin]:
    """
    Return a dict of all installed plugins, by name.

    :param group: the plugin group.
    :return: a mapping from plugin name to Plugin objects.
    """
    entry_points: List[EntryPoint] = list(WorkingSet().iter_entry_points(group=group))
    _check_no_duplicates(entry_points)
    return [Plugin(group, entry_point) for entry_point in entry_points]


def _get_cryptos() -> List[Plugin]:
    """Get cryptos plugins."""
    return _get_plugins(CRYPTO_PLUGIN_GROUP)


def _get_ledger_apis() -> List[Plugin]:
    """Get ledgers plugins."""
    return _get_plugins(LEDGER_APIS_PLUGIN_GROUP)


def _get_faucet_apis() -> List[Plugin]:
    """Get faucets plugins."""
    return _get_plugins(FAUCET_APIS_PLUGIN_GROUP)


def _iter_plugins() -> Iterator[Plugin]:
    """Iterate over all the plugins."""
    for plugin in itertools.chain(
        _get_cryptos(), _get_ledger_apis(), _get_faucet_apis()
    ):
        yield plugin


def _register_plugin(plugin: Plugin, is_raising_exception: bool = True) -> None:
    """Register a plugin to the right registry."""
    register_function = _from_group_to_register_callable[plugin.group]
    try:
        register_function(plugin.name, entry_point=plugin.entry_point_path)
    except AEAException:  # pragma: nocover
        if is_raising_exception:
            raise


def load_all_plugins(is_raising_exception: bool = True) -> None:
    """Load all plugins."""
    for plugin in _iter_plugins():
        _register_plugin(plugin, is_raising_exception)
