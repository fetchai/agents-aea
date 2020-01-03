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

"""Implementation of the 'aea fetch' subcommand."""
import click

from aea.cli.common import PublicIdParameter
from aea.cli.registry.fetch import fetch_agent, fetch_agent_locally



@click.command(name='fetch')
@click.option(
    '--registry', is_flag=True, help="For fetching agent from Registry."
)
@click.argument('public-id', type=PublicIdParameter(), required=True)
def fetch(public_id, registry):
    """Fetch Agent from Registry."""
    if not registry:
        fetch_agent_locally(public_id)
    else:
        fetch_agent(public_id)
