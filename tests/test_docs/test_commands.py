# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the tests for the commands in the documentation."""

import itertools
import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, Union

import click
from click.core import Command, Group, Option

from aea.cli import cli as aea_cli
from scripts.check_doc_ipfs_hashes import read_file


def get_cmd_data(cmd: Union[Command, Group]) -> Dict:
    """Returns a dict containing the command options and arguments."""

    return {
        "commands": {},
        "options": list(
            itertools.chain(*[i.opts for i in cmd.params if isinstance(i, Option)])
        )
        + ["--help"],  # we add help here as it does not appear in the list
        "arguments": list(
            itertools.chain(
                *[i.opts for i in cmd.params if isinstance(i, click.Argument)]
            )
        ),
    }


def get_group_tree(cmd: click.Group) -> Dict:
    """Returns a tree containing the command data."""
    tree = get_cmd_data(cmd)

    if isinstance(cmd, click.Group):

        for sub_cmd_name in cmd.list_commands(click.Context):

            # Get the sub-command
            sub_cmd = cmd.get_command(click.Context, sub_cmd_name)

            # Recursively build the tree
            tree["commands"][sub_cmd_name] = get_group_tree(sub_cmd)

    return tree


class CommandValidator:
    """Validates commands against a CLI"""

    def __init__(self, cli: Group):
        """Extract autonomy command tree from the aea cli"""
        self.tree = {"commands": {cli.name: get_group_tree(cli)}}

    def validate(self, cmd: str, file_: str = "") -> bool:
        """Validates a command"""

        # Copy the tree
        tree = deepcopy(self.tree)
        latest_subcmd = None
        allow_option_arg = False

        cmd_parts = [i for i in cmd.split(" ") if i]

        # Iterate the command parts
        for cmd_part in cmd_parts:

            # Subcommands
            if cmd_part in tree["commands"].keys():
                latest_subcmd = cmd_part
                tree = tree["commands"][cmd_part]
                allow_option_arg = False
                continue

            # Options
            if cmd_part.startswith("-"):
                if cmd_part not in tree["options"]:
                    print(
                        f"Command validation error in {file_}: option '{cmd_part}' is not present on the command tree {list(tree['options'])}:\n    {cmd}"
                    )
                    return False

                allow_option_arg = True
                continue

            # Option arguments: we can't validate them, just guess that they are correct.
            if allow_option_arg:
                allow_option_arg = False
                continue

            # Command arguments
            if not latest_subcmd:
                print(
                    f"Command validation error in {file_}: detected argument '{cmd_part}' but no latest subcommand exists yet:\n    {cmd}"
                )
                return False

            if not tree["arguments"]:
                print(
                    f"Command validation error in {file_}: argument '{cmd_part}' is not valid as the latest subcommand [{latest_subcmd}] does not admit arguments:\n    {cmd}"
                )
                return False

            # If we reach here, this command part is probably an argument for a command.
            # We can't validate it, just guess that it is correct.

        return True


def test_validate_doc_commands() -> None:
    """Test that doc commands are valid"""

    # Get the markdown files and the Makefile
    target_files = list(Path("docs").rglob("*.md"))
    target_files.append(Path("Makefile"))

    # Get the validator
    validator = CommandValidator(aea_cli)

    COMMAND_REGEX = r"""(^|\s|`|>)(?P<full_cmd>(?P<cli>aea) ((?!(&|'|\(|\[|\n|\.|`|\||#|<\/code>|=|")).)*)"""

    skips = [
        "aea packages/valory/protocols packages/valory/connections packages/fetchai/protocols packages/fetchai/connections packages/fetchai/skills tests/ --cov",
        "aea packages/valory/connections packages/valory/protocols packages/fetchai/connections packages/fetchai/protocols packages/fetchai/skills tests/test_$",
        "aea packages/valory/connections packages/valory/protocols packages/fetchai/connections packages/fetchai/protocols packages/fetchai/skills tests/test_packages/test_$",
    ]

    # Validate all matches
    for file_ in target_files:
        content = read_file(str(file_))

        for match in [m.groupdict() for m in re.finditer(COMMAND_REGEX, content)]:
            cmd = match["full_cmd"].strip()

            if cmd in skips:
                continue
            assert validator.validate(cmd, str(file_))


def test_validator() -> None:
    """Test the command validator"""

    validator = CommandValidator(aea_cli)

    good_cmds = [
        "aea run --aev",
        "aea scaffold connection my_new_connection",
        "aea add-key ethereum ethereum_private_key.txt",
    ]

    bad_cmds = [
        "aea install --bad_option",  # non-existent option
        "aea bad_arg",  # non-existent argument
    ]

    for cmd in good_cmds:
        assert validator.validate(cmd), f"Command {cmd} is not valid"

    for cmd in bad_cmds:
        assert not validator.validate(cmd), f"Command {cmd} is valid and it shouldn't."
