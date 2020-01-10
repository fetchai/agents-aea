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

"""Implementation of the 'aea publish' subcommand."""
import click
import os
from shutil import copyfile

from aea.cli.common import pass_ctx, Context, try_to_load_agent_config, try_get_item_target_path, DEFAULT_AEA_CONFIG_FILE
from aea.cli.registry.publish import publish_agent


@click.command(name='publish')
@click.option(
    '--registry', is_flag=True, help="For publishing agent to Registry."
)
@pass_ctx
def publish(ctx: Context, registry):
    """Publish Agent to Registry."""
    try_to_load_agent_config(ctx)
    if not registry:
        # TODO: check agent dependencies are available in local packages dir.
        _save_agent_locally(ctx)
    else:
        publish_agent()


def _save_agent_locally(ctx: Context) -> None:
    """
    Save agent to local packages.

    :param ctx: the context

    :return: None
    """
    item_type_plural = 'agents'

    target_dir = try_get_item_target_path(ctx.agent_config.registry_path, item_type_plural, ctx.agent_config.name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    source_path = os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE)
    target_path = os.path.join(target_dir, DEFAULT_AEA_CONFIG_FILE)
    copyfile(source_path, target_path)
    click.echo('Agent "{}" successfully saved in packages folder.'.format(ctx.agent_config.name))
