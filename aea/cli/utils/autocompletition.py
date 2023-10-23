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
"""This module contains the click autocompletition cache implementation."""
import os
import pickle  # nosec
import sys
import time
from os.path import expanduser
from pathlib import Path

import click  # type: ignore


completition_cache_file = Path(expanduser("~")) / ".aea_autocompletition_cache.pickle"
AUTOCOMPLETE_ENV_VAR = "_AEA_COMPLETE"
CACHE_EXPIRE_TIME = 10 * 60  # 10 minutes


def _cleanup_command(cmd: click.Command) -> None:
    for param in cmd.params:
        param.callback = None

    cmd.callback = None
    for subcommand in getattr(cmd, "commands", {}).values():
        _cleanup_command(subcommand)


def _generate_cache() -> click.Command:
    from ..core import cli  # pylint: disable=import-outside-toplevel

    _cleanup_command(cli)
    completition_cache_file.write_bytes(pickle.dumps((time.time(), cli)))
    return cli


def _do_autocomplete() -> None:
    if not completition_cache_file.exists():
        _generate_cache()
    ts, cached_cli = pickle.loads(completition_cache_file.read_bytes())  # nosec
    if time.time() - ts > CACHE_EXPIRE_TIME:
        cached_cli = _generate_cache()

    from click._bashcomplete import (  # type: ignore  # pylint: disable=import-outside-toplevel
        bashcomplete,
    )

    bashcomplete(cached_cli, "aea", AUTOCOMPLETE_ENV_VAR, "complete")


if os.environ.get(AUTOCOMPLETE_ENV_VAR) == "complete":
    _do_autocomplete()
    sys.exit(0)
