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
"""Utils used for operating Registry with CLI."""


import click
import requests

from aea.cli.registry.settings import REGISTRY_API_URL


def request_api(method, path, params=None):
    """Request Registry API."""
    resp = requests.request(
        method=method,
        url='{}{}'.format(REGISTRY_API_URL, path),
        params=params
    )
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 403:
        raise click.ClickException('You are not authenticated.')
    else:
        raise click.ClickException(
            'Wrong server response. Status code: {}'.format(resp.status_code)
        )


def format_items(items):
    """Format list of items (protocols/connections) to a string for CLI output."""
    list_str = ''
    for item in items:
        list_str += (
            '{line}\n'
            'Name: {name}\n'
            'Description: {description}\n'
            '{line}\n'.format(
                name=item['name'],
                description=item['description'],
                line='-' * 30
            ))
    return list_str


def format_skills(items):
    """Format list of skills to a string for CLI output."""
    list_str = ''
    for item in items:
        list_str += (
            '{line}\n'
            'Name: {name}\n'
            'Description: {description}\n'
            'Protocols: {protocols}\n'
            '{line}\n'.format(
                name=item['name'],
                description=item['description'],
                protocols=''.join(
                    name + ' | ' for name in item['protocol_names']
                ),
                line='-' * 30
            ))
    return list_str
