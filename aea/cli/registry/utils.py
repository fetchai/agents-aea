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


import os
import tarfile
from typing import Dict, Union

import click
import requests
import yaml

from aea.cli.common import logger, DEFAULT_REGISTRY_PATH, AEAConfigException
from aea.cli.registry.settings import (
    REGISTRY_API_URL,
    CLI_CONFIG_PATH,
    AUTH_TOKEN_KEY
)
from aea.configurations.base import PublicId


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
    :param filepath: str path to file to upload (default None).

    :return: dict response from Registry API
    """
    headers = {}
    if auth:
        try:
            token = read_cli_config()[AUTH_TOKEN_KEY]
        except AEAConfigException:
            raise click.ClickException(
                'Unable to read authentication config. '
                'Please sign in with "aea login" command.'
            )
        else:
            headers.update({
                'Authorization': 'Token {}'.format(token)
            })

    files = None
    if filepath:
        files = {'file': open(filepath, 'rb')}

    request_kwargs = dict(
        method=method,
        url='{}{}'.format(REGISTRY_API_URL, path),
        params=params,
        files=files,
        data=data,
        headers=headers,
    )
    try:
        resp = requests.request(**request_kwargs)
    except requests.exceptions.ConnectionError:
        raise click.ClickException('Registry server is not responding.')

    resp_json = resp.json()

    if resp.status_code == 200:
        pass
    elif resp.status_code == 201:
        logger.debug('Successfully created!')
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


def download_file(url: str, cwd: str) -> str:
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


def extract(source: str, target: str) -> None:
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


def fetch_package(obj_type: str, public_id: PublicId, cwd: str) -> None:
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
    owner, name, version = public_id.owner, public_id.name, public_id.version
    plural_obj_type = obj_type + 's'  # used for API and folder paths

    api_path = '/{}/{}/{}/{}'.format(plural_obj_type, owner, name, version)
    resp = request_api('GET', api_path)
    file_url = resp['file']

    click.echo('Downloading {obj_type} {public_id}...'.format(
        public_id=public_id,
        obj_type=obj_type
    ))
    filepath = download_file(file_url, cwd)
    target_folder = os.path.join(cwd, plural_obj_type)

    click.echo('Extracting {obj_type} {public_id}...'.format(
        public_id=public_id,
        obj_type=obj_type
    ))
    extract(filepath, target_folder)
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


def load_yaml(filepath: str) -> Dict:
    """
    Read content from yaml file.

    :param filepath: str path to yaml file.

    :return: dict YAML content
    """
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
    try:
        return load_yaml(CLI_CONFIG_PATH)
    except FileNotFoundError:
        raise AEAConfigException(
            'Unable to read config from {} - file not found.'
            .format(CLI_CONFIG_PATH)
        )


def _rm_tarfiles():
    cwd = os.getcwd()
    for filename in os.listdir(cwd):
        filepath = os.path.join(cwd, filename)
        if filepath.endswith('.tar.gz'):
            os.remove(filepath)


def clean_tarfiles(func):
    """Decorate func to clean tarfiles after executing."""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            _rm_tarfiles()
            raise e
        else:
            _rm_tarfiles()
            return result

    return wrapper


def get_item_source_path(
    cwd: str, item_type_plural: str, item_name: str
) -> str:
    """
    Get the item source path.

    :param cwd: the current working directory
    :param item_type_plural: the item type (plural)
    :param item_name: the item name
    :return: the item source path
    """
    source_path = os.path.join(cwd, item_type_plural, item_name)
    if not os.path.exists(source_path):
        raise click.ClickException(
            'Item "{}" not found in {}.'.format(item_name, cwd)
        )
    return source_path


def get_item_target_path(item_type_plural: str, item_name: str) -> str:
    """
    Get the item target path.

    :param item_type_plural: the item type (plural)
    :param item_name: the item name
    :return: the item target path
    """
    packages_path = DEFAULT_REGISTRY_PATH
    target_path = os.path.join(packages_path, item_type_plural, item_name)
    if os.path.exists(target_path):
        raise click.ClickException(
            'Item "{}" already exists in packages folder.'.format(item_name)
        )
    return target_path


def create_public_id(string: str) -> PublicId:
    """
    Create public ID from string.

    :param string: str public ID.
    :return: Public ID object.
    """
    try:
        return PublicId.from_string(string)
    except ValueError:
        raise click.ClickException('Bad public ID. Please check your input.')
