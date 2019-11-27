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
import os
import requests
import tarfile

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
    elif resp.status_code == 404:
        raise click.ClickException('Not found in Registry.')
    else:
        raise click.ClickException(
            'Wrong server response. Status code: {}'.format(resp.status_code)
        )


def split_public_id(public_id):
    """Split public ID to ownwer, name, version."""
    public_id = public_id.replace(':', '/')
    return public_id.split('/')


def _download_file(url, cwd):
    """Download file from URL and save it in CWD (current working directory)."""
    local_filename = url.split('/')[-1]
    filepath = os.path.join(cwd, local_filename)
    # NOTE the stream=True parameter below
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.raw.read())
    return filepath


def _extract(source, target):
    """Extract tarball and remove source file."""
    if (source.endswith("tar.gz")):
        tar = tarfile.open(source, "r:gz")
        tar.extractall(path=target)
        tar.close()
    else:
        raise Exception('Unknown file type: {}'.format(source))

    os.remove(source)

    folder_name = os.path.basename(source).replace('.tar.gz', '')
    extracted_folder = os.path.join(target, folder_name)
    return extracted_folder


def fetch_package(obj_type, public_id, cwd):
    """Fetch connection/protocol/skill from Registry."""
    click.echo('Fetching {public_id} {obj_type} from Registry...'.format(
        public_id=public_id,
        obj_type=obj_type
    ))
    owner, name, version = split_public_id(public_id)
    obj_type += 's'
    api_path = '/{}/{}/{}/{}'.format(obj_type, owner, name, version)
    resp = request_api('GET', api_path)
    file_url = resp['file']

    click.echo('Downloading {public_id} {obj_type}...'.format(
        public_id=public_id,
        obj_type=obj_type
    ))
    filepath = _download_file(file_url, cwd)
    target_folder = os.path.join(cwd, obj_type)

    click.echo('Extracting {public_id} {obj_type}...'.format(
        public_id=public_id,
        obj_type=obj_type
    ))
    _extract(
        source=filepath,
        target=target_folder
    )
