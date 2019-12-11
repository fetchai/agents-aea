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
import yaml
import shutil

from typing import List, Dict

from aea.cli.registry.settings import (
    REGISTRY_API_URL,
    CLI_CONFIG_PATH,
    AUTH_TOKEN_KEY
)


def request_api(
    method: str, path: str, params=None, data=None, auth=False, filepath=None
) -> Dict:
    """
    Request Registry API.

    :param method: str request method ('GET, 'POST', 'PUT', etc.).
    :param path: str URL path.
    :param params: dict GET params.
    :param data: dict POST data.
    :param auth: bool is auth requied (default False).

    :return: dict response from Registry API
    """
    headers = {}
    if auth:
        token = read_cli_config()['auth_token']
        headers.update({
            'Authorization': 'Token {}'.format(token)
        })

    files = None
    if filepath:
        files = {'file': open(filepath,'rb')}

    resp = requests.request(
        method=method,
        url='{}{}'.format(REGISTRY_API_URL, path),
        params=params,
        files=files,
        data=data,
        headers=headers,
    )
    resp_json = resp.json()

    if resp.status_code == 200:
        pass
    elif resp.status_code == 201:
        click.echo('Successfully created!')
    elif resp.status_code == 403:
        raise click.ClickException(
            'You are not authenticated. '
            'Please sign in with "aea login" command.'
        )
    elif resp.status_code == 404:
        raise click.ClickException('Not found in Registry.')
    elif resp.status_code == 409:
        raise click.ClickException(
            'Conflict in Registry. {}'.format(resp_json['detail'])
        )
    elif resp.status_code == 400:
        raise click.ClickException(resp.json())
    else:
        raise click.ClickException(
            'Wrong server response. Status code: {}'.format(resp.status_code)
        )
    return resp_json


def split_public_id(public_id: str) -> List[str]:
    """
    Split public ID to ownwer, name, version.

    :param public_id: public ID of item from Registry.

    :return: list of str [owner, name, version]
    """
    public_id = public_id.replace(':', '/')
    return public_id.split('/')


def _download_file(url: str, cwd: str) -> str:
    """
    Download file from URL and save it in CWD (current working directory).

    :param url: str url of the file to download.
    :param cwd: str path to current working directory.

    :return: str path to downloaded file
    """
    local_filename = url.split('/')[-1]
    filepath = os.path.join(cwd, local_filename)
    # NOTE the stream=True parameter below
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.raw.read())
    else:
        raise click.ClickException(
            'Wrong response from server when downloading package.'
        )
    return filepath


def _extract(source: str, target: str) -> None:
    """
    Extract tarball and remove source file.

    :param source: str path to a source tarball file.
    :param target: str path to target directory.

    :return: None
    """
    if (source.endswith("tar.gz")):
        tar = tarfile.open(source, "r:gz")
        tar.extractall(path=target)
        tar.close()
    else:
        raise Exception('Unknown file type: {}'.format(source))

    os.remove(source)


def _remove_pycache(source_dir: str):
    pycache_path = os.path.join(source_dir, '__pycache__')
    if os.path.exists(pycache_path):
        shutil.rmtree(pycache_path)


def _compress(output_filename: str, source_dir: str):
    _remove_pycache(source_dir)
    with tarfile.open(output_filename, "w:gz") as f:
        f.add(source_dir, arcname=os.path.basename(source_dir))


def fetch_package(obj_type: str, public_id: str, cwd: str) -> None:
    """
    Fetch connection/protocol/skill from Registry.

    :param obj_type: str type of object you want to fetch:
        'connection', 'protocol', 'skill'
    :param public_id: str public ID of object.
    :param cwd: str path to current working directory.

    :return: None
    """
    click.echo('Fetching {obj_type} {public_id} from Registry...'.format(
        public_id=public_id,
        obj_type=obj_type
    ))
    owner, name, version = split_public_id(public_id)
    plural_obj_type = obj_type + 's'  # used for API and folder paths

    api_path = '/{}/{}/{}/{}'.format(plural_obj_type, owner, name, version)
    resp = request_api('GET', api_path)
    file_url = resp['file']

    click.echo('Downloading {obj_type} {public_id}...'.format(
        public_id=public_id,
        obj_type=obj_type
    ))
    filepath = _download_file(file_url, cwd)
    target_folder = os.path.join(cwd, plural_obj_type)

    click.echo('Extracting {obj_type} {public_id}...'.format(
        public_id=public_id,
        obj_type=obj_type
    ))
    _extract(filepath, target_folder)
    click.echo('Successfully fetched {obj_type}: {public_id}.'.format(
        public_id=public_id,
        obj_type=obj_type
    ))


def registry_login(username: str, password: str) -> str:
    """
    Login into Registry account.

    :param username: str username.
    :param password: str password.

    :return: str token
    """
    resp = request_api(
        'POST', '/rest-auth/login/',
        data={'username': username, 'password': password}
    )
    return resp['key']


def _init_config_folder() -> None:
    """
    Create config folder if not exists.

    :return: None
    """
    conf_dir = os.path.dirname(CLI_CONFIG_PATH)
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)


def write_cli_config(dict_conf: Dict) -> None:
    """
    Write CLI config into yaml file.

    :param dict_conf: dict config to write.

    :return: None
    """
    _init_config_folder()
    with open(CLI_CONFIG_PATH, 'w') as f:
        yaml.dump(dict_conf, f, default_flow_style=False)


def _load_yaml(filepath):
    with open(filepath, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise click.ClickException(
                'Loading yaml config from {} failed: {}'.format(
                    filepath, e
                )
            )


def read_cli_config() -> Dict:
    """
    Read CLI config from yaml file.

    :return: dict CLI config.
    """
    return _load_yaml(CLI_CONFIG_PATH)


def push_item(item_type: str, item_name: str):
    item_type_plural = item_type + 's'
    cwd = os.getcwd()

    items_folder = os.path.join(cwd, item_type_plural)
    item_path = os.path.join(items_folder, item_name)
    click.echo(
        'Searching for {} {} in {} ...'. format(
        item_name, item_type, items_folder
    ))
    if not os.path.exists(item_path):
        raise click.ClickException(
            '{} "{}" not found  in {}. Make sure you run push command '
            'from a correct folder.'.format(
                item_type.title(), item_name, items_folder
            )
        )

    output_filename = '{}.tar.gz'.format(item_name)
    click.echo('Compressing {} {} to {} ...'.format(
        item_name, item_type, output_filename
    ))
    _compress(output_filename, item_path)
    output_filepath = os.path.join(cwd, output_filename)

    item_config_filepath = os.path.join(item_path, '{}.yaml'.format(item_type))
    click.echo('Reading {} {} config ...'.format(item_name, item_type))
    item_config = _load_yaml(item_config_filepath)

    data = {
        'name': item_name,
        'description': item_config['description'],
        'version': item_config['version']
    }
    path = '/{}/create'.format(item_type_plural)
    click.echo('Pushing {} {} to Registry ...'.format(
        item_name, item_type
    ))
    resp = request_api(
        'POST', path, data=data, auth=True, filepath=output_filepath
    )
    click.echo(
        'Successfully pushed {} {} to the Registry. Public ID: {}'.format(
            item_type, item_name, resp['public_id']
        )
    )

    click.echo('Removing temporary file {}'.format(output_filepath))
    os.remove(output_filepath)
