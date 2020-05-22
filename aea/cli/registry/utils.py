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
from pathlib import Path

import click

import requests

from aea.cli.registry.settings import AUTH_TOKEN_KEY, REGISTRY_API_URL
from aea.cli.utils.config import _get_or_create_cli_config
from aea.cli.utils.loggers import logger
from aea.configurations.base import PublicId


def get_auth_token() -> str:
    """
    Get current auth token.

    :return: str auth token
    """
    config = _get_or_create_cli_config()
    return config.get(AUTH_TOKEN_KEY, None)


def request_api(
    method: str,
    path: str,
    params=None,
    data=None,
    is_auth=False,
    filepath=None,
    handle_400=True,
    return_code=False,
):
    """
    Request Registry API.

    :param method: str request method ('GET, 'POST', 'PUT', etc.).
    :param path: str URL path.
    :param params: dict GET params.
    :param data: dict POST data.
    :param is_auth: bool is auth requied (default False).
    :param filepath: str path to file to upload (default None).

    :return: dict response from Registry API or tuple (dict response, status code).
    """
    headers = {}
    if is_auth:
        token = get_auth_token()
        if token is None:
            raise click.ClickException(
                "Unable to read authentication config. "
                'Please sign in with "aea login" command.'
            )
        else:
            headers.update({"Authorization": "Token {}".format(token)})

    files = None
    if filepath:
        files = {"file": open(filepath, "rb")}

    request_kwargs = dict(
        method=method,
        url="{}{}".format(REGISTRY_API_URL, path),
        params=params,
        files=files,
        data=data,
        headers=headers,
    )
    try:
        resp = requests.request(**request_kwargs)
    except requests.exceptions.ConnectionError:
        raise click.ClickException("Registry server is not responding.")

    resp_json = resp.json()

    if resp.status_code == 200:
        pass
    elif resp.status_code == 201:
        logger.debug("Successfully created!")
    elif resp.status_code == 403:
        raise click.ClickException(
            "You are not authenticated. " 'Please sign in with "aea login" command.'
        )
    elif resp.status_code == 404:
        raise click.ClickException("Not found in Registry.")
    elif resp.status_code == 409:
        raise click.ClickException(
            "Conflict in Registry. {}".format(resp_json["detail"])
        )
    elif resp.status_code == 400:
        if handle_400:
            raise click.ClickException(resp_json)
    else:
        raise click.ClickException(
            "Wrong server response. Status code: {}".format(resp.status_code)
        )
    if return_code:
        return resp_json, resp.status_code
    else:
        return resp_json


def download_file(url: str, cwd: str) -> str:
    """
    Download file from URL and save it in CWD (current working directory).

    :param url: str url of the file to download.
    :param cwd: str path to current working directory.

    :return: str path to downloaded file
    """
    local_filename = url.split("/")[-1]
    filepath = os.path.join(cwd, local_filename)
    # NOTE the stream=True parameter below
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(response.raw.read())
    else:
        raise click.ClickException(
            "Wrong response from server when downloading package."
        )
    return filepath


def extract(source: str, target: str) -> None:
    """
    Extract tarball and remove source file.

    :param source: str path to a source tarball file.
    :param target: str path to target directory.

    :return: None
    """
    if source.endswith("tar.gz"):
        tar = tarfile.open(source, "r:gz")
        tar.extractall(path=target)
        tar.close()
    else:
        raise Exception("Unknown file type: {}".format(source))

    os.remove(source)


def fetch_package(obj_type: str, public_id: PublicId, cwd: str, dest: str) -> Path:
    """
    Fetch connection/protocol/skill from Registry.

    :param obj_type: str type of object you want to fetch:
        'connection', 'protocol', 'skill'
    :param public_id: str public ID of object.
    :param cwd: str path to current working directory.

    :return: package path
    """
    logger.debug(
        "Fetching {obj_type} {public_id} from Registry...".format(
            public_id=public_id, obj_type=obj_type
        )
    )
    author, name, version = public_id.author, public_id.name, public_id.version
    item_type_plural = obj_type + "s"  # used for API and folder paths

    api_path = "/{}/{}/{}/{}".format(item_type_plural, author, name, version)
    resp = request_api("GET", api_path)
    file_url = resp["file"]

    logger.debug(
        "Downloading {obj_type} {public_id}...".format(
            public_id=public_id, obj_type=obj_type
        )
    )
    filepath = download_file(file_url, cwd)

    # next code line is needed because the items are stored in tarball packages as folders
    dest = os.path.split(dest)[0]  # TODO: replace this hotfix with a proper solution
    logger.debug(
        "Extracting {obj_type} {public_id}...".format(
            public_id=public_id, obj_type=obj_type
        )
    )
    extract(filepath, dest)
    click.echo(
        "Successfully fetched {obj_type}: {public_id}.".format(
            public_id=public_id, obj_type=obj_type
        )
    )
    package_path = os.path.join(dest, public_id.name)
    return Path(package_path)


def registry_login(username: str, password: str) -> str:
    """
    Login into Registry account.

    :param username: str username.
    :param password: str password.

    :return: str token
    """
    resp = request_api(
        "POST", "/rest-auth/login/", data={"username": username, "password": password}
    )
    return resp["key"]


def registry_logout() -> None:
    """
    Logout from Registry account.

    :return: None
    """
    request_api("POST", "/rest-auth/logout/")


def _rm_tarfiles():
    cwd = os.getcwd()
    for filename in os.listdir(cwd):
        if filename.endswith(".tar.gz"):
            filepath = os.path.join(cwd, filename)
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


def check_is_author_logged_in(author_name: str) -> None:
    """
    Check if current user's name equals to item's author.

    :param author_name: str item author username.

    :raise ClickException: if username and author's name are not equal.
    :return: None.
    """
    resp = request_api("GET", "/rest-auth/user/", is_auth=True)
    if not author_name == resp["username"]:
        raise click.ClickException(
            "Author username is not equal to current logged in username "
            "(logged in: {}, author: {}). Please logout and then login correctly.".format(
                resp["username"], author_name
            )
        )


def is_auth_token_present():
    """
    Check if any user is currently logged in.

    :return: bool is logged in.
    """
    return get_auth_token() is not None
