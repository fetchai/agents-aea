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
import sys
from pathlib import Path

import click
import click_log
import yaml

import logging

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


class Context(object):

    def __init__(self):
        self.config = {}

    def set_config(self, key, value):
        self.config[key] = value
        logger.info('  config[%s] = %s' % (key, value), file=sys.stderr)


pass_ctx = click.make_pass_decorator(Context)


@click.group()
@click.option('--config', nargs=2, multiple=True,
              metavar='KEY VALUE', help='Overrides a config key/value pair.')
@click.version_option('0.1')
@click.pass_context
@click_log.simple_verbosity_option(logger)
def cli(ctx, config):
    ctx.obj = Context()
    for key, value in config:
        ctx.obj.set_config(key, value)


@cli.command()
@click.argument('name', type=str)
@click.argument('path', type=click.Path(), required=False, default=None)
@pass_ctx
def create(ctx: Context, name, path):
    """Create an agent."""
    if path is None:
        # default agent's directory name: the agent's name.
        path = Path("./{}".format(name))

    logger.info("creating agent's directory in '{}'".format(path))

    # create the agent's directory
    try:
        path.mkdir(exist_ok=False)
    except OSError:
        logger.error("Directory already exist. Aborting...")
        return

    # create a config file inside it
    config_file_path = path.joinpath(Path("config.yaml"))
    config_file = open(config_file_path, "w")
    yaml.safe_dump("""- name: {}""".format(name), config_file)

    logger.info("Created config file {}".format(config_file_path))

if __name__ == '__main__':
    cli()