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

"""This module contains the tests for the content of cli-commands.md file."""
import pprint
import re
from pathlib import Path

from aea.cli import cli

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import BaseTestMarkdownDocs


IGNORE_MATCHES = ["`-v DEBUG run`", "`config set [path] [--type TYPE]`"]


class TestCliCommands(BaseTestMarkdownDocs):
    """Test cli-commands.md documentation."""

    DOC_PATH = Path(ROOT_DIR, "docs", "cli-commands.md")

    def test_cli_commands(self):
        """Test CLI commands."""
        commands_raw = re.compile(r"\| `.*` +\|").findall(self.doc_content)
        commands_raw = [
            re.compile(r"`([A-Za-z0-9\-_]+) ?.*`").search(s) for s in commands_raw
        ]
        commands_raw = list(
            filter(lambda x: x.group(0) not in IGNORE_MATCHES, commands_raw)
        )
        actual_commands = list(map(lambda match: match.group(1), commands_raw))

        actual_commands_set = set(actual_commands)
        expected_commands = set(cli.commands.keys())

        # test no duplicates
        assert len(actual_commands) == len(
            actual_commands_set
        ), "Found duplicate commands in the documentation."

        # test that there is no missing command
        missing = expected_commands.difference(actual_commands)
        assert (
            len(missing) == 0
        ), f"Missing the following commands: {pprint.pformat(missing)}"

        # test that there are no more commands
        more = actual_commands_set.difference(expected_commands)
        assert len(more) == 0, f"There are unknown commands: {pprint.pformat(missing)}"

        # test that they are in the same order.
        actual = actual_commands
        expected = sorted(expected_commands)
        assert actual == expected, "Commands are not in alphabetical order."
