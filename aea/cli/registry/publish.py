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
"""Methods for CLI publish functionality."""

import os
import click
import tarfile

from aea.cli.common import logger
from aea.cli.registry.utils import clean_tarfiles, load_yaml, request_api
from aea.cli.registry.settings import AGENT_CONFIG_FILENAME


def _compress(output_filename: str, *filepaths):
    """Compare the output file."""
    with tarfile.open(output_filename, "w:gz") as f:
        for filepath in filepaths:
            f.add(filepath, arcname=os.path.basename(filepath))


@clean_tarfiles
def publish_agent():
    """Publish an agent."""
    cwd = os.getcwd()
    agent_config_path = os.path.join(cwd, AGENT_CONFIG_FILENAME)
    if not os.path.exists(agent_config_path):
        raise click.ClickException(
            'Agent config not found in {}. Make sure you run push command '
            'from a correct folder.'.format(cwd)
        )
    agent_config = load_yaml(agent_config_path)
    name = agent_config['agent_name']
    output_tar = os.path.join(cwd, '{}.tar.gz'.format(name))
    _compress(output_tar, agent_config_path)

    data = {
        'name': name,
        'description': agent_config['description'],
        'version': agent_config['version']
    }
    path = '/agents/create'
    logger.debug('Publishing agent {} to Registry ...'.format(name))
    resp = request_api(
        'POST', path, data=data, auth=True, filepath=output_tar
    )
    click.echo(
        'Successfully published agent {} to the Registry. Public ID: {}'.format(
            name, resp['public_id']
        )
    )
