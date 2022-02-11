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

"""Plug-in system for adding new CLI commands."""
import os
import sys
import traceback
from typing import Callable, Iterable, List

import click
import pkg_resources


def with_plugins(plugins: Iterable[pkg_resources.EntryPoint]) -> Callable:
    """
    A decorator to register external CLI commands to an instance of `click.Group()`.

    :param plugins: An iterable producing one `pkg_resources.EntryPoint()` per iteration.
    :return: a click.Group instance.
    """

    def decorator(group: click.Group) -> click.Group:
        if not isinstance(group, click.Group):
            raise TypeError(
                "Plugins can only be attached to an instance of click.Group()"
            )

        for entry_point in plugins or ():
            try:
                group.add_command(entry_point.load())
            except Exception:  # pylint: disable=broad-except
                # Catch this so a busted plugin doesn't take down the CLI.
                # Handled by registering a dummy command that does nothing
                # other than explain the error.
                group.add_command(BrokenCommand(entry_point.name))

        return group

    return decorator


class BrokenCommand(click.Command):
    """
    Helper click.Command in case a broken plug-in is loaded.

    Rather than completely crash the CLI when a broken plugin is loaded, this
    class provides a modified help message informing the user that the plugin is
    broken and they should contact the owner.  If the user executes the plugin
    or specifies `--help` a traceback is reported showing the exception the
    plugin loader encountered.
    """

    def __init__(self, name: str) -> None:
        """
        Define the special help messages after instantiating a `click.Command()`.

        :param name: the name of the command.
        """

        click.Command.__init__(self, name)

        util_name = os.path.basename(sys.argv and sys.argv[0] or __file__)
        self.help = (
            "\nWarning: entry point could not be loaded. Contact "
            "its author for help.\n\n\b\n" + traceback.format_exc()
        )
        self.short_help = " Warning: could not load plugin. See `%s %s --help`." % (
            util_name,
            self.name,
        )

    def invoke(self, ctx: click.Context) -> None:
        """
        Print the traceback instead of doing nothing.

        :param ctx: the click.Context object.
        """

        click.echo(self.help, color=ctx.color)
        ctx.exit(1)

    def parse_args(self, ctx: click.Context, args: List) -> List:
        """
        Parse arguments.

        :param ctx: the click.Context object.
        :param args: the raw arguments.
        :return: the arguments, parsed.
        """
        return args
