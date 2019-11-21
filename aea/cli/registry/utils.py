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
    else:
        raise click.ClickException(
            'Wrong server response. Status code: {}'.format(resp.status_code)
        )


def _split_public_id(public_id):
    """Split public ID to ownwer, name, version."""
    public_id = public_id.replace(':', '/')
    return public_id.split('/')


def _download_file(url):
    """Short summary.

    Parameters
    ----------
    url : type
        Description of parameter `url`.

    Returns
    -------
    type
        Description of returned object.

    """
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
    return local_filename


def _extract(path):
    """Extract tarball and remove source file.

    Parameters
    ----------
    path : str
        Path to file.

    Returns
    -------
    str
        File path of fetched object.

    """
    if (path.endswith("tar.gz")):
        tar = tarfile.open(path, "r:gz")
        tar.extractall(path='path')
        tar.close()
    else:
        raise Exception('Unknown file type: {}'.format(path))

    # os.remove(path)
    raise NotImplementedError


def fetch(obj_type, public_id):
    """Fetch connection/protocol/skill from Registry.

    Parameters
    ----------
    obj_type : str
        Type of object you want to fetch: 'connection', 'protocol', 'skill'.
    public_id : str
        Public ID of object.

    Returns
    -------
    str
        Folder path of fetched object.

    """
    owner, name, version = _split_public_id(id)
    obj_type += 's'
    path = '/{}/{}/{}/{}'.format(obj_type, owner, name, version)
    resp = request_api('GET', path)
    file_url = resp['file']
    raise NotImplementedError
