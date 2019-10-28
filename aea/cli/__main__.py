#!/usr/bin/env python3
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

"""Entry-point for the AEA command-line tool."""

from aea.cli.add import add
from aea.cli.install import install
from aea.cli.list import list as _list
from aea.cli.remove import remove
from aea.cli.run import run
from aea.cli.scaffold import scaffold
from aea.cli.search import search
from aea.cli.core import cli

cli.add_command(add)
cli.add_command(_list)
cli.add_command(search)
cli.add_command(scaffold)
cli.add_command(remove)
cli.add_command(install)
cli.add_command(run)

if __name__ == '__main__':
    cli()  # pragma: no cover
