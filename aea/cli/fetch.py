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
from distutils.dir_util import copy_tree
import os

from aea.cli.common import Context, pass_ctx, PublicIdParameter, DEFAULT_REGISTRY_PATH, try_get_item_source_path
from aea.cli.registry.fetch import fetch_agent
from aea.configurations.base import PublicId


@click.command(name='fetch')
@click.option(
    '--registry', is_flag=True, help="For fetching agent from Registry."
)
@click.argument('public-id', type=PublicIdParameter(), required=True)
@pass_ctx
def fetch(ctx: Context, public_id, registry):
    """Fetch Agent from Registry."""
    if not registry:
        _fetch_agent_locally(ctx, public_id)
    else:
        fetch_agent(ctx, public_id)


def _fetch_agent_locally(ctx: Context, public_id: PublicId) -> None:
    """
    Fetch Agent from local packages.

    :param ctx: Context
    :param public_id: public ID of agent to be fetched.

    :return: None
    """
    packages_path = os.path.basename(DEFAULT_REGISTRY_PATH)
    source_path = try_get_item_source_path(packages_path, 'agents', public_id.name)
    target_path = os.path.join(ctx.cwd, public_id.name)
    if os.path.exists(target_path):
        raise click.ClickException(
            'Item "{}" already exists in target folder.'.format(public_id.name)
        )
    copy_tree(source_path, target_path)
    click.echo('Agent {} successfully fetched.'.format(public_id.name))
    # TODO: install all dependencies recursively
