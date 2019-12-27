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
"""Methods for CLI fetch functionality."""
from typing import Union

import click
import os

from distutils.dir_util import copy_tree

from aea.cli.common import DEFAULT_REGISTRY_PATH
from aea.cli.registry.utils import (
    request_api, download_file, extract
)
from aea.configurations.base import PublicId


def fetch_agent(public_id: Union[PublicId, str]) -> None:
    """
    Fetch Agent from Registry.

    :param public_id: str public ID of desirable Agent.

    :return: None
    """
    if isinstance(public_id, str):
        public_id = PublicId.from_string(public_id)
    owner, name, version = public_id.owner, public_id.name, public_id.version
    api_path = '/agents/{}/{}/{}'.format(owner, name, version)
    resp = request_api('GET', api_path)
    file_url = resp['file']

    cwd = os.getcwd()
    filepath = download_file(file_url, cwd)
    target_folder = os.path.join(cwd, name)
    extract(filepath, target_folder)
    click.echo(
        'Agent {} successfully fetched to {}.'
        .format(name, target_folder)
    )


def _get_agent_source_path(item_name: str) -> str:
    packages_path = os.path.basename(DEFAULT_REGISTRY_PATH)
    target_path = os.path.join(packages_path, 'agents', item_name)
    if not os.path.exists(target_path):
        raise click.ClickException(
            'Agent "{}" not found in packages folder.'.format(item_name)
        )
    return target_path


def fetch_agent_locally(public_id: Union[PublicId, str]) -> None:
    """
    Fetch Agent from local packages.

    :param public_id: str public ID of desirable Agent.

    :return: None
    """
    if isinstance(public_id, str):
        public_id = PublicId.from_string(public_id)

    name = public_id.name
    source_dir = _get_agent_source_path(name)
    cwd = os.getcwd()
    target_dir = os.path.join(cwd, name)
    copy_tree(source_dir, target_dir)
    click.echo(
        'Agent {} successfully saved in {}.'
        .format(name, cwd)
    )
