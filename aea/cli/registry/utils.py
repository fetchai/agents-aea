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
from json.decoder import JSONDecodeError

import click
import requests

from aea.cli.registry.settings import AUTH_TOKEN_KEY, REGISTRY_API_URL
from aea.cli.utils.config import get_or_create_cli_config
from aea.cli.utils.context import Context
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import find_item_locally
from aea.configurations.base import PublicId


def get_auth_token() -> str:
    """
    Get current auth token.

    :return: str auth token
    """
    config = get_or_create_cli_config()
    return config.get(AUTH_TOKEN_KEY, None)


def request_api(
    method: str,
    path: str,
    params=None,
    data=None,
    is_auth=False,
    files=None,
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
    :param files: optional dict {file_field_name: open(filepath, "rb")} (default None).

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
        headers.update({"Authorization": "Token {}".format(token)})

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
        resp_json = resp.json()
    except requests.exceptions.ConnectionError:
        raise click.ClickException("Registry server is not responding.")
    except JSONDecodeError:
        resp_json = None

    if resp.status_code == 200:
        pass
    elif resp.status_code == 201:
        logger.debug("Successfully created!")
    elif resp.status_code == 403:
        raise click.ClickException(
            "You are not authenticated. " 'Please sign in with "aea login" command.'
        )
    elif resp.status_code == 500:
        raise click.ClickException("Registry internal server error.")
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
        raise ValueError("Unknown file type: {}".format(source))

    os.remove(source)


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


def get_package_meta(obj_type: str, public_id: PublicId) -> dict:
    """
    Get package meta data from remote registry.

    :param obj_type: str. component type
    :param public_id: component public id

    :return: dict with package details
    """
    api_path = f"/{obj_type}s/{public_id.author}/{public_id.name}/{public_id.version}"
    resp = request_api("GET", api_path)
    return resp


def get_latest_public_id_mixed(
    ctx: Context, item_type: str, item_public_id: PublicId,
) -> PublicId:
    """
    Get latest public id of the message, mixed mode.

    That is, give priority to local registry, and fall back to remote registry
    in case of failure.

    :param ctx: the CLI context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: the path to the found package.
    """
    try:
        _, item_config = find_item_locally(ctx, item_type, item_public_id)
        latest_item_public_id = item_config.public_id
    except click.ClickException:
        logger.debug(
            "Get latest public id from local registry failed, trying remote registry..."
        )
        # the following might raise exception, but we don't catch it this time
        package_meta = get_package_meta(item_type, item_public_id)
        latest_item_public_id = PublicId.from_str(package_meta["public_id"])
    return latest_item_public_id


def get_latest_version_available_in_registry(
    ctx: Context, item_type: str, item_public_id: PublicId
) -> PublicId:
    """
    Get latest available package version public id.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: the latest public id.
    """
    is_local = ctx.config.get("is_local")
    is_mixed = ctx.config.get("is_mixed")
    try:
        if is_mixed:
            latest_item_public_id = get_latest_public_id_mixed(
                ctx, item_type, item_public_id
            )
        elif is_local:
            _, item_config = find_item_locally(ctx, item_type, item_public_id)
            latest_item_public_id = item_config.public_id
        else:
            package_meta = get_package_meta(item_type, item_public_id)
            latest_item_public_id = PublicId.from_str(package_meta["public_id"])
    except Exception:  # pylint: disable=broad-except
        raise click.ClickException(
            f"Package {item_public_id} details can not be fetched from the registry!"
        )

    return latest_item_public_id
